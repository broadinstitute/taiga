import * as React from "react";
import { Link } from "react-router-dom";
import {
  Modal,
  Button,
  FormGroup,
  FormControl,
  FormControlProps,
  InputGroup,
  Radio,
  ControlLabel,
  HelpBlock,
  Table,
  ProgressBar,
  DropdownButton,
  MenuItem,
} from "react-bootstrap";
import update from "immutability-helper";

import * as Models from "../../models/models";
import { TaigaApi } from "../../models/api";
import { relativePath } from "../../utilities/route";

import "../../styles/modals/uploadtofigshare.css";

type UpdateAction = "Keep" | "Replace" | "Delete" | "Add";
type FileToUpdate = {
  figshareFileId: number;
  name: string;
  datafileId: string;
  action: UpdateAction;
};

type FigshareArticleResponse = {
  id: number;
  version: number;
  authors: Array<{
    full_name: string;
    id: number;
    is_active: boolean;
  }>;
  files: Array<{
    id: number;
    is_link_only: boolean;
    name: string;
  }>;
};
type Props = {
  tapi: TaigaApi;
  handleClose: (uploadComplete: boolean, figsharePrivateUrl: string) => void;
  show: boolean;
  userFigshareAccountId: number;
  datasetVersion: Models.DatasetVersion;
};

