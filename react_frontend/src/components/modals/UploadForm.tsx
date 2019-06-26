import * as React from "react";
import { Form, FormControl, Col, ControlLabel, FormGroup, Grid, Row, Glyphicon, HelpBlock } from 'react-bootstrap';
import * as Dropzone from "react-dropzone";
import * as Modal from "react-modal";
import * as AWS from "aws-sdk";
import * as PropTypes from "prop-types";

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

// TODO: Duplication of modalStyles in Dialogs.tsx => Find a way to fix this
const modalStyles: any = {
    content: {
        background: null,
        border: null
    }
};

interface UploadStatus {
    progress: number // between 0 and 100
    progressMessage: string;
}

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
}

interface UploadDialogProps extends CreateDatasetDialogProps, CreateVersionDialogProps {
    title: string;
    showNameField?: boolean;
    help?: string
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

    requestUpload() {
        console.log("requestUpload")
        this.setState({
            formDisabled: true
        });
        return Promise.all([
            this.getTapi().get_s3_credentials(),
            this.getTapi().get_upload_session()
        ]).then((values: Array<any>) => {
            let credentials = values[0] as S3Credentials;
            let sid = values[1] as string;
            return this.createDataset(credentials, this.state.uploadFiles, sid);
        })
    }

    uploadAndConvert(s3: AWS.S3, s3_credentials: S3Credentials, file: UploadFile, sid: string, uploadIndex: number): Promise<string> {
        let s3Key = s3_credentials.prefix + file.name;
        let params = {
            Bucket: s3_credentials.bucket,
            Key: s3Key,
            Body: file.uploadFile
        };

        let upload = new AWS.S3.ManagedUpload({
            params: params,
            service: s3
        });

        // Subscribe to measure progress
        upload.on('httpUploadProgress', (evt: any) => {
            // TODO: evt.key is not recognized in the DefinitelyType AWS, but it works. Raise an issue in Git
            let progressPercentage = Math.floor(evt.loaded / evt.total * 100);
            this.updateFileStatus(uploadIndex, "progress", progressPercentage)
        });

        // After the upload completes, run the conversion
        return upload.promise().then((s3uploadData: S3UploadedData) => {
            // TODO: Send the signal the upload is done on the AWS side, so you can begin the conversion on the backend
            // POST
            // We need to retrieve the filetype and the filename to send it to the api too

            let s3FileMetadata = {
                filename: file.name,
                filetype: "s3",
                s3Upload: {
                    format: file.uploadFormat,
                    bucket: s3_credentials.bucket,
                    key: s3Key
                }
            };

            return this.getTapi().create_datafile(sid, s3FileMetadata).then((taskStatusId) => {
                return this.initRecurringCheckStatus(uploadIndex, taskStatusId);
            }).then(() => {
                // Get the file who received this progress notification
                this.updateFileStatus(uploadIndex, "conversionProgress", "Done");

                return Promise.resolve<string>(sid)
            })
        }).catch((err: any) => {
            console.log(err);
            this.setState({
                formDisabled: false
            });
            return Promise.reject<string>(err);
        });
    }

    // Use the credentials received to upload the files dropped in the module
    createDataset(s3_credentials: S3Credentials, datafiles: Array<UploadFile>, sid: string) {
        console.log("doUpload", s3_credentials, datafiles, sid);
        // TODO: If we change the page, we lose the download
        // Configure the AWS S3 object with the received credentials
        let s3 = new AWS.S3({
            apiVersion: '2006-03-01',
            credentials: {
                accessKeyId: s3_credentials.accessKeyId,
                secretAccessKey: s3_credentials.secretAccessKey,
                sessionToken: s3_credentials.sessionToken
            }
        });

        // Looping through all the files
        let uploadPromises: Array<Promise<string>> = [];
        let uploadStatus: Array<UploadStatus> = [];

        datafiles.forEach((file: UploadFile, i: number) => {
            let status: UploadStatus;
            if (file.fileType == UploadFileType.Upload) {
                status = { progress: 0, progressMessage: "Upload starting" }
                uploadPromises.push(this.uploadAndConvert(s3, s3_credentials, file, sid, i))
            } else {
                status = { progress: 100, progressMessage: "No upload needed" }
            }
            uploadStatus.push(status)
        });

        return Promise.all(uploadPromises).then((datafile_ids: string[]) => {
            if (this.props.datasetId) {
                return this.getTapi().create_new_dataset_version(sid, this.props.datasetId, this.state.datasetDescription, datafile_ids)
            } else {
                return this.getTapi().create_dataset(sid, this.state.datasetName, this.state.datasetDescription, this.props.folderId)
            }
        });
    }

    updateFileStatus(index: number, property: string, value: any) {
        // this.setState()
        console.log("unimplemented");
    }

    initRecurringCheckStatus(fileIndex: number, taskId: string) {
        return this.getTapi().get_task_status(taskId).then((new_status: TaskStatus) => {
            return this.checkOrContinue(new_status, fileIndex);
        })
    }

    checkOrContinue(status: TaskStatus, fileIndex: number): Promise<string> {
        // If status == SUCCESS, return the last check
        // If status != SUCCESS, wait 1 sec and check again
        // TODO: Make an enum from the task state

        if (status.state == 'SUCCESS') {
            this.displayStatusUpdate(status, fileIndex);
            return Promise.resolve(status.id)
        }
        else if (status.state == 'FAILURE') {
            // TODO: Make an exception class to manage properly the message
            status.message = "FAILURE: " + status.message;
            this.displayStatusUpdate(status, fileIndex);
            return Promise.reject<string>(status.message);
        }
        else {
            this.displayStatusUpdate(status, fileIndex);
            return this.getTapi().get_task_status(status.id).then((new_status: TaskStatus) => {
                // Wait one sec Async then check again
                // setTimeout(() => {return this.checkOrContinue(status)}, 1000);
                return this.delay(1000).then(() => {
                    return this.checkOrContinue(new_status, fileIndex)
                });
            });
        }
    }

    // Async function to wait
    delay(milliseconds: number) {
        return new Promise<void>(resolve => {
            setTimeout(resolve, milliseconds);
        });
    }

    displayStatusUpdate(status: TaskStatus, fileIndex: number) {
        this.updateFileStatus(fileIndex, "conversionProgress", status.message);
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
            <button type="submit" className="btn btn-primary" disabled={this.state.formDisabled}
                onClick={(e) => {
                    e.preventDefault();
                    this.requestUpload().catch((err: any) => {
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

