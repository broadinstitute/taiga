import * as React from "react";
import {
  Modal,
  Button,
  FormGroup,
  FormControl,
  FormControlProps,
  Checkbox,
  ControlLabel,
  HelpBlock,
  Table,
} from "react-bootstrap";
import update from "immutability-helper";

import FigshareWYSIWYGEditor from "./FigshareWYSIWYGEditor";
import InfoIcon from "../InfoIcon";
import { getDefaultFilesToUpdate } from "../../utilities/figshare";

import { DatasetVersion } from "../../models/models";
import {
  ArticleInfo,
  FileToUpdate,
  UpdateArticleResponse,
  UpdateArticleRemovedFigshareFile as RemovedFigshareFile,
  UpdateArticleAdditionalTaigaDatafile as AdditionalTaigaDatafile,
  UpdateArticleUnchangedFile as UnchangedFile,
} from "../../models/figshare";
import { TaigaApi } from "../../models/api";

interface Props {
  tapi: TaigaApi;
  figshareArticleInfo: ArticleInfo;
  datasetVersion: DatasetVersion;
  onUpdateArticle: (updateArticleResponse: UpdateArticleResponse) => void;
}

interface State {
  updateSubmitted: boolean;
  description: string;
  removedFigshareFiles: ReadonlyArray<RemovedFigshareFile>;
  additionalTaigaDatafiles: ReadonlyArray<AdditionalTaigaDatafile>;
  unchangedFiles: ReadonlyArray<UnchangedFile>;
}

export default class UpdateFigshareUpdateArticleStep extends React.Component<
  Props,
  State
