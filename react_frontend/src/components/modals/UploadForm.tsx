import * as React from "react";
import { Form, FormControl, Col, ControlLabel, FormGroup, Label, Grid, Row, Glyphicon, HelpBlock } from 'react-bootstrap';
import * as Dropzone from "react-dropzone";
import * as Modal from "react-modal";
import { UploadStatus, UploadFileType, CreateVersionParams, CreateDatasetParams, DatasetIdAndVersionId } from "../UploadTracker";
import update from "immutability-helper";
import { UploadTable, UploadFile, UploadController } from "./UploadTable";

import { Link } from "react-router-dom";
import { relativePath } from "../../utilities/route";


interface UploadFormProps {
    help?: string
    showNameField: boolean;
    showChangesField: boolean;
    controller: UploadController;
    name: string;
    description: string
    changesDescription: string
    files: Array<UploadFile>;
    onNameChange: (value: string) => void;
    onDescriptionChange: (value: string) => void;
    onChangesDescriptionChange: (value: string) => void;
    isProcessing: boolean;
}

interface GetGCSFileResult {
    size?: number;
    errorMessage?: string;
}

interface TaigaFileSummary {
    id: string;
    size: string;
    name: string;
}

interface GetTaigaFilesResult {
    files: Array<TaigaFileSummary>;
    errorMessage?: string;
}

interface Callbacks {
    getGCSFile: (gscPath: string) => Promise<GetGCSFileResult>;
    getTaigaFiles: (taigaId: string) => Promise<GetTaigaFilesResult>;
}

const dropZoneStyle: any = {
    height: '100px',
    borderWidth: '2px',
    borderColor: 'rgb(102, 102, 102)',
    borderStyle: 'dashed',
    borderRadius: '5px'
};

import { DialogProps, DialogState } from "../Dialogs";
import {
    S3Credentials, FileUploadStatus, TaskStatus, InitialFileType,
    S3UploadedData, DatasetVersion, DatasetVersionDatafiles,
    dropExtension
} from "../../models/models";
import { TaigaApi } from "../../models/api";
import { getTaigaPrefix } from "../../utilities/route";

// TODO: Duplication of modalStyles in Dialogs.tsx => Find a way to fix this
const modalStyles: any = {
    content: {
        background: null,
        border: null
    }
};

interface UploadDialogState {
    uploadFiles: Array<UploadFile>; // uploadFiles and uploadStatus are ordered the same so they can be indexed together
    uploadStatus: Array<UploadStatus>;
    formDisabled: boolean;
    datasetName: string;
    datasetDescription: string;
    changesDescription: string;
    newDatasetVersion?: DatasetIdAndVersionId;
    isProcessing: boolean;
    error: string;
}

interface CreateDatasetDialogProps extends DialogProps {
    folderId: string; // the folder to create the new dataset within
    onOpen?: Function;
    upload(uploadFiles: Array<UploadFile>, params: (CreateVersionParams | CreateDatasetParams), uploadProgressCallback: (status: Array<UploadStatus>) => void): Promise<any>;
}

interface CreateVersionDialogProps extends DialogProps {
    datasetId: string;
    datasetPermaname: string;
    datasetName: string;

    // previousVersionName: string;
    previousVersionNumber: string;
    previousVersionFiles: Array<DatasetVersionDatafiles>;
    previousDescription: string;

    onOpen?: Function;
    upload(uploadFiles: Array<UploadFile>, params: (CreateVersionParams | CreateDatasetParams), uploadProgressCallback: (status: Array<UploadStatus>) => void): Promise<any>;
}

interface UploadDialogProps extends Partial<CreateDatasetDialogProps>, Partial<CreateVersionDialogProps> {
    title: string;
    showNameField?: boolean;
    showChangesField: boolean;
    help?: string;
}

export class CreateDatasetDialog extends React.Component<CreateDatasetDialogProps, Readonly<{}>> {
    render() {
        return (
          <UploadDialog
            title="Create new Dataset"
            help="help text"
            showNameField={true}
            showChangesField={false}
            {...this.props}
          />
        );
    }
}

