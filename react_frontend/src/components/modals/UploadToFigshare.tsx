import * as React from "react";
import { Link } from "react-router-dom";
import {
  Modal,
  Button,
  FormGroup,
  FormControl,
  FormControlProps,
  ControlLabel,
  HelpBlock,
  Table,
} from "react-bootstrap";
import update from "immutability-helper";
import Select from "react-select";

import FigshareWYSIWYGEditor from "./FigshareWYSIWYGEditor";
import FigshareUploadStatusTable from "./FigshareUploadStatusTable";

import { DatasetVersion, TaskStatus } from "../../models/models";
import { TaigaApi } from "../../models/api";
import { UploadFileStatus } from "../../models/figshare";
import { relativePath } from "../../utilities/route";

import "../../styles/modals/uploadtofigshare.css";

type Props = {
  tapi: TaigaApi;
  handleClose: (uploadComplete: boolean, figsharePrivateUrl: string) => void;
  show: boolean;
  userFigshareLinked: boolean;
  datasetName: string;
  datasetVersion: DatasetVersion;
};

type State = {
  articleTitle: string;
  articleDescription: string;
  articleLicense: number;
  articleCategories: Array<number>;
  articleKeywords: Array<string>;
  articleReferences: Array<string>;
  categories?: Array<{ value: any; label: any }>;
  licenses?: Array<{ value: any; label: any }>;
  filesToUpload: ReadonlyArray<{
    datafileId: string;
    datafileName: string;
    figshareFileName: string;
    include: boolean;
  }>;

  uploadResults: ReadonlyArray<UploadFileStatus>;
  articleId: number;
};

export default class UploadToFigshare extends React.Component<Props, State> {
  datafileIdToName: Map<string, string>;
  constructor(props: Props) {
    super(props);

    this.datafileIdToName = new Map();
    this.populateDatafileIdToNameMap(props);

    this.state = this.getDefaultStateFromProps(props);
  }

  componentDidMount() {
    this.props.tapi
      .get_figshare_article_creation_parameters()
      .then(({ licenses, categories }) =>
        this.setState({
          licenses: licenses.map((license) => {
            return { value: license.value, label: license.name };
          }),
          categories: categories.map((category) => {
            return { value: category.id, label: category.title };
          }),
        })
      );
  }

  populateDatafileIdToNameMap(props: Props) {
    props.datasetVersion.datafiles.forEach((datafile) => {
      this.datafileIdToName.set(datafile.id, datafile.name);
    });
  }

  getDefaultStateFromProps(props: Props): State {
    return {
      articleTitle: props.datasetName,
      articleDescription: "",
      articleLicense: 0,
      articleCategories: [],
      articleKeywords: [],
      articleReferences: [],
      filesToUpload: props.datasetVersion.datafiles.map((datafile) => {
        return {
          datafileId: datafile.id,
          datafileName: datafile.name,
          figshareFileName:
            datafile.type == "Raw" ? datafile.name : datafile.name + ".csv",
          include: true,
        };
      }),
      uploadResults: null,
      articleId: null,
    };
  }

  componentDidUpdate(prevProps: Props) {
    if (prevProps.datasetVersion.id != this.props.datasetVersion.id) {
      this.populateDatafileIdToNameMap(this.props);
      this.setState(this.getDefaultStateFromProps(this.props));
    }
  }

  handleArticleTitleChange = (
    e: React.FormEvent<FormControl & FormControlProps>
  ) => {
    this.setState({ articleTitle: e.currentTarget.value as string });
  };

  handleArticleDescriptionChange = (articleDescription: string) => {
    this.setState({ articleDescription });
  };

  handleArticleCategoriesChange = (
    categories: Array<{ value: number; label: string }>
  ) => {
    this.setState({ articleCategories: categories.map((c) => c.value) });
  };

  handleArticleKeywordChange = (
    e: React.FormEvent<FormControl & FormControlProps>
  ) => {
    let keywords = (e.currentTarget.value as string)
      .split(",")
      .map((kw) => kw.trim())
      .filter((kw) => kw.length > 1);
    this.setState({ articleKeywords: keywords });
  };

