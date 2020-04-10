import * as React from "react";
import { Link } from "react-router-dom";
import {
  Modal,
  Button,
  FormGroup,
  FormControl,
  FormControlProps,
  ControlLabel,
  Table,
  ProgressBar,
} from "react-bootstrap";
import update from "immutability-helper";

import * as Models from "../../models/models";
import { TaigaApi } from "../../models/api";
import { relativePath } from "../../utilities/route";

import "../../styles/modals/uploadtofigshare.css";
type Props = {
  tapi: TaigaApi;
  handleClose: (uploadComplete: boolean, figsharePrivateUrl: string) => void;
  show: boolean;
  userFigshareLinked: boolean;
  datasetVersion: Models.DatasetVersion;
};

type State = {
  articleTitle: string;
  articleDescription: string;
  filesToUpload: Array<{
    datafileId: string;
    datafileName: string;
    figshareFileName: string;
    include: boolean;
  }>;
  uploadResults?: {
    article_id: number;
    files: Array<{
      datafile_id: string;
      file_name: string;
      task_id?: string;
      failure_reason?: string;
      taskStatus?: Models.TaskStatus;
    }>;
  };
};

export default class UploadToFigshare extends React.Component<Props, State> {
  datafileIdToName: Map<string, string>;
  constructor(props: Props) {
    super(props);

    this.datafileIdToName = new Map();
    this.populateDatafileIdToNameMap(props);

    this.state = this.getDefaultStateFromProps(props);
  }

  populateDatafileIdToNameMap(props: Props) {
    props.datasetVersion.datafiles.forEach((datafile) => {
      this.datafileIdToName.set(datafile.id, datafile.name);
    });
  }

  getDefaultStateFromProps(props: Props): State {
    return {
      articleTitle: props.datasetVersion.dataset.name,
      articleDescription: "",
      filesToUpload: props.datasetVersion.datafiles.map((datafile) => {
        return {
          datafileId: datafile.id,
          datafileName: datafile.name,
          figshareFileName:
            datafile.type == "Raw" ? datafile.name : datafile.name + ".csv",
          include: true,
        };
      }),
      uploadResults: undefined,
    };
  }

  componentDidUpdate(prevProps: Props) {
    if (prevProps.datasetVersion.id != this.props.datasetVersion.id) {
      this.populateDatafileIdToNameMap(this.props);
      this.setState(this.getDefaultStateFromProps(this.props));
    }
  }

  handleArticleTitleChange(e: React.FormEvent<FormControlProps>) {
    this.setState({ articleTitle: e.currentTarget.value as string });
  }

  handleArticleDescriptionChange(e: React.FormEvent<FormControlProps>) {
    this.setState({ articleDescription: e.currentTarget.value as string });
  }

  handleFileNameChange(e: React.FormEvent<FormControlProps>, i: number) {
    // @ts-ignore
    this.setState({
      filesToUpload: update(this.state.filesToUpload, {
        [i]: { figshareFileName: { $set: e.currentTarget.value } },
      }),
    });
  }

  toggleIncludeFile(currentVal: boolean, i: number) {
    // @ts-ignore
    this.setState({
      filesToUpload: update(this.state.filesToUpload, {
        [i]: { include: { $set: !currentVal } },
      }),
    });
  }

  handleUploadToFigshare() {
    this.props.tapi
      .upload_dataset_version_to_figshare(
        this.props.datasetVersion.id,
        this.state.articleTitle,
        this.state.articleDescription,
        this.state.filesToUpload
          .filter((fileToUpload) => fileToUpload.include)
          .map((fileToUpload) => {
            return {
              datafile_id: fileToUpload.datafileId,
              file_name: fileToUpload.figshareFileName,
            };
          })
      )
      .then((value) => {
        this.setState({ uploadResults: value });
        value.files.forEach((file, i) => {
          if (file.task_id) {
            this.pollUploadToFigshareFile(i, file.task_id);
          }
        });
      })
      .catch((value) => {
        console.log("failure");
        console.log(value);
      });
  }

  pollUploadToFigshareFile(i: number, taskId: string) {
    this.props.tapi
      .get_task_status(taskId)
      .then((newStatus: Models.TaskStatus) => {
        this.setState(
          // @ts-ignore
          {
            uploadResults: update(this.state.uploadResults, {
              files: {
                [i]: { taskStatus: { $set: newStatus } },
              },
            }),
          },
          () => {
            if (newStatus.state != "SUCCESS" && newStatus.state != "FAILURE") {
              setTimeout(() => this.pollUploadToFigshareFile(i, taskId), 1000);
            }
          }
        );
      });
  }

