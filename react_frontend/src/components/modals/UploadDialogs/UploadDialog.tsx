import * as React from "react";
import * as Modal from "react-modal";
import { Link } from "react-router-dom";
import cx from "classnames";
import update from "immutability-helper";
import { relativePath } from "../../../utilities/route";
import {
  UploadStatus,
  UploadFileType,
  CreateVersionParams,
  CreateDatasetParams,
  DatasetIdAndVersionId,
} from "../../UploadTracker";
import UploadController from "./UploadController";
import UploadForm from "./UploadForm";
import type {
  CreateDatasetDialogProps,
  CreateVersionDialogProps,
  UploadTableFile,
} from "./types";
import styles from "./UploadDialogs.scss";

interface UploadDialogProps
  extends Partial<CreateDatasetDialogProps>,
    Partial<CreateVersionDialogProps> {
  title: string;
  showNameField?: boolean;
  showChangesField: boolean;
}

interface UploadDialogState {
  uploadFiles: Array<UploadTableFile>; // uploadFiles and uploadStatus are ordered the same so they can be indexed together
  uploadStatus: Array<UploadStatus>;
  formDisabled: boolean;
  datasetName: string;
  datasetDescription: string;
  changesDescription: string;
  newDatasetVersion?: DatasetIdAndVersionId;
  isProcessing: boolean;
  error: string;
}


function isNonempty(v: string) {
  // this covers "" and null
  return !!v;
}

export class UploadDialog extends React.Component<
  UploadDialogProps,
  Partial<UploadDialogState>
> {
  controller: UploadController;

  constructor(props: UploadDialogProps) {
    super(props);

    let files: Array<UploadTableFile> = [];
    if (this.props.previousVersionFiles) {
      files = this.props.previousVersionFiles.map((file) => {
        let taigaId =
          this.props.datasetPermaname +
          "." +
          this.props.previousVersionNumber +
          "/" +
          file.name;
        return {
          name: file.name,
          computeNameFromTaigaId: false,
          size: file.short_summary,
          fileType: UploadFileType.TaigaPath,
          existingTaigaId: taigaId,
        };
      });
    }

    this.controller = new UploadController(files, (files: UploadTableFile[]) =>
      this.setState({ uploadFiles: files })
    );

    this.state = {
      uploadFiles: files,
      formDisabled: false,
      datasetName: "",
      datasetDescription: this.props.previousDescription,
      changesDescription: "",
      isProcessing: false,
      error: null,
    };
  }

  requestClose() {
    this.props.cancel();
  }

  uploadProgressCallback(statuses: Array<UploadStatus>) {
    let changes = {} as any;

    statuses.forEach((status, i) => {
      changes[i] = {
        progress: { $set: status.progress },
        progressMessage: { $set: status.progressMessage },
      };
    });

    this.setState(update(this.state, { uploadFiles: changes }));
  }

  render() {
    let validationError = null as string;

    if (this.props.showChangesField && !this.state.changesDescription) {
      validationError = "Description of changes cannot be empty";
    }

    if (!this.props.datasetId && !isNonempty(this.state.datasetName)) {
      validationError = "Dataset name is required";
    } else if (this.state.uploadFiles.length == 0) {
      validationError = "At least one file is required";
    }

    let submitButton: any;

    // If we have a new datasetVersion in the state, we can show the link button
    if (this.state.newDatasetVersion) {
      submitButton = (
        <Link
          className="btn btn-success"
          role="submit"
          to={relativePath(
            "dataset/" +
              this.state.newDatasetVersion.dataset_id +
              "/" +
              this.state.newDatasetVersion.version_id
          )}
        >
          See my new Dataset
        </Link>
      );
    } else if (validationError) {
      submitButton = (
        <button type="submit" className="btn btn-primary" disabled={true}>
          {validationError}
        </button>
      );
    } else if (this.state.error) {
      submitButton = (
        <button
          type="submit"
          className="btn btn-primary"
          onClick={(e) => {
            e.preventDefault();
            this.setState({
              formDisabled: false,
              isProcessing: false,
              error: null,
            });
          }}
        >
          Edit
        </button>
      );
    } else {
      submitButton = (
        <button
          type="submit"
          className="btn btn-primary"
          disabled={this.state.formDisabled}
          onClick={(e) => {
            e.preventDefault();

            let params: CreateDatasetParams | CreateVersionParams;
            if (this.props.folderId) {
              // create a new dataset
              params = {
                name: this.state.datasetName,
                description: this.state.datasetDescription,
                folderId: this.props.folderId,
              };
            } else {
              // create a new version
              params = {
                datasetId: this.props.datasetId,
                description: this.state.datasetDescription,
                changesDescription: this.state.changesDescription,
              };
            }

            this.props
              .upload(this.state.uploadFiles, params, (status) =>
                this.uploadProgressCallback(status)
              )
              .then((newDatasetVersion) => {
                if (newDatasetVersion === null) {
                  this.setState({ error: "File conversion failed" });
                } else {
                  // after a successful upload, set the newDatasetVersion which will give us a link to see it.
                  this.setState({ newDatasetVersion: newDatasetVersion });
                }
              })
              .catch((error) => {
                this.setState({ error: "" + error });
              });

            this.setState({
              formDisabled: true,
              isProcessing: true,
              error: null,
            });
          }}
        >
          Upload all
        </button>
      );
    }

    return (
      <Modal
        className={styles.Modal}
        ariaHideApp={false}
        closeTimeoutMS={150}
        isOpen={this.props.isVisible}
        contentLabel="Upload"
      >
        <div className="modal-content">
          <div className="modal-header">
            <h2 ref="subtitle">{this.props.title}</h2>
          </div>
            <div className={cx("modal-body", styles.modalBody)}>
              <UploadForm
                controller={this.controller}
                name={this.state.datasetName}
                description={this.state.datasetDescription}
                changesDescription={this.state.changesDescription}
                files={this.state.uploadFiles}
                showNameField={this.props.showNameField}
                showChangesField={this.props.showChangesField}
                onNameChange={(value: string) => this.onNameChange(value)}
                onDescriptionChange={(value: string) =>
                  this.onDescriptionChange(value)
                }
                onChangesDescriptionChange={(value: string) =>
                  this.onChangesDescriptionChange(value)
                }
                isProcessing={this.state.isProcessing}
              />
            </div>
            <div className="modal-footer" style={{ marginTop: 0 }}>
              <button
                type="button"
                className="btn btn-default"
                onClick={(e) => {
                  this.requestClose();
                }}
              >
                Close
              </button>
              {submitButton}
            </div>
        </div>
      </Modal>
    );
  }

  onNameChange(value: string) {
    this.setState({ datasetName: value });
  }

  onDescriptionChange(value: string) {
    this.setState({ datasetDescription: value });
  }

  onChangesDescriptionChange(value: string) {
    this.setState({ changesDescription: value });
  }
}
