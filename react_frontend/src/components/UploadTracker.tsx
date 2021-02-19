import update from "immutability-helper";

import * as AWS from "aws-sdk";
import { randomLogNormal } from "d3";
import { version } from "punycode";
import { TaigaApi } from "../models/api";
import {
  S3Credentials,
  TaskStatus,
  S3UploadedData,
  UploadedFileMetadata,
  InitialFileType,
  DatasetVersion,
} from "../models/models";

export interface CreateDatasetParams {
  name: string;
  description: string;
  folderId: string;
}

export interface CreateVersionParams {
  datasetId: string;
  description: string;
  changesDescription: string;
}

export interface UploadStatus {
  progress: number; // between 0 and 100
  progressMessage: string;
}

export enum UploadFileType {
  Upload,
  TaigaPath,
  GCSPath,
}

export interface UploadFile {
  name: string; // the name of the datafile record in once dataset has been created
  fileType: UploadFileType;
  gcsPath?: string; // If the path to a GCS object
  existingTaigaId?: string; // the ID of an existing taiga data file.
  uploadFile?: File;
  uploadFormat?: InitialFileType;
  encoding?: string; // Character encoding of the file
}

// Async function to wait
function delay(milliseconds: number) {
  return new Promise<void>((resolve, reject) => {
    setTimeout(resolve, milliseconds);
  });
}

export function pollFunction(
  milliseconds: number,
  fn: () => Promise<boolean>
): Promise<void> {
  return fn().then((continueFlag: boolean) => {
    if (continueFlag) {
      return delay(milliseconds).then(() => pollFunction(milliseconds, fn));
    }
    return Promise.resolve();
  });
}

export interface DatasetIdAndVersionId {
  dataset_id: string;
  version_id: string;
}

interface ConversionStatus {
  keepPolling: boolean;
  isSuccessful?: boolean;
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

  upload(
    uploadFiles: Array<UploadFile>,
    params: CreateVersionParams | CreateDatasetParams,
    uploadProgressCallback: (status: Array<UploadStatus>) => void
  ): Promise<DatasetIdAndVersionId> {
    console.log("uploading, params:", params);

    this.uploadProgressCallback = uploadProgressCallback;

    return Promise.all([
      this.getTapi().get_s3_credentials(),
      this.getTapi().get_upload_session(),
    ])
      .then((values: Array<any>) => {
        const credentials = values[0] as S3Credentials;
        const sid = values[1] as string;
        return this.submitCreateDataset(credentials, uploadFiles, sid, params);
      })
      .then((datasetId) => {
        console.log("Created new dataset", datasetId);
        return datasetId;
      });
  }

  associateExistingFile(
    name: string,
    taigaId: string,
    sid: string
  ): Promise<any> {
    const fileMetadata = {
      filename: name,
      filetype: "virtual",
      existingTaigaId: taigaId,
    };

    return this.getTapi().create_datafile(sid, fileMetadata);
  }

  uploadAndConvert(
    s3: AWS.S3,
    s3_credentials: S3Credentials,
    file: UploadFile,
    sid: string,
    uploadIndex: number
  ): Promise<boolean> {
    const s3Key = s3_credentials.prefix + file.name;
    const params = {
      Bucket: s3_credentials.bucket,
      Key: s3Key,
      Body: file.uploadFile,
    };

    const upload = new AWS.S3.ManagedUpload({
      params,
      service: s3,
    });

    // Subscribe to measure progress
    upload.on("httpUploadProgress", (evt: any) => {
      // TODO: evt.key is not recognized in the DefinitelyType AWS, but it works. Raise an issue in Git
      const progressPercentage = Math.floor((evt.loaded / evt.total) * 100);
      this.updateFileStatus(uploadIndex, "progress", progressPercentage);
    });

    // After the upload completes, run the conversion
    return upload.promise().then((s3uploadData: S3UploadedData) => {
      // TODO: Send the signal the upload is done on the AWS side, so you can begin the conversion on the backend
      // POST
      // We need to retrieve the filetype and the filename to send it to the api too

      const s3FileMetadata: UploadedFileMetadata = {
        filename: file.name,
        filetype: "s3",
        s3Upload: {
          format: file.uploadFormat,
          bucket: s3_credentials.bucket,
          key: s3Key,
          encoding: file.encoding,
        },
      };

      return this.getTapi()
        .create_datafile(sid, s3FileMetadata)
        .then((taskStatusId) => {
          return this.waitForConversion(uploadIndex, taskStatusId);
        })
        .then((success: boolean) => {
          // Get the file who received this progress notification
          if (success) {
            this.updateFileStatus(
              uploadIndex,
              "progressMessage",
              "Conversion done"
            );
          }

          return Promise.resolve<boolean>(success);
        });
    });
  }

  addGCSPointer(name: string, gcsPath: string, sid: string): Promise<any> {
    const fileMetadata = {
      filename: name,
      filetype: "gcs",
      gcsPath,
    };

    return this.getTapi().create_datafile(sid, fileMetadata);
  }