export class CreateVersionDialog extends React.Component<CreateVersionDialogProps, Readonly<{}>> {
    render() {
        return (
          <UploadDialog
            title="Create new Dataset version"
            help="help text"
            showNameField={false}
            showChangesField={true}
            {...this.props}
          />
        );
    }
}

function isNonempty(v: string) {
    // this covers "" and null
    return !(!v);
}

class UploadDialog extends React.Component<UploadDialogProps, Partial<UploadDialogState>> {
    controller: UploadController;

    constructor(props: UploadDialogProps) {
        super(props);

        let files: Array<UploadFile> = [];
        if (this.props.previousVersionFiles) {
            console.log("prev", this.props.previousVersionFiles);
            files = this.props.previousVersionFiles.map(file => {
                let taigaId = this.props.datasetPermaname + "." + this.props.previousVersionNumber + "/" + file.name;
                return { name: file.name, computeNameFromTaigaId: false, size: file.short_summary, fileType: UploadFileType.TaigaPath, existingTaigaId: taigaId }
            });
        }

        this.controller = new UploadController(files, (files: any) => this.setState({ uploadFiles: files }));

        this.state = {
            uploadFiles: files,
            formDisabled: false,
            datasetName: "",
            datasetDescription: this.props.previousDescription,
            changesDescription: "",
            isProcessing: false,
            error: null
        };
    }

    requestClose() {
        this.props.cancel();
    }

    uploadProgressCallback(statuses: Array<UploadStatus>) {
        let changes = {} as any;

        statuses.forEach((status, i) => {
            changes[i] = { progress: { $set: status.progress }, progressMessage: { $set: status.progressMessage } };
        });

        this.setState(update(this.state, { uploadFiles: changes }));
    }

