import {
    S3Credentials, TaskStatus,
    S3UploadedData,
    InitialFileType
} from "../models/models";

import { TaigaApi } from "../models/api";
import * as AWS from "aws-sdk";
import { file } from "@babel/types";

interface CreateDatasetParams {
    name: string;
    description: string;
    folderId: string;
}

interface CreateVersionParams {
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

interface UploadFile {
    name: string; // the name of the datafile record in once dataset has been created
    fileType: UploadFileType;
    gcsPath?: string; // If the path to a GCS object
    existingTaigaId?: string; // the ID of an existing taiga data file.
    uploadFile?: File;
    uploadFormat?: InitialFileType;
}

export class UploadTracker {
    tapi: TaigaApi;
    uploadStatus: Array<UploadStatus>;
    uploadProgressCallback: (status: Array<UploadStatus>) => void;

    constructor(tapi: TaigaApi) {
        this.tapi = tapi;
    }

    getTapi() {
        return this.tapi;
    }

    upload(uploadFiles: Array<UploadFile>, params: (CreateVersionParams | CreateDatasetParams), uploadProgressCallback: (status: Array<UploadStatus>) => void): Promise<any> {
        this.uploadProgressCallback = uploadProgressCallback;

        console.log("requestUpload");
        return Promise.all([
            this.getTapi().get_s3_credentials(),
            this.getTapi().get_upload_session()
        ]).then((values: Array<any>) => {
            let credentials = values[0] as S3Credentials;
            let sid = values[1] as string;
            return this.submitCreateDataset(credentials, uploadFiles, sid, params);
        });
    }

    associateExistingFile(name: string, taigaId: string, sid: string): Promise<any> {
        let fileMetadata = {
            filename: name,
            filetype: "virtual",
            existingTaigaId: taigaId
        };

        console.log("associateExistingFile", fileMetadata);
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
                return this.initRecurringCheckStatus(uploadIndex, taskStatusId);
            }).then(() => {
                // Get the file who received this progress notification
                this.updateFileStatus(uploadIndex, "conversionProgress", "Done");

                return Promise.resolve<string>(sid);
            });
        });
    }

    // Use the credentials received to upload the files dropped in the module
    submitCreateDataset(s3_credentials: S3Credentials, datafiles: Array<UploadFile>, sid: string, params: (CreateVersionParams | CreateDatasetParams)) {
        console.log("doUpload", s3_credentials, datafiles, sid);
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
                uploadPromises.push(this.uploadAndConvert(s3, s3_credentials, file, sid, i))
            } else {
                // initial status
                status = { progress: 0, progressMessage: "Attempting to add existing file" }

                // perform the attach
                let p = this.associateExistingFile(file.name, file.existingTaigaId, sid);
                p.then(() => {
                    // update the status after successful adding to upload session
                    this.displayStatusUpdate("Added existing file", 100, i);
                });
                uploadPromises.push(p);
            }
            uploadStatus.push(status)
        });

        console.log("kicking off upload of " + uploadPromises.length + " files");

        return Promise.all(uploadPromises).then((datafile_ids: string[]) => {
            if ((params as any).datasetId) {
                let p = params as CreateVersionParams;
                return this.getTapi().create_new_dataset_version(sid, p.datasetId, p.description, datafile_ids);
            } else {
                let p = params as CreateDatasetParams;
                return this.getTapi().create_dataset(sid, p.name, p.description, p.folderId);
            }
        });
    }

    updateFileStatus(index: number, property: string, value: any) {
        console.log("unimplemented");
        this.uploadProgressCallback(this.uploadStatus);
    }

    initRecurringCheckStatus(fileIndex: number, taskId: string) {
        return this.getTapi().get_task_status(taskId).then((new_status: TaskStatus) => {
            return this.checkOrContinue(new_status, fileIndex);
        })
    }

    checkOrContinue(status: TaskStatus, fileIndex: number): Promise<string> {
        // If status == SUCCESS, return the last check
        // If status != SUCCESS, wait 1 sec and check again
        // TODO: Make an enum from the task state

        if (status.state == 'SUCCESS') {
            this.displayStatusUpdate(status, fileIndex);
            return Promise.resolve(status.id)
        }
        else if (status.state == 'FAILURE') {
            // TODO: Make an exception class to manage properly the message
            status.message = "FAILURE: " + status.message;
            this.displayStatusUpdate(status, fileIndex);
            return Promise.reject<string>(status.message);
        }
        else {
            this.displayStatusUpdate(status, fileIndex);
            return this.getTapi().get_task_status(status.id).then((new_status: TaskStatus) => {
                // Wait one sec Async then check again
                // setTimeout(() => {return this.checkOrContinue(status)}, 1000);
                return this.delay(1000).then(() => {
                    return this.checkOrContinue(new_status, fileIndex)
                });
            });
        }
    }

    // Async function to wait
    delay(milliseconds: number) {
        return new Promise<void>(resolve => {
            setTimeout(resolve, milliseconds);
        });
    }

    displayStatusUpdate(message: string, progress: number, fileIndex: number) {
        this.updateFileStatus(fileIndex, "conversionProgress", message);
    }
}
