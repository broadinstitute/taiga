import * as React from "react";
import * as Dropzone from "react-dropzone";
import { Well } from "react-bootstrap";
import { UploadFileType } from "../../UploadTracker";
import UploadTable from "./UploadTable";
import UploadController from "./UploadController";
import type { UploadTableFile } from "./types";
import styles from "./UploadDialogs.scss";

interface DataVersionFileListProps {
  controller: UploadController;
  files: Array<UploadTableFile>;
  isProcessing: boolean;
  onClickAddButton: () => void;
}


function DataVersionFileList({
  controller,
  files,
  isProcessing,
  onClickAddButton,
}: DataVersionFileListProps) {
  const onDrop = (acceptedFiles: Array<File>, rejectedFiles: Array<File>) => {
    acceptedFiles.forEach((file) => controller.addUpload(file));
    onClickAddButton();

    if (rejectedFiles?.length > 0) {
      window.console.warn('Rejected files:\n', rejectedFiles);
    }
  };

  const addTaigaReference = () => {
    controller.addTaiga("", "...");
    onClickAddButton();
  };

  const addGCSPointer = () => {
    controller.addGCS("");
    onClickAddButton();
  };

  const lastFile = files?.length > 0 ? files[files.length - 1] : null;
  const shouldShowGcsHelp = lastFile?.fileType === UploadFileType.GCSPath;

  return (
    <div>
      <div className={styles.controls}>
        <Dropzone
          className={styles.dropzone}
          onDrop={onDrop}
        >
          <div>
            Try dropping some files here, or click to select files to upload.
          </div>
        </Dropzone>
        <button
          type="button"
          className="btn btn-default"
          style={{ marginTop: "15px" }}
          onClick={(e) => {
            e.preventDefault();
            addTaigaReference();
          }}
        >
          Add reference to existing Taiga file
        </button>
        <button
          type="button"
          className="btn btn-default"
          style={{ marginTop: 15, marginLeft: 15 }}
          onClick={(e) => {
            e.preventDefault();
            addGCSPointer();
          }}
        >
          Add pointer to existing GCS object
        </button>
      </div>
      <UploadTable
        controller={controller}
        files={files}
        isProcessing={isProcessing}
      />
      {shouldShowGcsHelp && (
        <Well className={styles.gcsHelp}>
          To add a pointer to a GCS object,{" "}
          <code>taiga-892@cds-logging.iam.gserviceaccount.com</code> must have{" "}
          <code>storage.buckets.get</code> access to the bucket.
        </Well>
      )}
    </div>
  );
}

export default DataVersionFileList;