  // returns a promise yielding the dataset_id of the newly constructed dataset
  submitCreateDataset(
    s3_credentials: S3Credentials,
    datafiles: Array<UploadFile>,
    sid: string,
    params: CreateVersionParams | CreateDatasetParams
  ): Promise<DatasetIdAndVersionId> {
    // TODO: If we change the page, we lose the download
    // Configure the AWS S3 object with the received credentials
    const s3 = new AWS.S3({
      apiVersion: "2006-03-01",
      credentials: {
        accessKeyId: s3_credentials.accessKeyId,
        secretAccessKey: s3_credentials.secretAccessKey,
        sessionToken: s3_credentials.sessionToken,
      },
    });

    // Looping through all the files
    const uploadPromises: Array<Promise<boolean>> = [];
    const uploadStatus: Array<UploadStatus> = [];

    datafiles.forEach((file: UploadFile, i: number) => {
      let status: UploadStatus;
      if (file.fileType === UploadFileType.Upload) {
        status = { progress: 0, progressMessage: "Upload starting" };
        const p = this.uploadAndConvert(s3, s3_credentials, file, sid, i);
        uploadPromises.push(p);
      } else if (file.fileType === UploadFileType.GCSPath) {
        status = {
          progress: 0,
          progressMessage: "Attempting to pointer to GCS object",
        };
        const p = this.addGCSPointer(file.name, file.gcsPath, sid)
          .then(() => {
            this.displayStatusUpdate("Added pointer to GCS object", 100, i);
            return true;
          })
          .catch((reason) => {
            console.log("failure", reason);
            this.displayStatusUpdate(`${reason}`, 0, i);
            return false;
          });
        uploadPromises.push(p);
      } else {
        // initial status
        status = {
          progress: 0,
          progressMessage: "Attempting to add existing file",
        };

        // perform the attach
        const p = this.associateExistingFile(
          file.name,
          file.existingTaigaId,
          sid
        )
          .then(() => {
            this.displayStatusUpdate("Added existing file", 100, i);
            // update the status after successful adding to upload session
            return true;
          })
          .catch((reason) => {
            console.log("failure", reason);
            this.displayStatusUpdate(`${reason}`, 0, i);
            return false;
          });
        uploadPromises.push(p);
      }
      uploadStatus.push(status);
    });

    this.uploadStatus = uploadStatus;

    // console.log("kicking off upload of " + uploadPromises.length + " files");

    return Promise.all(uploadPromises).then(
      (successes: Array<boolean>): Promise<DatasetIdAndVersionId> => {
        if (!successes.every(Boolean)) {
          return null;
        }

        if ((params as any).datasetId) {
          const p = params as CreateVersionParams;
          return this.getTapi()
            .create_new_dataset_version(
              sid,
              p.datasetId,
              p.description,
              p.changesDescription
            )
            .then((dataset_version_id: string) => {
              return this.getTapi()
                .get_dataset_version(dataset_version_id)
                .then((version: DatasetVersion) => {
                  return {
                    dataset_id: version.dataset_id,
                    version_id: dataset_version_id,
                  };
                });
            });
        }
        const p = params as CreateDatasetParams;
        return this.getTapi()
          .create_dataset(sid, p.name, p.description, p.folderId)
          .then(
            (dataset_id: string): Promise<DatasetIdAndVersionId> => {
              return this.getTapi()
                .get_dataset_version_last(dataset_id)
                .then((version: DatasetVersion) => {
                  return {
                    dataset_id: version.dataset_id,
                    version_id: version.id,
                  };
                });
            }
          );
      }
    );
  }

  updateFileStatus(index: number, property: string, value: any) {
    const change = {} as any;
    change[property] = { $set: value };

    this.uploadStatus = update(this.uploadStatus, { [index]: change });
    this.uploadProgressCallback(this.uploadStatus);
  }

  waitForConversion(fileIndex: number, taskId: string): Promise<boolean> {
    // returns a delayed boolean which indicates whether the conversion was successful or not
    let isSuccessful = false;

    return pollFunction(1000, () => {
      return this.getTapi()
        .get_task_status(taskId)
        .then((new_status: TaskStatus) => {
          const status = this.checkOrContinue(new_status, fileIndex);
          if (!status.keepPolling) {
            isSuccessful = status.isSuccessful;
          }
          return Promise.resolve(status.keepPolling);
        });
    }).then((): boolean => {
      return isSuccessful;
    });
  }

  checkOrContinue(status: TaskStatus, fileIndex: number): ConversionStatus {
    // If status == SUCCESS, return the last check
    // If status != SUCCESS, wait 1 sec and check again
    // TODO: Make an enum from the task state

    if (status.state == "SUCCESS") {
      this.displayStatusUpdate(status.message, 100, fileIndex);
      return { keepPolling: false, isSuccessful: true };
    }
    if (status.state == "FAILURE") {
      // TODO: Make an exception class to manage properly the message
      status.message = `FAILURE: ${status.message}`;
      this.displayStatusUpdate(status.message, 0, fileIndex);
      return { keepPolling: false, isSuccessful: false };
    }
    let progress = (100 * status.current) / status.total;
    if (status.total === 0) {
      progress = 0;
    }

    this.displayStatusUpdate(status.message, progress, fileIndex);
    return { keepPolling: true };
  }

  displayStatusUpdate(message: string, progress: number, fileIndex: number) {
    this.updateFileStatus(fileIndex, "progressMessage", message);
    this.updateFileStatus(fileIndex, "progress", progress);
  }
}