> {
  constructor(props: Props) {
    super(props);

    this.state = {
      updateSubmitted: false,
      description: props.figshareArticleInfo.description,
      ...getDefaultFilesToUpdate(
        props.figshareArticleInfo.files,
        props.datasetVersion.datafiles
      ),
    };
  }

  handleDescriptionChange = (description: string) => {
    this.setState({ description });
  };

  handleToggleRemoveFile(i: number) {
    this.setState({
      removedFigshareFiles: update(this.state.removedFigshareFiles, {
        [i]: { removeFile: { $apply: (cur: boolean) => !cur } },
      }),
    });
  }

  handleToggleAddFile(i: number) {
    this.setState({
      additionalTaigaDatafiles: update(this.state.additionalTaigaDatafiles, {
        [i]: { addFile: { $apply: (cur: boolean) => !cur } },
      }),
    });
  }

  handleAdditionalFileNameChange(i: number, name: string) {
    this.setState({
      additionalTaigaDatafiles: update(this.state.additionalTaigaDatafiles, {
        [i]: { name: { $set: name } },
      }),
    });
  }

  handleUploadToFigshare = () => {
    const filesToUpdate: Array<FileToUpdate> = [];

    this.state.removedFigshareFiles
      .filter((file) => file.removeFile)
      .forEach((file) =>
        filesToUpdate.push({
          figshare_file_id: file.figshareFileId,
          action: "Delete",
          datafile_id: null,
          file_name: null,
        })
      );

    this.state.additionalTaigaDatafiles
      .filter((file) => file.addFile)
      .forEach((file) =>
        filesToUpdate.push({
          figshare_file_id: null,
          action: "Add",
          datafile_id: file.datafileId,
          file_name: file.name,
        })
      );

    this.setState({ updateSubmitted: true }, () =>
      this.props.tapi
        .update_figshare_article(
          this.props.figshareArticleInfo.id,
          this.state.description,
          this.props.figshareArticleInfo.version,
          this.props.datasetVersion.id,
          filesToUpdate
        )
        .then(this.props.onUpdateArticle)
        .catch((value) => {
          console.log("failure");
          console.log(value);
        })
    );
  };

  renderRemovedFiles() {
    const { removedFigshareFiles, additionalTaigaDatafiles } = this.state;
    return (
      <>
        <h5>
          Removed Figshare files
          <InfoIcon
            tooltipId="removed-files-info-icon"
            message="Files that are in the latest Figshare article but not this dataset version."
          />
        </h5>
        {removedFigshareFiles.length == 0 ? (
          <p>None</p>
        ) : (
          <Table responsive striped bsClass="figshare-upload-files-table table">
            <thead>
              <tr>
                <th>Remove from article?</th>
                <th>Name</th>
              </tr>
            </thead>
            <tbody>
              {removedFigshareFiles.map((file, i) => {
                const matchingAddedFile = additionalTaigaDatafiles.find(
                  (f) => f.name == file.name && f.addFile
                );
                return (
                  <tr key={file.figshareFileId}>
                    <td>
                      <Checkbox
                        checked={file.removeFile}
                        onChange={() => this.handleToggleAddFile(i)}
                      />
                    </td>
                    <td>
                      <div>{file.name}</div>
                      {file.removeFile && matchingAddedFile && (
                        <HelpBlock>
                          Replaced by datafile {matchingAddedFile.datafileName}
                        </HelpBlock>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </Table>
        )}
      </>
    );
  }

  renderAdditionalFiles() {
    const {
      removedFigshareFiles,
      additionalTaigaDatafiles,
      unchangedFiles,
    } = this.state;
    return (
      <>
        <h5>
          <span>Additional Taiga datafiles</span>
          <InfoIcon
            tooltipId="additional-files-info-icon"
            message="Files that are in this dataset version but not in the latest Figshare article."
          />
        </h5>
        <Table responsive striped bsClass="figshare-upload-files-table table">
          <thead>
            <tr>
              <th>Add to article?</th>
              <th>Taiga datafile</th>
              <th>Name</th>
            </tr>
          </thead>
          <tbody>
            {additionalTaigaDatafiles.map((file, i) => {
              const addingUnnamedFile = file.addFile && !file.name;

              const fileHasSameName = (
                f: AdditionalTaigaDatafile | UnchangedFile
              ) => f.name == file.name && f.datafileId != file.datafileId;

              const addingDuplicateFileName =
                (file.addFile &&
                  additionalTaigaDatafiles.some(fileHasSameName)) ||
                unchangedFiles.some(fileHasSameName);

              return (
                <tr>
                  <td>
                    <Checkbox
                      checked={file.addFile}
                      onChange={() => {
                        this.handleToggleAddFile(i);
                      }}
                    />
                  </td>
                  <td>{file.datafileName}</td>
                  <td>
                    <FormGroup
                      validationState={
                        addingUnnamedFile
                          ? "error"
                          : addingDuplicateFileName
                          ? "warning"
                          : null
                      }
                    >
                      <FormControl
                        type="text"
                        value={file.name}
                        disabled={!file.addFile}
                        onChange={(
                          e: React.FormEvent<FormControl & FormControlProps>
                        ) =>
                          this.handleAdditionalFileNameChange(
                            i,
                            e.currentTarget.value as string
                          )
                        }
                      />
                      <FormControl.Feedback />
                      {file.addFile &&
                        removedFigshareFiles.some(
                          (f) => f.name == file.name && f.removeFile
                        ) && (
                          <HelpBlock>
                            Replaces the Figshare file of the same name
                          </HelpBlock>
                        )}
                      {addingDuplicateFileName && (
                        <HelpBlock>
                          There is another file in the article named {file.name}
                        </HelpBlock>
                      )}
                    </FormGroup>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </Table>
      </>
    );
  }

  renderUnchangedFiles() {
    const { unchangedFiles } = this.state;
    return (
      <>
        <h5>Unchanged files</h5>
        {unchangedFiles.length == 0 ? (
          <p>None</p>
        ) : (
          <details>
            <Table
              responsive
              striped
              bsClass="figshare-upload-files-table table"
            >
              <thead>
                <tr>
                  <th>Figshare file</th>
                  <th>Taiga datafile</th>
                </tr>
              </thead>
              <tbody>
                {unchangedFiles.map((file) => (
                  <tr key={file.figshareFileId}>
                    <td>{file.name}</td>
                    <td>{file.datafileName}</td>
                  </tr>
                ))}
              </tbody>
            </Table>
          </details>
        )}
      </>
    );
  }

  render() {
    const {
      removedFigshareFiles,
      additionalTaigaDatafiles,
      updateSubmitted,
    } = this.state;
    const addingUnnamedFile = additionalTaigaDatafiles.some(
      (file) => file.addFile && !!file.name
    );
    const noUpdates =
      (removedFigshareFiles.length == 0 ||
        removedFigshareFiles.every((file) => !file.removeFile)) &&
      (additionalTaigaDatafiles.length == 0 ||
        additionalTaigaDatafiles.every((file) => !file.addFile));

    return (
      <>
        <Modal.Body
          // @ts-expect-error
          bsClass="modal-body figshare-modal-body"
        >
          <FormGroup controlId="formArticleDescription">
            <ControlLabel>Description</ControlLabel>
            <FigshareWYSIWYGEditor
              value={this.state.description}
              onChange={this.handleDescriptionChange}
            />
          </FormGroup>
          {this.renderRemovedFiles()}
          {this.renderAdditionalFiles()}
          {this.renderUnchangedFiles()}
        </Modal.Body>
        <Modal.Footer>
          <Button
            disabled={addingUnnamedFile || noUpdates || updateSubmitted}
            onClick={this.handleUploadToFigshare}
          >
            Upload
          </Button>
        </Modal.Footer>
      </>
    );
  }
}