type State = {
  articleId: string;
  figshareArticleInfo: FigshareArticleResponse;
  fetchingArticle: boolean;

  filesToUpdate: Array<FileToUpdate>;

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

export default class UpdateFigshare extends React.Component<Props, State> {
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
      articleId: "",
      figshareArticleInfo: null,
      fetchingArticle: false,
      filesToUpdate: [],
      uploadResults: undefined,
    };
  }

  componentDidUpdate(prevProps: Props) {
    if (prevProps.datasetVersion.id != this.props.datasetVersion.id) {
      this.populateDatafileIdToNameMap(this.props);
      this.setState(this.getDefaultStateFromProps(this.props));
    }
  }

  handleClose = () => {
    this.setState(
      { articleId: "", figshareArticleInfo: null, fetchingArticle: false },
      () => this.props.handleClose(false, null)
    );
  };

  handleArticleIdChange(e: React.FormEvent<FormControlProps>) {
    this.setState({
      articleId: e.currentTarget.value as string,
      figshareArticleInfo: null,
    });
  }

  handleFileActionChange(i: number, action: UpdateAction) {
    // @ts-ignore
    this.setState({
      filesToUpdate: update(this.state.filesToUpdate, {
        [i]: { action: { $set: action }, datafileId: { $set: null } },
      }),
    });
  }

  handleFileReplaceDatafileChange(i: number, datafileId: string) {
    // @ts-ignore
    this.setState({
      filesToUpdate: update(this.state.filesToUpdate, {
        [i]: { datafileId: { $set: datafileId } },
      }),
    });
  }

  handleAddNewFile = () => {
    // @ts-ignore
    this.setState({
      filesToUpdate: update(this.state.filesToUpdate, {
        $push: [
          {
            figshareFileId: null,
            name: null,
            datafileId: null,
            action: "Add",
          },
        ],
      }),
    });
  };

  handleNewFileNameChange(i: number, name: string) {
    // @ts-ignore
    this.setState({
      filesToUpdate: update(this.state.filesToUpdate, {
        [i]: { name: { $set: name } },
      }),
    });
  }

  handleRemoveNewFile(i: number) {
    // @ts-ignore
    this.setState({
      filesToUpdate: update(this.state.filesToUpdate, { $splice: [[i, 1]] }),
    });
  }

  handleFetchFigshareArticle = () => {
    this.setState({ fetchingArticle: true }, () => {
      fetch(`https://api.figshare.com/v2/articles/${this.state.articleId}`)
        .then((r) => r.json())
        .then((figshareArticleInfo: FigshareArticleResponse) =>
          this.setState({
            figshareArticleInfo,
            fetchingArticle: false,
            filesToUpdate: figshareArticleInfo.files.map((file) => {
              return {
                figshareFileId: file.id,
                name: file.name,
                datafileId: null,
                action: "Keep",
              } as FileToUpdate;
            }),
          })
        )
        .catch((r) => alert(r));
    });
  };

  handleUploadToFigshare() {
    this.props.tapi
      .update_figshare_article(
        this.state.figshareArticleInfo.id,
        this.state.figshareArticleInfo.version,
        this.props.datasetVersion.id,
        this.state.filesToUpdate
          .filter((f) => f.action != "Keep")
          .map((f) => {
            return {
              figshare_file_id: f.figshareFileId,
              action: f.action,
              datafile_id: f.datafileId,
              file_name: f.name,
            };
          })
      )
      .then((uploadResults) => {
        this.setState({
          uploadResults: {
            article_id: uploadResults.article_id,
            files: uploadResults.files.map((r) => {
              if (!r.task_id && !r.failure_reason) {
                return {
                  ...r,
                  taskStatus: {
                    id: null,
                    state: "SUCCESS",
                    message: null,
                    current: 1,
                    total: 1,
                    s3Key: null,
                  },
                };
              }
              return r;
            }),
          },
        });
        uploadResults.files.forEach((file, i) => {
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
      <Table responsive striped bsClass="figshare-upload-files-table table">
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
    const datafileIdsInUse = this.state.filesToUpdate
      .filter((f) => Boolean(f.datafileId))
      .map((f) => f.datafileId);
    const allDatafilesUsed =
      datafileIdsInUse.length == this.props.datasetVersion.datafiles.length;

    return (
      <Table responsive striped bsClass="figshare-upload-files-table table">
        <thead>
          <tr>
            <th>Figshare file</th>
            <th>Action</th>
            <th>Datafile</th>
          </tr>
        </thead>
        <tbody>
          {this.state.filesToUpdate.map((file, i) => (
            <tr key={file.figshareFileId}>
              <td>
                {file.action == "Add" ? (
                  <InputGroup>
                    <FormControl
                      type="text"
                      value={file.name}
                      placeholder="Enter text"
                      onChange={(
                        e: React.FormEvent<FormControl & FormControlProps>
                      ) =>
                        this.handleNewFileNameChange(
                          i,
                          e.currentTarget.value as string
                        )
                      }
                    />
                    <InputGroup.Button>
                      <Button onClick={() => this.handleRemoveNewFile(i)}>
                        Cancel
                      </Button>
                    </InputGroup.Button>
                  </InputGroup>
                ) : (
                  file.name
                )}
              </td>
              <td>
                {file.action == "Add" ? (
                  "Add"
                ) : (
                  <FormGroup>
                    <Radio
                      name={`update_figshare_action_${i}`}
                      inline
                      onChange={() => this.handleFileActionChange(i, "Keep")}
                      checked={file.action == "Keep"}
                    >
                      Keep
                    </Radio>
                    <Radio
                      name={`update_figshare_action_${i}`}
                      inline
                      onChange={() => this.handleFileActionChange(i, "Replace")}
                      checked={file.action == "Replace"}
                      disabled={allDatafilesUsed}
                    >
                      Replace
                    </Radio>
                    <Radio
                      name={`update_figshare_action_${i}`}
                      inline
                      onChange={() => this.handleFileActionChange(i, "Delete")}
                      checked={file.action == "Delete"}
                    >
                      Delete
                    </Radio>
                  </FormGroup>
                )}
              </td>
              <td>
                {(file.action == "Replace" || file.action == "Add") && (
                  <DropdownButton
                    title={
                      file.datafileId
                        ? this.props.datasetVersion.datafiles.find(
                            (f) => f.id == file.datafileId
                          ).name
                        : "Datafile"
                    }
                    pullRight
                    key={`replace-file-${i}`}
                    id={`replace-file-${i}`}
                  >
                    {this.props.datasetVersion.datafiles.map((datafile) => (
                      <MenuItem
                        key={datafile.id}
                        eventKey={datafile.id}
                        onSelect={(eventKey: any) =>
                          this.handleFileReplaceDatafileChange(i, eventKey)
                        }
                        disabled={
                          file.datafileId != datafile.id &&
                          datafileIdsInUse.includes(datafile.id)
                        }
                        active={file.datafileId == datafile.id}
                      >
                        {datafile.name}
                      </MenuItem>
                    ))}
                  </DropdownButton>
                )}
              </td>
            </tr>
          ))}
          <tr>
            <td>
              <Button
                disabled={allDatafilesUsed}
                onClick={this.handleAddNewFile}
              >
                Add new
              </Button>
            </td>
            <td></td>
            <td></td>
          </tr>
        </tbody>
      </Table>
    );
  }

  renderUploadForm() {
    const isUploading = !!this.state.uploadResults;
    return (
      <form>
        {isUploading
          ? this.renderUploadingStatusTable()
          : this.renderUploadTable()}
      </form>
    );
  }

  renderModalBodyContent() {
    if (this.props.userFigshareAccountId === null) {
      return (
        <p>
          You are not connected to Figshare. You can connect to Figshare via the
          link in the sidebar on the{" "}
          <Link to={relativePath("token")}>My Token</Link> page.
        </p>
      );
    }

    const authorDifferent =
      this.state.figshareArticleInfo !== null &&
      !this.state.figshareArticleInfo.authors.some(
        (author) => author.id == this.props.userFigshareAccountId
      );

    if (this.state.figshareArticleInfo === null || authorDifferent) {
      return (
        <FormGroup
          controlId="publicArticleId"
          validationState={authorDifferent ? "error" : null}
        >
          <ControlLabel>Figshare article ID</ControlLabel>
          <FormControl
            type="text"
            value={this.state.articleId}
            onChange={(e: React.FormEvent<FormControl & FormControlProps>) =>
              this.handleArticleIdChange(e)
            }
            disabled={this.state.fetchingArticle}
          />
          <FormControl.Feedback />
          {authorDifferent && (
            <HelpBlock>
              This article was published under a different Figshare account.
              Please connect your Taiga account with that Figshare account, or
              try a different article.
            </HelpBlock>
          )}
          <HelpBlock>
            The number after the article name in the public Figshare URL. For
            example, 11384241 for
            https://figshare.com/articles/DepMap_19Q4_Public/11384241
          </HelpBlock>
        </FormGroup>
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
    } else if (this.state.figshareArticleInfo === null) {
      primaryAction = (
        <Button
          bsStyle="primary"
          disabled={!this.state.articleId || this.state.fetchingArticle}
          onClick={this.handleFetchFigshareArticle}
        >
          Next
        </Button>
      );
    } else if (
      !this.state.figshareArticleInfo.authors.some(
        (author) => author.id == this.props.userFigshareAccountId
      )
    ) {
      primaryAction = (
        <Button
          onClick={() =>
            this.setState({ figshareArticleInfo: null, articleId: "" })
          }
          bsStyle="primary"
        >
          Back
        </Button>
      );
    } else {
      primaryAction = (
        <Button
          onClick={() => this.handleUploadToFigshare()}
          bsStyle="primary"
          disabled={
            this.props.userFigshareAccountId === null ||
            this.state.filesToUpdate.some(
              (f) =>
                ((f.action == "Replace" || f.action == "Add") &&
                  f.datafileId === null) ||
                (f.action == "Add" && !f.name)
            )
          }
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
          <Modal.Title>Update Figshare Article</Modal.Title>
        </Modal.Header>

        <Modal.Body
          // @ts-ignore
          bsClass="modal-body update-figshare-body"
        >
          {this.renderModalBodyContent()}
        </Modal.Body>
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
