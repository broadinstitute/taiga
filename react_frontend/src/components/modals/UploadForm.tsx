import * as React from "react";
import { Form, FormControl, Col, ControlLabel, FormGroup, Grid, Row, Glyphicon, HelpBlock } from 'react-bootstrap';
import * as Dropzone from "react-dropzone";
import * as Modal from "react-modal";
import * as PropTypes from "prop-types";
import { UploadStatus } from "../UploadTracker";
import update from "immutability-helper";
import { UploadTable, UploadFile, UploadController, UploadFileType } from "./UploadTable";

interface UploadFormProps {
    help?: string
    showNameField: boolean;
    controller: UploadController;
    name: string;
    description: string
    files: Array<UploadFile>;
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
    height: '150px',
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
}

interface CreateDatasetDialogProps extends DialogProps {
    folderId?: string; // the folder to create the new dataset within
    onFileUploadedAndConverted?: any;
    onOpen?: Function;
    upload(uploadProgressCallback: (status: Array<UploadStatus>) => void): Promise<any>;
}

interface CreateVersionDialogProps extends DialogProps {
    datasetId?: string; // if set, we will create new version, otherwise we will create a new dataset
    datasetPermaname?: string;

    previousVersionName?: string;
    previousVersionNumber?: string;
    previousVersionFiles?: Array<DatasetVersionDatafiles>;

    previousDescription?: string;
    onFileUploadedAndConverted?: any;
    onOpen?: Function;
    upload(uploadProgressCallback: (status: Array<UploadStatus>) => void): Promise<any>;
}

interface UploadDialogProps extends CreateDatasetDialogProps, CreateVersionDialogProps {
    title: string;
    showNameField?: boolean;
    help?: string;
}

export class CreateDatasetDialog extends React.Component<CreateDatasetDialogProps, any> {
    render() {
        return <UploadDialog title="Create new Dataset" help="help text" {...this.props} />
    }
}

export class CreateVersionDialog extends React.Component<CreateVersionDialogProps, any> {
    render() {
        return <UploadDialog title="Create new Dataset version" help="help text" {...this.props} />
    }
}


class UploadDialog extends React.Component<UploadDialogProps, Partial<UploadDialogState>> {
    static contextTypes = {
        tapi: PropTypes.object,
        currentUser: PropTypes.string,
        user: PropTypes.object,
    };

    controller: UploadController

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
            uploadStatus: null,
            formDisabled: false,
            datasetName: "",
            datasetDescription: this.props.previousDescription
        }
    }

    requestClose() {
        this.props.cancel();
    }

    getTapi(): TaigaApi {
        return (this.context as any).tapi as TaigaApi;
    }

    render() {
        // let newDatasetLink = undefined;
        // // If we have a new datasetVersion in the state, we can show the link button
        // if (!isNullOrUndefined(this.state.newDatasetVersion)) {
        //     newDatasetLink = (
        //         <Link className="btn btn-success"
        //             role="submit"
        //             to={relativePath(
        //                 "dataset/" + this.state.newDatasetVersion.dataset_id + "/" + this.state.newDatasetVersion.id
        //             )}>
        //             See my new Dataset
        //         </Link>
        //     );
        // }

        let uploadButton = (

            this.setState({
                formDisabled: true
            });

        <button type="submit" className="btn btn-primary" disabled={this.state.formDisabled}
            onClick={(e) => {
                e.preventDefault();
                this.props.upload().catch((err: any) => {
                    console.log("Error received: " + err);
                });
            }}>
            Upload all
            </button>
        );


        return (<Modal
            ariaHideApp={false}
            style={modalStyles}
            closeTimeoutMS={150}
            isOpen={this.props.isVisible}
            contentLabel="Upload">
            <div className="modal-content">
                <div className="modal-header">
                    <h2 ref="subtitle">{this.props.title}</h2>
                    <p>A dataset can contain one or multiple files.</p>
                    <p>Drag and drop your files below. Hit Upload when you have all your files.</p>
                </div>
                <Form horizontal>
                    <div className="modal-body">
                        <UploadForm help={this.props.help}
                            controller={this.controller}
                            name={this.state.datasetName}
                            description={this.state.datasetDescription}
                            files={this.state.uploadFiles}
                            showNameField={this.props.showNameField} />
                    </div>
                    <div className="modal-footer">
                        <button type="button" className="btn btn-default" onClick={(e) => {
                            this.requestClose();
                        }}>
                            Close
                        </button>
                        {uploadButton}
                    </div>
                </Form>
            </div>
        </Modal>)
    }
}

interface empty {
}

class UploadForm extends React.Component<UploadFormProps, empty> {
    constructor(props: any) {
        super(props);
    }

    onNameChange(value: string) {
        this.props.controller.onDatasetNameChange(value)
    }

    onDescriptionChange(value: string) {
        this.props.controller.onDescriptionChange(value)
    }

    onDrop(acceptedFiles: Array<File>, rejectedFiles: Array<File>) {
        console.log(acceptedFiles)
        acceptedFiles.forEach((file) => this.props.controller.addUpload(file))
    }

    addTaigaReference() {
        console.log("Add taiga ref")
        this.props.controller.addTaiga("", "...")
        console.log("Add taiga ref done")
    }

    render() {
        let help = this.props.help;

        let inputName = <FormControl value={this.props.name}
            onChange={(evt) => { this.onNameChange((evt.target as any).value) }}
            type="text"
            placeholder="Dataset name" />

        let inputDescription = (
            <FormControl value={this.props.description}
                onChange={(evt) => { this.onDescriptionChange((evt.target as any).value) }}
                componentClass="textarea"
                placeholder="Dataset description" />
        )

        return <div>
            <div className="content">
                <div className="row">
                    <div className="col-md-8">
                        <div className="dataset-metadata">
                            <FormGroup controlId="formName">
                                <Col componentClass={ControlLabel} sm={2}>
                                    Dataset name
                                            </Col>
                                <Col sm={10}>
                                    {inputName}
                                </Col>
                                <Col sm={10} smOffset={2}>
                                    {help && <HelpBlock>{help}</HelpBlock>}
                                </Col>
                            </FormGroup>
                            <FormGroup controlId="formDescription">
                                <Col componentClass={ControlLabel} sm={2}>
                                    Dataset description
                                </Col>
                                <Col sm={10}>
                                    {inputDescription}
                                </Col>
                            </FormGroup>
                        </div>
                    </div>

                    <div className="col-md-4">
                        <Dropzone style={dropZoneStyle} onDrop={(acceptedFiles: any, rejectedFiles: any) =>
                            this.onDrop(acceptedFiles, rejectedFiles)}
                        >
                            <div>Try dropping some files here, or click to select files to upload.</div>
                        </Dropzone>
                    </div>
                </div>
                <div className="row">
                    <div className="col-md-12">
                        <UploadTable controller={this.props.controller} files={this.props.files} />

                        <button className="btn btn-default" onClick={(e) => {
                            e.preventDefault();
                            this.addTaigaReference();
                        }}>Add reference to existing Taiga file</button>
                    </div>
                </div>
            </div>
        </div>
    }
}