  renderUploadingStatusTable() {
    return (
      <Table responsive striped bsClass="table figshare-upload-files-table">
        <thead>
          <tr>
            <th>Datafile</th>
            <th>Upload status</th>
          </tr>
        </thead>
        <tbody>
          {this.state.uploadResults.files.map((file, i) => {
            let progressIndicator = null;

            const state = file.taskStatus ? file.taskStatus.state : null;
            if (file.failure_reason) {
              progressIndicator = (
                <ProgressBar
                  now={0}
                  label={`Failed to upload: ${file.failure_reason}`}
                  bsStyle="danger"
                />
              );
            } else if (state == "PROGRESS") {
              progressIndicator = (
                <ProgressBar
                  now={file.taskStatus.current * 100}
                  label="Uploading"
                />
              );
            } else if (state == "SUCCESS") {
              progressIndicator = <ProgressBar now={100} label="Uploaded" />;
            } else if (state == "FAILURE") {
              progressIndicator = (
                <ProgressBar
                  now={file.taskStatus.current * 100}
                  label={"Failed to upload"}
                  bsStyle="danger"
                />
              );
            }

            return (
              <tr key={file.datafile_id}>
                <td>{this.datafileIdToName.get(file.datafile_id)}</td>
                <td>{progressIndicator}</td>
              </tr>
            );
          })}
        </tbody>
      </Table>
    );
  }

  renderUploadTable() {
    return (
      <Table responsive striped bsClass="table figshare-upload-files-table">
        <thead>
          <tr>
            <th>Include</th>
            <th>Datafile</th>
            <th>Figshare file name</th>
          </tr>
        </thead>
        <tbody>
          {this.state.filesToUpload.map((fileToUpload, i) => (
            <tr key={fileToUpload.datafileId}>
              <td>
                <input
                  type="checkbox"
                  checked={fileToUpload.include}
                  onChange={() =>
                    this.toggleIncludeFile(fileToUpload.include, i)
                  }
                />
              </td>
              <td>{fileToUpload.datafileName}</td>
              <td>
                <FormControl
                  type="text"
                  onChange={(
                    e: React.FormEvent<FormControl & FormControlProps>
                  ) => this.handleFileNameChange(e, i)}
                  value={this.state.filesToUpload[i].figshareFileName}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </Table>
    );
  }

  renderUploadForm() {
    const isUploading = !!this.state.uploadResults;
    return (
      <form>
        <FormGroup controlId="formArticleTitle">
          <ControlLabel>Figshare article title</ControlLabel>
          <FormControl
            type="text"
            onChange={(e: React.FormEvent<FormControl & FormControlProps>) =>
              this.handleArticleTitleChange(e)
            }
            value={this.state.articleTitle}
            disabled={isUploading}
          />
        </FormGroup>
        <FormGroup controlId="formArticleDescription">
          <ControlLabel>Figshare article description</ControlLabel>
          <FormControl
            componentClass="textarea"
            onChange={(e: React.FormEvent<FormControl & FormControlProps>) =>
              this.handleArticleDescriptionChange(e)
            }
            value={this.state.articleDescription}
            bsClass="form-control textarea-lock-width"
            disabled={isUploading}
          />
        </FormGroup>
        {isUploading
          ? this.renderUploadingStatusTable()
          : this.renderUploadTable()}
      </form>
    );
  }

  renderModalBodyContent() {
    if (!this.props.userFigshareLinked) {
      return (
        <p>
          You are not connected to Figshare. You can connect to Figshare via the
          link in the sidebar on the{" "}
          <Link to={relativePath("token")}>My Token</Link> page.
        </p>
      );
    }

    return this.renderUploadForm();
  }

  render() {
    const uploadComplete =
      this.state.uploadResults &&
      this.state.uploadResults.files.every(
        (file) =>
          !!file.failure_reason ||
          (file.taskStatus &&
            (file.taskStatus.state == "SUCCESS" ||
              file.taskStatus.state == "FAILURE"))
      );

    const isUploading = !!this.state.uploadResults && !uploadComplete;

    let primaryAction = null;
    let figsharePrivateUrl: string = null;
    if (uploadComplete) {
      figsharePrivateUrl = `https://figshare.com/account/articles/${this.state.uploadResults.article_id}`;
      primaryAction = (
        <Button bsStyle="success" href={figsharePrivateUrl} target="_blank">
          See your new Figshare article
        </Button>
      );
    } else if (isUploading) {
      primaryAction = (
        <Button bsStyle="primary" disabled={true}>
          Uploading to Figshare...
        </Button>
      );
    } else {
      primaryAction = (
        <Button
          onClick={() => this.handleUploadToFigshare()}
          bsStyle="primary"
          disabled={!this.props.userFigshareLinked}
        >
          Upload to Figshare
        </Button>
      );
    }
    return (
      <Modal
        show={this.props.show}
        onHide={() =>
          this.props.handleClose(uploadComplete, figsharePrivateUrl)
        }
        dialogClassName="upload-to-figshare-modal"
      >
        <Modal.Header closeButton>
          <Modal.Title>Upload to Figshare</Modal.Title>
        </Modal.Header>
        <Modal.Body>{this.renderModalBodyContent()}</Modal.Body>
        <Modal.Footer>
          <Button
            onClick={() =>
              this.props.handleClose(uploadComplete, figsharePrivateUrl)
            }
          >
            Close
          </Button>
          {primaryAction}
        </Modal.Footer>
      </Modal>
    );
  }
}
