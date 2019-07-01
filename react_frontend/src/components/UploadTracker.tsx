import {
    S3Credentials, TaskStatus,
    S3UploadedData,
    InitialFileType
} from "../models/models";
import update from "immutability-helper";

import { TaigaApi } from "../models/api";
import * as AWS from "aws-sdk";
import { randomLogNormal } from "d3";

export interface CreateDatasetParams {
    name: string;
    description: string;
    folderId: string;
}

export interface CreateVersionParams {
    datasetId: string;
    description: string;
}


export interface UploadStatus {
    progress: number; // between 0 and 100
    progressMessage: string;
}

export enum UploadFileType {
    Upload,
    TaigaPath,
    GCSPath
}

export interface UploadFile {
    name: string; // the name of the datafile record in once dataset has been created
    fileType: UploadFileType;
    gcsPath?: string; // If the path to a GCS object
    existingTaigaId?: string; // the ID of an existing taiga data file.
    uploadFile?: File;
    uploadFormat?: InitialFileType;
}

// Async function to wait
function delay(milliseconds: number) {
    return new Promise<void>((resolve, reject) => {
        setTimeout(resolve, milliseconds);
    });
}

export function pollFunction(milliseconds: number, fn: () => Promise<boolean>): Promise<void> {
    return fn().then((continueFlag: boolean) => {
        if (continueFlag) {
            return delay(milliseconds).then(() => pollFunction(milliseconds, fn));
        } else {
            return Promise.resolve();
        }
    });
}

export class UploadTracker {
    tapi: TaigaApi;
    uploadStatus: Readonly<Array<UploadStatus>>;
    uploadProgressCallback: (status: Readonly<Array<UploadStatus>>) => void;

    constructor(tapi: TaigaApi) {
        this.tapi = tapi;
    }

    getTapi() {
        return this.tapi;
    }

    upload(uploadFiles: Array<UploadFile>, params: (CreateVersionParams | CreateDatasetParams), uploadProgressCallback: (status: Array<UploadStatus>) => void): Promise<string> {
        console.log("uploading, params:", params);

        this.uploadProgressCallback = uploadProgressCallback;

        return Promise.all([
            this.getTapi().get_s3_credentials(),
            this.getTapi().get_upload_session()
        ]).then((values: Array<any>) => {
            let credentials = values[0] as S3Credentials;
            let sid = values[1] as string;
            return this.submitCreateDataset(credentials, uploadFiles, sid, params);
        }).then((datasetId) => {
            console.log("Created new dataset", datasetId);
            return datasetId;
        });
    }

    associateExistingFile(name: string, taigaId: string, sid: string): Promise<any> {
        let fileMetadata = {
            filename: name,
            filetype: "virtual",
            existingTaigaId: taigaId
        };

        return this.getTapi().create_datafile(sid, fileMetadata);
    }

    uploadAndConvert(s3: AWS.S3, s3_credentials: S3Credentials, file: UploadFile, sid: string, uploadIndex: number): Promise<string> {
        let s3Key = s3_credentials.prefix + file.name;
        let params = {
            Bucket: s3_credentials.bucket,
            Key: s3Key,
            Body: file.uploadFile
        };

        let upload = new AWS.S3.ManagedUpload({
            params: params,
            service: s3
        });

        // Subscribe to measure progress
        upload.on('httpUploadProgress', (evt: any) => {
            // TODO: evt.key is not recognized in the DefinitelyType AWS, but it works. Raise an issue in Git
            let progressPercentage = Math.floor(evt.loaded / evt.total * 100);
            this.updateFileStatus(uploadIndex, "progress", progressPercentage);
        });

        // After the upload completes, run the conversion
        return upload.promise().then((s3uploadData: S3UploadedData) => {
            // TODO: Send the signal the upload is done on the AWS side, so you can begin the conversion on the backend
            // POST
            // We need to retrieve the filetype and the filename to send it to the api too

            let s3FileMetadata = {
                filename: file.name,
                filetype: "s3",
                s3Upload: {
                    format: file.uploadFormat,
                    bucket: s3_credentials.bucket,
                    key: s3Key
                }
            };

            return this.getTapi().create_datafile(sid, s3FileMetadata).then((taskStatusId) => {
                return this.waitForConversion(uploadIndex, taskStatusId);
            }).then(() => {
                // Get the file who received this progress notification
                this.updateFileStatus(uploadIndex, "progressMessage", "Conversion done");

                return Promise.resolve<string>(sid);
            });
        });
    }

