import * as React from "react";
import { Form, FormControl, Col, ControlLabel, FormGroup, Grid, Row, Glyphicon, HelpBlock } from 'react-bootstrap';
import * as Dropzone from "react-dropzone";
import * as Modal from "react-modal";

import update from "immutability-helper";
import { UploadTable, UploadFile, UploadController, UploadFileType } from "./UploadTable";

interface UploadFormProps {
    help?: string
    initialFiles: Array<UploadFile>;
}

interface UploadFormState {
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
    S3UploadedFileMetadata, S3UploadedData, DatasetVersion, DatasetVersionDatafiles,
    dropExtension
} from "../../models/models";

interface UploadDialogProps extends DialogProps {
    onFileUploadedAndConverted?: any;

    title: string;
    readOnlyName?: string;
    readOnlyDescription?: string;

    // Determines what is done when opening the modal/componentWillReceiveProps
    onOpen?: Function;
    // Parent gives the previous version files. If it exists, we display another Table
    previousVersionFiles?: Array<DatasetVersionDatafiles>;
    // Parent can give the previous version name. Need it if pass previousVersionFiles
    // TODO: Only pass the previousVersion, so we can take the previous DataFiles from it too
    previousVersionName?: string;
    datasetPermaname?: string;
    previousVersionNumber?: string;

    // If we want to change the description, we can use this to pass the previous description
    // It can't be compatible with readOnlyDescription
    previousDescription?: string;

    validationState?: string;
    help?: string;
}

// TODO: Duplication of modalStyles in Dialogs.tsx => Find a way to fix this
const modalStyles: any = {
    content: {
        background: null,
        border: null
    }
};

// name: string; // the name of the datafile record in once dataset has been created
// size: string; // desciption of size

// fileType: UploadFileType;

// gcsPath?: string; // If the path to a GCS object

// exitingTaigaId?: string; // the ID of an existing taiga data file.

// uploadFile?: File;
// uploadFormat?: string;
// progress?: number; // between 0 and 1
// progressMessage?: string;


export class UploadDialog extends React.Component<UploadDialogProps, null> {
    render() {
        let files = this.props.previousVersionFiles.map(file => {
            let taigaId = this.props.datasetPermaname + "." + this.props.previousVersionNumber + "/" + file.name;
            return { name: file.name, size: file.short_summary, fileType: UploadFileType.TaigaPath, existingTaigaId: taigaId }
        });

        return (<Modal
            style={modalStyles}
            closeTimeoutMS={150}
            isOpen={this.props.isVisible}
            contentLabel="Upload">
            <UploadForm help={this.props.help} initialFiles={files} />
        </Modal>)
    }
}

export class UploadForm extends React.Component<UploadFormProps, UploadFormState> {
    controller: UploadController

    constructor(props: any) {
        super(props);
        this.state = {
            name: "",
            description: "",
            files: []
        }

        this.controller = new UploadController((files: any) => this.setState({ files: files }));
    }

    onNameChange(value: string) {
        this.setState({ name: value })
    }

    onDescriptionChange(value: string) {
        this.setState({ description: value })
    }

    onDrop(acceptedFiles: Array<File>, rejectedFiles: Array<File>) {
        console.log(acceptedFiles)
        console.log("controller", this.controller);
        acceptedFiles.forEach((file) => this.controller.addUpload(file))
    }

    render() {
        let help = this.props.help;

        let inputName = <FormControl value={this.state.name}
            onChange={(evt) => { this.onNameChange((evt.target as any).value) }}
            type="text"
            placeholder="Dataset name" />

        let inputDescription = (
            <FormControl value={this.state.description}
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
                        <UploadTable controller={this.controller} files={this.state.files} />
                    </div>
                </div>
            </div>
        </div>
    }
}