  handleArticleReferencesChange = (
    e: React.FormEvent<FormControl & FormControlProps>
  ) => {
    let keywords = (e.currentTarget.value as string)
      .split(",")
      .map((kw) => kw.trim())
      .filter((kw) => kw.length > 0);
    this.setState({ articleReferences: keywords });
  };

  handleArticleLicenseChange = (v: { value: number; label: string }) => {
    this.setState({ articleLicense: v.value });
  };

  handleFileNameChange = (
    e: React.FormEvent<FormControl & FormControlProps>,
    i: number
  ) => {
    this.setState({
      filesToUpload: update(this.state.filesToUpload, {
        [i]: { figshareFileName: { $set: e.currentTarget.value } },
      }),
    });
  };

  toggleIncludeFile(currentVal: boolean, i: number) {
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
          }),
        this.state.articleLicense,
        this.state.articleCategories,
        this.state.articleKeywords,
        this.state.articleReferences
      )
      .then((value) => {
        this.setState({
          uploadResults: value.files,
          articleId: value.article_id,
        });
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
    this.props.tapi.get_task_status(taskId).then((newStatus: TaskStatus) => {
      this.setState(
        {
          uploadResults: update(this.state.uploadResults, {
            [i]: { taskStatus: { $set: newStatus } },
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
          <ControlLabel>Title</ControlLabel>
          <FormControl
            type="text"
            onChange={this.handleArticleTitleChange}
            defaultValue={this.state.articleTitle}
            disabled={isUploading}
          />
        </FormGroup>

        {this.state.categories && (
          <FormGroup controlId="formArticleLicense">
            <ControlLabel>Categories</ControlLabel>
            <Select
              isMulti
              isDisabled={!this.state.categories}
              isLoading={!this.state.categories}
              isSearchable={true}
              name="article-categories"
              options={this.state.categories ? this.state.categories : []}
              onChange={this.handleArticleCategoriesChange}
            />
          </FormGroup>
        )}

        <FormGroup controlId="formArticleKeywords">
          <ControlLabel>Keyword(s)</ControlLabel>
          <FormControl
            componentClass="textarea"
            onChange={this.handleArticleKeywordChange}
            defaultValue={""}
            bsClass="form-control textarea-lock-width"
            disabled={isUploading}
          />
          <HelpBlock>Keywords separated by commas</HelpBlock>
        </FormGroup>

        <FormGroup controlId="formArticleDescription">
          <ControlLabel>Description</ControlLabel>
          <FigshareWYSIWYGEditor
            value={this.state.articleDescription}
            onChange={this.handleArticleDescriptionChange}
          />
        </FormGroup>

        <FormGroup controlId="formArticleReferences">
          <ControlLabel>References</ControlLabel>
          <FormControl
            componentClass="textarea"
            onChange={this.handleArticleReferencesChange}
            defaultValue={""}
            bsClass="form-control textarea-lock-width"
            disabled={isUploading}
          />
          <HelpBlock>References separated by commas</HelpBlock>
        </FormGroup>

        {this.state.licenses && (
          <FormGroup controlId="formArticleLicense">
            <ControlLabel>License</ControlLabel>
            <Select
              defaultValue={this.state.licenses[0]}
              isDisabled={!this.state.licenses}
              isLoading={!this.state.licenses}
              isSearchable={true}
              name="article-license"
              options={this.state.licenses ? this.state.licenses : []}
              onChange={this.handleArticleLicenseChange}
            />
          </FormGroup>
        )}

        {isUploading ? (
          <FigshareUploadStatusTable
            datafileIdToName={this.datafileIdToName}
            uploadResults={this.state.uploadResults}
          />
        ) : (
          this.renderUploadTable()
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

    return this.renderUploadForm();
  }

  render() {
    const uploadComplete =
      this.state.uploadResults &&
      this.state.uploadResults.every(
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
      figsharePrivateUrl = `https://figshare.com/account/articles/${this.state.articleId}`;
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
        <Modal.Body
          // @ts-ignore
          bsClass="modal-body figshare-modal-body"
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