    // Use the credentials received to upload the files dropped in the module
    submitCreateDataset(s3_credentials: S3Credentials, datafiles: Array<UploadFile>, sid: string, params: (CreateVersionParams | CreateDatasetParams)) {
        // TODO: If we change the page, we lose the download
        // Configure the AWS S3 object with the received credentials
        let s3 = new AWS.S3({
            apiVersion: '2006-03-01',
            credentials: {
                accessKeyId: s3_credentials.accessKeyId,
                secretAccessKey: s3_credentials.secretAccessKey,
                sessionToken: s3_credentials.sessionToken
            }
        });

        // Looping through all the files
        let uploadPromises: Array<Promise<string>> = [];
        let uploadStatus: Array<UploadStatus> = [];

        datafiles.forEach((file: UploadFile, i: number) => {
            let status: UploadStatus;
            if (file.fileType === UploadFileType.Upload) {
                status = { progress: 0, progressMessage: "Upload starting" }
                let p = this.uploadAndConvert(s3, s3_credentials, file, sid, i);
                uploadPromises.push(p);
            } else {
                // initial status
                status = { progress: 0, progressMessage: "Attempting to add existing file" }

                // perform the attach
                let p = this.associateExistingFile(file.name, file.existingTaigaId, sid).then(datafileId => {
                    this.displayStatusUpdate("Added existing file", 100, i);
                    // update the status after successful adding to upload session
                    return datafileId;
                }).catch(reason => {
                    console.log("failure", reason);
                    this.displayStatusUpdate("" + reason, 0, i);
                    throw "Create dataset failed";
                });
                uploadPromises.push(p);
            }
            uploadStatus.push(status)
        });

        this.uploadStatus = uploadStatus;

        // console.log("kicking off upload of " + uploadPromises.length + " files");

        return Promise.all(uploadPromises).then((datafile_ids: string[]) => {
            if ((params as any).datasetId) {
                let p = params as CreateVersionParams;
                return this.getTapi().create_new_dataset_version(sid, p.datasetId, p.description);
            } else {
                let p = params as CreateDatasetParams;
                return this.getTapi().create_dataset(sid, p.name, p.description, p.folderId);
            }
        });
    }

    updateFileStatus(index: number, property: string, value: any) {
        let change = {} as any;
        change[property] = { $set: value };

        this.uploadStatus = update(this.uploadStatus, { [index]: change });
        this.uploadProgressCallback(this.uploadStatus);
    }

    waitForConversion(fileIndex: number, taskId: string) {
        return pollFunction(1000, () => {
            return this.getTapi().get_task_status(taskId).then((new_status: TaskStatus) => {
                return this.checkOrContinue(new_status, fileIndex);
            });
        });

    }

    checkOrContinue(status: TaskStatus, fileIndex: number): Promise<boolean> {
        // If status == SUCCESS, return the last check
        // If status != SUCCESS, wait 1 sec and check again
        // TODO: Make an enum from the task state

        if (status.state == 'SUCCESS') {
            this.displayStatusUpdate(status.message, 100, fileIndex);
            return Promise.resolve(false);
        }
        else if (status.state == 'FAILURE') {
            // TODO: Make an exception class to manage properly the message
            status.message = "FAILURE: " + status.message;
            this.displayStatusUpdate(status.message, 0, fileIndex);
            return Promise.resolve(false);
        }
        else {
            let progress = 100 * status.current / status.total;
            if (status.total === 0) {
                progress = 0;
            }

            this.displayStatusUpdate(status.message, progress, fileIndex);
            return Promise.resolve(true);
        }
    }


    displayStatusUpdate(message: string, progress: number, fileIndex: number) {
        this.updateFileStatus(fileIndex, "progressMessage", message);
        this.updateFileStatus(fileIndex, "progress", progress);
    }
}