    render() {
        let validationError = null as string;
        if (!this.props.datasetId && !isNonempty(this.state.datasetName)) {
            validationError = "Dataset name is required";
        } else if (this.state.uploadFiles.length == 0) {
            validationError = "At least one file is required";
        }

        let submitButton: any;

        console.log("state.isProcessing is", this.state.isProcessing);
        // If we have a new datasetVersion in the state, we can show the link button
        if (this.state.newDatasetVersion) {
            submitButton = (
                <Link className="btn btn-success"
                    role="submit"
                    to={relativePath(
                        "dataset/" + this.state.newDatasetVersion.dataset_id + "/" + this.state.newDatasetVersion.version_id
                    )}>
                    See my new Dataset
                </Link>
            );
        } else if (validationError) {
            submitButton = (<button type="submit" className="btn btn-primary" disabled={true}>
                {validationError}
            </button>);
        } else if (this.state.error) {
            submitButton = (<button type="submit" className="btn btn-primary" onClick={(e => {
                e.preventDefault();
                this.setState({
                    formDisabled: false,
                    isProcessing: false,
                    error: null
                });
            })}>
                Edit
            </button>);
        } else {
            submitButton = (
                <button type="submit" className="btn btn-primary" disabled={this.state.formDisabled}
                    onClick={(e) => {
                        e.preventDefault();

                        let params: CreateDatasetParams | CreateVersionParams;
                        if (this.props.folderId) {
                            // create a new dataset
                            params = {
                                name: this.state.datasetName,
                                description: this.state.datasetDescription,
                                folderId: this.props.folderId
                            };
                        } else {
                            // create a new version
                            params = {
                                datasetId: this.props.datasetId,
                                description: this.state.datasetDescription,
                                changesDescription: this.state.changesDescription,
                            };
                        }
                        // console.log("Creating with params", params);
                        // console.log("created from", this.state);

                        this.props.upload(this.state.uploadFiles,
                            params,
                            (status) => this.uploadProgressCallback(status)).then((newDatasetVersion) => {
                                // after a successful upload, set the newDatasetVersion which will give us a link to see it.
                                this.setState({ newDatasetVersion: newDatasetVersion });
                            }).catch((error) => {
                                this.setState({ error: "" + error });
                            });

                        this.setState({
                            formDisabled: true,
                            isProcessing: true,
                            error: null
                        });
                        // console.log("isProcessing set to true");

                    }}>
                    Upload all
                </button>
            );
        }

        return (<Modal
            ariaHideApp={false}
            style={modalStyles}
            closeTimeoutMS={150}
            isOpen={this.props.isVisible}
            contentLabel="Upload">
            <div className="modal-content">
                <div className="modal-header">
                    <h2 ref="subtitle">{this.props.title}</h2>
                </div>
                <Form horizontal>
                    <div className="modal-body">
                        <UploadForm help={this.props.help}
                            controller={this.controller}
                            name={this.state.datasetName}
                            description={this.state.datasetDescription}
                            changesDescription={this.state.changesDescription}
                            files={this.state.uploadFiles}
                            showNameField={this.props.showNameField}
                            showChangesField={this.props.showChangesField}
                            onNameChange={(value: string) => this.onNameChange(value)}
                            onDescriptionChange={(value: string) => this.onDescriptionChange(value)}
                            onChangesDescriptionChange={(value: string) =>
                                this.onChangesDescriptionChange(value)
                            }
                            isProcessing={this.state.isProcessing}
                        />
                    </div>
                    <div className="modal-footer">
                        <button type="button" className="btn btn-default" onClick={(e) => {
                            this.requestClose();
                        }}>
                            Close
                        </button>
                        {submitButton}
                    </div>
                </Form>
            </div>
        </Modal>)
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

class UploadForm extends React.Component<UploadFormProps, Readonly<{}>> {
    constructor(props: any) {
        super(props);
    }

    onDrop(acceptedFiles: Array<File>, rejectedFiles: Array<File>) {
        acceptedFiles.forEach((file) => this.props.controller.addUpload(file));
    }

    addTaigaReference() {
        this.props.controller.addTaiga("", "...");
    }

    render() {
        let help = this.props.help;

        let inputName = <FormControl value={this.props.name}
            onChange={(evt) => { this.props.onNameChange((evt.target as any).value) }}
            type="text"
            placeholder="Dataset name" />

        let inputDescription = (
            <FormControl value={this.props.description}
                onChange={(evt) => { this.props.onDescriptionChange((evt.target as any).value) }}
                componentClass="textarea"
                placeholder="Dataset description" rows={10} />
        )
        let inputChanges = (
            <FormControl value={this.props.changesDescription}
                onChange={(evt) => { this.props.onChangesDescriptionChange((evt.target as any).value) }}
                componentClass="textarea"
                placeholder="Dataset description" rows={5} />
        )

        return <div>
            <div className="content">
                <div className="row">
                    <div className="col-md-7">
                        <div className="dataset-metadata" >
                            {this.props.showNameField &&
                                <FormGroup controlId="formName" style={{ marginLeft: "0px" }}>
                                    <label className="col-sm-4 col-form-label">
                                        Dataset name
                                </label>
                                    {inputName}
                                    {/* {help && <HelpBlock>{help}</HelpBlock>} */}
                                </FormGroup>
                            }
                            <FormGroup controlId="formDescription" style={{ marginLeft: "0px" }}>
                                <label className="col-sm-4 col-form-label">
                                    Description
                                </label>
                                {inputDescription}
                            </FormGroup>
                            <FormGroup controlId="formDescription" style={{ marginLeft: "0px" }}>
                                <label className="col-sm-12 col-form-label">
                                    Description of changes
                                </label>
                                {inputChanges}
                            </FormGroup>
                        </div>
                    </div>

                    <div className="col-md-5">
                        <Dropzone style={dropZoneStyle} onDrop={(acceptedFiles: any, rejectedFiles: any) =>
                            this.onDrop(acceptedFiles, rejectedFiles)}
                        >
                            <div>Try dropping some files here, or click to select files to upload.</div>
                        </Dropzone>
                        <button className="btn btn-default" style={{ marginTop: "15px" }} onClick={(e) => {
                            e.preventDefault();
                            this.addTaigaReference();
                        }}>Add reference to existing Taiga file</button>

                        <UploadTable controller={this.props.controller} files={this.props.files} isProcessing={this.props.isProcessing} />

                    </div>
                </div>
                <div className="row">
                    <div className="col-md-12">
                    </div>
                </div>
            </div>
        </div>
    }
}

