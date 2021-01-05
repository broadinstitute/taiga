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
  DropdownButton,
  MenuItem,
} from "react-bootstrap";
import update from "immutability-helper";

import FigshareWYSIWYGEditor from "./FigshareWYSIWYGEditor";
import FigshareUploadStatusTable from "./FigshareUploadStatusTable";
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

type Props = {
  tapi: TaigaApi;
  handleClose: (uploadComplete: boolean, figsharePrivateUrl: string) => void;
  show: boolean;
  userFigshareLinked: boolean;
  datasetVersion: Models.DatasetVersion;
};

type State = {
  articleId: string;
  description: string;
  figshareArticleInfo: Models.FigshareArticleInfo;
  fetchingArticle: boolean;
  articleDoesNotExists: boolean;
  articleAuthorsDoNotMatch: boolean;

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
      description: "",
      figshareArticleInfo: null,
      fetchingArticle: false,
      articleDoesNotExists: false,
      articleAuthorsDoNotMatch: false,
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

  handleClose = (uploadComplete: boolean, figsharePrivateUrl: string) => {
    this.setState(this.getDefaultStateFromProps(this.props), () =>
      this.props.handleClose(uploadComplete, figsharePrivateUrl)
    );
  };

  handleArticleIdChange(e: React.FormEvent<FormControlProps>) {
    this.setState({
      articleId: e.currentTarget.value as string,
      figshareArticleInfo: null,
    });
  }

  handleDescriptionChange = (description: string) => {
    this.setState({ description });
  };

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
      this.props.tapi
        .get_figshare_article(parseInt(this.state.articleId))
        .then((figshareArticleInfo) => {
          this.setState({
            description: figshareArticleInfo.description,
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
          });
        })
        .catch((reason) => {
          if ("Not Found" in reason) {
            this.setState({ articleDoesNotExists: true });
          } else if ("Forbidden" in reason) {
            this.setState({ articleAuthorsDoNotMatch: true });
          } else {
            console.log(reason);
          }
        });
    });
  };

  handleUploadToFigshare() {
    this.props.tapi
      .update_figshare_article(
        this.state.figshareArticleInfo.id,
        this.state.description,
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
        {isUploading ? (
          <FigshareUploadStatusTable
            datafileIdToName={this.datafileIdToName}
            uploadResults={this.state.uploadResults}
          />
        ) : (
          <>
            <FormGroup controlId="formArticleDescription">
              <ControlLabel>Description</ControlLabel>
              <FigshareWYSIWYGEditor
                value={this.state.description}
                onChange={this.handleDescriptionChange}
              />
            </FormGroup>
            {this.renderUploadTable()}
          </>
        )}
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

    const {
      figshareArticleInfo,
      articleDoesNotExists,
      articleAuthorsDoNotMatch,
      articleId,
      fetchingArticle,
    } = this.state;

    if (figshareArticleInfo === null) {
      return (
        <FormGroup
          controlId="publicArticleId"
          validationState={
            articleDoesNotExists || articleAuthorsDoNotMatch ? "error" : null
          }
        >
          <ControlLabel>Figshare article ID</ControlLabel>
          <FormControl
            type="text"
            value={articleId}
            onChange={(e: React.FormEvent<FormControl & FormControlProps>) =>
              this.handleArticleIdChange(e)
            }
            disabled={fetchingArticle}
          />
          <FormControl.Feedback />
          {articleAuthorsDoNotMatch && (
            <HelpBlock>
              This article was published under a different Figshare account.
              Please connect your Taiga account with that Figshare account, or
              try a different article.
            </HelpBlock>
          )}
          {articleDoesNotExists && (
            <HelpBlock>No public article was found for this ID</HelpBlock>
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
      this.state.articleDoesNotExists ||
      this.state.articleAuthorsDoNotMatch
    ) {
      primaryAction = (
        <Button
          onClick={() =>
            this.setState({
              figshareArticleInfo: null,
              articleId: "",
              articleDoesNotExists: false,
              articleAuthorsDoNotMatch: false,
            })
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
            !this.props.userFigshareLinked ||
            this.state.filesToUpdate.some(
              (f) =>
                ((f.action == "Replace" || f.action == "Add") &&
                  f.datafileId === null) ||
                (f.action == "Add" && !f.name)
            ) ||
            this.state.filesToUpdate.every((f) => f.action == "Keep")
          }
        >
          Upload to Figshare
        </Button>
      );
    }
    return (
      <Modal
        show={this.props.show}
        onHide={() => this.handleClose(uploadComplete, figsharePrivateUrl)}
        dialogClassName="upload-to-figshare-modal"
      >
        <Modal.Header closeButton>
          <Modal.Title>Update Figshare Article</Modal.Title>
        </Modal.Header>

        <Modal.Body
          // @ts-ignore
          bsClass="modal-body figshare-modal-body"
        >
          {this.renderModalBodyContent()}
        </Modal.Body>
        <Modal.Footer>
          <Button
            onClick={() => this.handleClose(uploadComplete, figsharePrivateUrl)}
          >
            Close
          </Button>
          {primaryAction}
        </Modal.Footer>
      </Modal>
    );
  }
}
