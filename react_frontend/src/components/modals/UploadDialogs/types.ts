import { DatasetVersionDatafiles } from "../../../models/models";
import { UploadFile } from "../../UploadTracker";
import { DialogProps } from "../../Dialogs";
import {
  UploadStatus,
  CreateVersionParams,
  CreateDatasetParams,
} from "../../UploadTracker";

export interface UploadTableFile extends UploadFile {
  size: string; // desciption of size

  computeNameFromTaigaId: boolean;

  progress?: number; // between 0 and 100
  progressMessage?: string;
}

export interface CreateDatasetDialogProps extends DialogProps {
  folderId: string; // the folder to create the new dataset within
  onOpen?: Function;
  upload(
    uploadFiles: Array<UploadTableFile>,
    params: CreateVersionParams | CreateDatasetParams,
    uploadProgressCallback: (status: Array<UploadStatus>) => void
  ): Promise<any>;
}

export interface CreateVersionDialogProps extends DialogProps {
  datasetId: string;
  datasetPermaname: string;
  datasetName: string;

  // previousVersionName: string;
  previousVersionNumber: string;
  previousVersionFiles: Array<DatasetVersionDatafiles>;
  previousDescription: string;

  onOpen?: Function;
  upload(
    uploadFiles: Array<UploadTableFile>,
    params: CreateVersionParams | CreateDatasetParams,
    uploadProgressCallback: (status: Array<UploadStatus>) => void
  ): Promise<any>;
  checkConcurrentEdit: () => Promise<boolean>;
}
