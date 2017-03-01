import * as React from "react";
import {Link} from 'react-router';
import * as Modal from "react-modal";

import * as AWS from "aws-sdk";
import * as Dropzone from "react-dropzone";
import * as filesize from "filesize";

import {BootstrapTable, TableHeaderColumn, SelectRowMode, CellEditClickMode, CellEdit} from "react-bootstrap-table";
import {Form, FormControl, Col, ControlLabel, FormGroup, Grid, Row, Glyphicon, HelpBlock} from 'react-bootstrap';

import {DialogProps, DialogState} from "../Dialogs";

import {TypeEditorBootstrapTable} from "./TypeEditorBootstrapTable";

import {getInitialFileTypeFromMimeType} from "../../utilities/formats";
import {relativePath} from "../../utilities/route";

import {
    S3Credentials, FileUploadStatus, TaskStatus, InitialFileType,
    S3UploadedFileMetadata, S3UploadedData, DatasetVersion, DatasetVersionDatafiles
} from "../../models/models";

import {TaigaApi} from "../../models/api";
import {isNullOrUndefined} from "util";
import update = require("immutability-helper");


interface DropzoneProps extends DialogProps {
    onFileUploadedAndConverted?: any;
    currentFolderId: string;

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

    validationState?: string;
    help?: string;
}

interface DropzoneState extends DialogState {
    filesStatus?: Array<FileUploadStatus>;
    previousFilesStatus?: Array<FileUploadStatus>;
    disableUpload?: boolean;
    datasetFormDisabled?: boolean;
    nameValue?: string;
    descriptionValue?: string;
    newDatasetVersion?: DatasetVersion;

    // For Previous datafile selection
    previousVersionFilesIdsSelected?: Array<DatasetVersionDatafiles>;

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

const dropZoneStyle: any = {
    height: '75px',
    borderWidth: '2px',
    borderColor: 'rgb(102, 102, 102)',
    borderStyle: 'dashed',
    borderRadius: '5px'
};

const rowUploadFiles: any = {
    paddingTop: '15px'
};

let tapi: TaigaApi = null;

let credentials: S3Credentials = null;

export class UploadDataset extends React.Component<DropzoneProps, DropzoneState> {
    static contextTypes = {
        tapi: React.PropTypes.object
    };

    constructor(props: any) {
        super(props);

        // TODO: How can we ensure we are not erasing/forgetting states defined in the interface?
        this.state = {
            filesStatus: new Array<FileUploadStatus>(),
            disableUpload: true,
            datasetFormDisabled: false,
            nameValue: '',
            descriptionValue: '',
            previousVersionFilesIdsSelected: [],
            validationState: null,
            help: null
        }
    }

    componentDidMount() {
        tapi = (this.context as any).tapi;

        // We need to retrieve now the s3 credentials, so we can build the FileStatus properly
        // TODO: We should not allow the use of the form while we wait for these credentials
        tapi.get_s3_credentials().then((_credentials: S3Credentials) => {
            console.log("Received credentials! ");
            console.log("- Access key id: " + _credentials.accessKeyId);
            credentials = _credentials;
        });
    }

    componentWillReceiveProps(nextProps: any) {
        // We clean the filesStatus when we open this Upload Modal (isVisible is True, and previously was False)
        if (nextProps.isVisible && !this.props.isVisible) {
            // We clean the uploadedFileStatus
            this.setState({
                filesStatus: new Array<FileUploadStatus>(),
                newDatasetVersion: undefined,
                previousVersionFilesIdsSelected: [],
                validationState: null,
                help: null
            });

            // We renew the s3_credentials
            this.renew_s3_credentials();
        }
    }

    renew_s3_credentials() {
        tapi.get_s3_credentials().then((_credentials: S3Credentials) => {
            console.log("Received credentials! ");
            console.log("- Access key id: " + _credentials.accessKeyId);
            credentials = _credentials;
        });
    }

    // When files are put in the drop zone
    onDrop(acceptedFiles: Array<File>, rejectedFiles: Array<File>) {
        // We construct the FileStatusUpload object for each accepted files
        let currentFilesUploadStatus = this.state.filesStatus;
        let newFilesUploadStatus = acceptedFiles.map((file) => {
            return new FileUploadStatus(file, credentials.prefix);
        });
        // We append to the existing files the new ones
        Array.prototype.push.apply(currentFilesUploadStatus, newFilesUploadStatus);

        this.setState({
            filesStatus: currentFilesUploadStatus
        });
        this.setState({
            disableUpload: false,
            datasetFormDisabled: false
        });
    }

    // Ask the credentials to be able to upload
    requestUpload() {
        // We check the name is not empty
        if (isNullOrUndefined(this.props.readOnlyName) && (isNullOrUndefined(this.state.nameValue) || !this.state.nameValue)) {
            // We set the form as error and we don't trigger the rest
            this.setState({
                validationState: "error",
                help: "Please enter a name for your dataset"
            });
            return Promise.reject("Dataset is not named");
        }
        else {
            this.setState({
                validationState: null,
                help: null
            });
            // Request creation of Upload session => sid
            return tapi.get_upload_session().then((sid: string) => {
                // doUpload with this sid
                return this.doUpload(credentials, this.state.filesStatus, sid);
            });
        }
    }

    // Use the credentials received to upload the files dropped in the module
    doUpload(s3_credentials: S3Credentials, filesStatus: Array<FileUploadStatus>, sid: string) {
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
        let promises_fileUpload: Array<Promise<string>> = filesStatus.map((file: FileUploadStatus) => {
            // TODO: Find a better way to manage the prefix associated with the sid, since we currently receive them both separatly
            let fileUploadStatus: FileUploadStatus = this.retrieveFileStatus(file.s3Key);
            let newPrefix = credentials.prefix + sid + "/";
            fileUploadStatus.recreateS3Key(newPrefix);

            this.saveFileStatus(fileUploadStatus);
            let params = {
                Bucket: s3_credentials.bucket,
                Key: file.s3Key,
                Body: file.file
            };

            let upload = new AWS.S3.ManagedUpload({
                params: params,
                service: s3
            });

            // Subscribe to measure progress
            upload.on('httpUploadProgress', (evt: any) => {
                // TODO: evt.key is not recognized in the DefinitelyType AWS, but it works. Raise an issue in Git
                let updatedFilesStatus = this.retrieveFileStatus(evt.key);

                let progressPercentage = Math.floor(evt.loaded / evt.total * 100);
                updatedFilesStatus.progress = progressPercentage;

                this.saveFileStatus(updatedFilesStatus);

                this.setState({
                    disableUpload: true,
                    datasetFormDisabled: true
                });
            });

            // Create an upload promise via the aws sdk and launch it
            let uploadPromise = upload.promise();
            // TODO: Manage all the errors that can come along the way
            return uploadPromise.then((s3uploadeData: S3UploadedData) => {
                // TODO: Send the signal the upload is done on the AWS side, so you can begin the conversion on the backend
                // POST
                // We need to retrieve the filetype and the filename to send it to the api too
                let uploadedFileStatus = this.retrieveFileStatus(s3uploadeData.Key);

                let s3FileMetadata = new S3UploadedFileMetadata(s3uploadeData,
                    uploadedFileStatus.fileName,
                    uploadedFileStatus.fileType);

                return tapi.create_datafile(sid, s3FileMetadata
                ).then((taskStatusId) => {
                    return this.initRecurringCheckStatus(taskStatusId, s3FileMetadata.key);
                }).then(() => {
                    // Get the file who received this progress notification
                    let updatedFileStatus = this.retrieveFileStatus(s3FileMetadata.key);
                    updatedFileStatus.conversionProgress = "Done";
                    this.saveFileStatus(updatedFileStatus);

                    return Promise.resolve<string>(sid)
                }).catch((err: any) => {
                    return Promise.reject<string>(err);
                });
            }).catch((err: any) => {
                console.log(err);
                this.setState({
                    disableUpload: false,
                    datasetFormDisabled: false
                });
                return Promise.reject<string>(err);
            });
        });
        // Then we create the dataset if all have been resolved
        Promise.all(promises_fileUpload).then((sids) => {
            sid = sids[0].toString();

            this.props.onFileUploadedAndConverted(
                sid,
                this.state.nameValue,
                this.state.descriptionValue,
                this.state.previousVersionFilesIdsSelected
            ).then((newDatasetVersion: DatasetVersion) => {
                this.setState({
                    newDatasetVersion: newDatasetVersion
                });
            }).catch((err: any) => {
                console.log(err);
            });
        });
    }

    retrieveFileStatus(s3Key: string) {
        let updatedFilesStatus = this.state.filesStatus;

        // Get the file who received this progress notification
        let updatedFileStatus = updatedFilesStatus.find((element: FileUploadStatus) => {
            return element.s3Key == s3Key;
        });

        return updatedFileStatus;
    }

    saveFileStatus(fileStatus: FileUploadStatus) {
        let updatedFilesStatus = this.state.filesStatus;

        let oldFileStatus = this.retrieveFileStatus(fileStatus.s3Key);
        oldFileStatus = fileStatus;

        this.setState({
            filesStatus: updatedFilesStatus
        });
    }

    // Async function to wait
    delay(milliseconds: number) {
        return new Promise<void>(resolve => {
            setTimeout(resolve, milliseconds);
        });
    }

    displayStatusUpdate(status: TaskStatus, s3Key: string) {
        let updatedFileStatus = this.retrieveFileStatus(s3Key);

        if (updatedFileStatus) {
            updatedFileStatus.conversionProgress = status.message;
            this.saveFileStatus(updatedFileStatus)
        }
        console.log(status.message);
    }

    initRecurringCheckStatus(taskId: string, s3Key: string) {
        return tapi.get_task_status(taskId).then((new_status: TaskStatus) => {
            return this.checkOrContinue(new_status, s3Key);
        })
    }

    checkOrContinue(status: TaskStatus, s3Key: string): Promise<string> {
        // If status == SUCCESS, return the last check
        // If status != SUCCESS, wait 1 sec and check again
        // TODO: Make an enum from the task state

        if (status.state == 'SUCCESS') {
            this.displayStatusUpdate(status, s3Key);
            console.log("Success of task: " + status.id);
            return Promise.resolve(status.id)
        }
        else if (status.state == 'FAILURE') {
            // TODO: Make an exception class to manage properly the message
            status.message = "FAILURE: " + status.message;
            this.displayStatusUpdate(status, s3Key);
            return Promise.reject<string>(status.message);
        }
        else {
            this.displayStatusUpdate(status, s3Key);
            return tapi.get_task_status(status.id).then((new_status: TaskStatus) => {
                // Wait one sec Async then check again
                // setTimeout(() => {return this.checkOrContinue(status)}, 1000);
                return this.delay(1000).then(() => {
                    return this.checkOrContinue(new_status, s3Key)
                });
            });
        }
    }

    // Form dataset
    handleFormNameChange(event: any) {
        this.setState({nameValue: event.target.value});
    }

    handleFormDescriptionChange(event: any) {
        this.setState({descriptionValue: event.target.value});
    }

    // Bootstrap Table functions
    onAfterDeleteRow(rowKeys: Array<string>) {
        const remaining_filesStatus = this.state.filesStatus.filter((fileStatus) => {
            // We only return the fileStatus that do NOT match any of the rowKeys (file name)0
            return rowKeys.indexOf(fileStatus.file.name) === -1
        });

        this.setState({
            filesStatus: remaining_filesStatus
        })
    }

    fileNameFormatter(cell: any, row: any) {
        return (
            <span title={ cell }>{ cell }</span>
        )
    }

    progressFormatter(cell: any, row: any) {
        return (
            <span>{ cell }%</span>
        );
    }

    conversionProgressFormatter(cell: any, row: any) {
        return (
            <span title={ cell }>{ cell }</span>
        )
    }

    sizeFormatter(cell: any, row: any) {
        let cellFileSize = filesize(cell, {base: 10});
        return (
            <span>{cellFileSize}</span>
        )
    }

    typeFormatter(cell: any, row: any) {
        let formattedType: InitialFileType = getInitialFileTypeFromMimeType(cell);
        return formattedType.toString();
    }

    columnClassProgressFormat(fieldValue: any, row: any, rowIdx: number, colIds: number) {
        if (row instanceof FileUploadStatus && row.progress == 100) {
            return 'progressDownloadComplete';
        }
        else {
            return '';
        }
    }

    columnClassProgressUploadFormat(fieldValue: any, row: any, rowIdx: number, colIds: number) {
        // TODO: This function handles both Upload Progress and Conversion Progress. Should merge into one column, or have two different functions
        if (row instanceof FileUploadStatus && row.conversionProgress == "Done") {
            return 'progressDownloadComplete';
        }
        // TODO: The test of failure should not be done against a string but an object
        else if (row instanceof FileUploadStatus && row.conversionProgress.startsWith("FAILURE")) {
            return 'conversionProgressFailure';
        }
        else {
            return '';
        }
    }

    onPreviousRowSelect(row: any, isSelected: Boolean, e: any): boolean {
        const previousVersionFilesIdsSelected = this.state.previousVersionFilesIdsSelected;
        const clickedId = row['id'];

        let newPreviousVersionFilesIdsSelected = null;
        if (isSelected) {
            newPreviousVersionFilesIdsSelected = update(previousVersionFilesIdsSelected,
                {$push: [clickedId]});
        }
        else {
            let idIndex = previousVersionFilesIdsSelected.indexOf(clickedId);
            newPreviousVersionFilesIdsSelected = update(previousVersionFilesIdsSelected,
                {$splice: [[idIndex, 1]]});
        }
        this.setState({
            previousVersionFilesIdsSelected: newPreviousVersionFilesIdsSelected
        });
        return true;
    }

    requestClose() {
        this.props.cancel();
    }

    render() {
        // TODO: Since the module to have the upload status grows bigger and bigger, think about refactoring it in another file or module
        const filesStatus = this.state.filesStatus;

        const check_mode: SelectRowMode = 'checkbox';
        const selectRowProp = {
            mode: check_mode
        };

        const options = {
            noDataText: 'Nothing uploaded yet',
            afterDeleteRow: (rowKeys: Array<string>) => this.onAfterDeleteRow(rowKeys) // A hook for after droping rows.
        };

        const cellEditProp: CellEdit = {
            mode: 'click'
        };

        const fileTypeWidth = '170';

        const createTypeEditor = (onUpdate: any, props: any) => (
            <TypeEditorBootstrapTable onUpdate={ onUpdate } {...props}/>);

        // FormControl
        // InputName => If populated with readOnlyName, we render a disabled FormControl.
        // Otherwise, we render a regular one
        let inputName = null;
        if (this.props.readOnlyName) {
            inputName = (
                <FormControl value={this.props.readOnlyName}
                             type="text"
                             disabled={true}/>
            );
        }
        else {
            inputName = (
                <FormControl value={this.state.nameValue}
                             onChange={(evt) => {this.handleFormNameChange(evt)}}
                             type="text"
                             placeholder="Dataset name"/>
            );
        }

        // InputDescription => If populated with readOnlyDescription, we render a disabled FormControler.
        // Otherwise, we render a reguler one
        let inputDescription = null;
        if (this.props.readOnlyDescription) {
            inputDescription = (
                <FormControl value={ this.props.readOnlyDescription }
                             componentClass="textarea"
                             disabled={true}/>
            )
        }
        else {
            inputDescription = (
                <FormControl value={this.state.descriptionValue}
                             onChange={(evt) => {this.handleFormDescriptionChange(evt)}}
                             componentClass="textarea"
                             placeholder="Dataset description"/>
            )
        }

        let newDatasetLink = undefined;
        // If we have a new datasetVersion in the state, we can show the link button
        if (!isNullOrUndefined(this.state.newDatasetVersion)) {
            newDatasetLink = (
                <Link className="btn btn-success"
                      role="submit"
                      to={relativePath(
                      "dataset/"+this.state.newDatasetVersion.dataset_id+"/"+this.state.newDatasetVersion.id
                      )}>
                    See my new Dataset
                </Link>
            );
        }

        let uploadButton = (
            <button type="submit" className="btn btn-primary" disabled={this.state.disableUpload}
                    onClick={(e) => {
                        e.preventDefault();
                        this.requestUpload().then(() => {
                            console.log("Ok upload");
                        }).catch((err:any) => {
                            console.log("Error received: "+err);
                        });
                    }}>
                Upload
            </button>
        );

        // Show the uploaded files if we have some, otherwise say we have nothing yet
        // TODO: Use Colum Format to make a button on Remove boolean => http://allenfang.github.io/react-bootstrap-table/example.html#column-format -->
        let uploadedFiles = (
            <div>
                <BootstrapTable data={filesStatus} deleteRow={ true }
                                selectRow={ selectRowProp }
                                options={ options }
                                cellEdit={ cellEditProp }>
                    <TableHeaderColumn isKey
                                       dataField='fileName'
                                       width="150"
                                       dataFormat={ this.fileNameFormatter }>
                        Name
                    </TableHeaderColumn>
                    <TableHeaderColumn dataField='fileType'
                                       width={fileTypeWidth}
                                       dataFormat={ this.typeFormatter }
                                       customEditor={ { getElement: createTypeEditor }}>
                        <Glyphicon glyph="pencil"/> Type (click to edit)
                    </TableHeaderColumn>
                    <TableHeaderColumn dataField='fileSize'
                                       width="150"
                                       editable={ false }
                                       dataFormat={ this.sizeFormatter }>Size</TableHeaderColumn>
                    <TableHeaderColumn dataField='progress'
                                       width="100"
                                       editable={ false }
                                       dataFormat={ this.progressFormatter }
                                       columnClassName={
                                           (fieldValue: any, row: any, rowIdx: any, colIds: any) =>
                                           this.columnClassProgressFormat(fieldValue, row, rowIdx, colIds) }>Progress</TableHeaderColumn>
                    <TableHeaderColumn dataField='conversionProgress'
                                       width="300"
                                       editable={ false }
                                       dataFormat={ this.conversionProgressFormatter }
                                       columnClassName={
                                           (fieldValue: any, row: any, rowIdx: any, colIds: any) =>
                                           this.columnClassProgressUploadFormat(fieldValue, row, rowIdx, colIds) }>Conversion Progress</TableHeaderColumn>
                </BootstrapTable>
            </div>
        );

        const check_previous_mode: SelectRowMode = 'checkbox';
        const selectRowPreviousProp = {
            mode: check_previous_mode,
            clickToSelect: true,
            onSelect: (row: any, isSelected: Boolean, event: any) => this.onPreviousRowSelect(row, isSelected, event)
        };

        let previousFiles = null;
        if (this.props.previousVersionFiles) {
            previousFiles = (
                <div style={rowUploadFiles}>
                    <h3>Select the files you want from the version { this.props.previousVersionName }</h3>
                    <BootstrapTable data={ this.props.previousVersionFiles } selectRow={ selectRowPreviousProp }>
                        <TableHeaderColumn isKey dataField='id' hidden>Id</TableHeaderColumn>
                        <TableHeaderColumn dataField='name'>Name</TableHeaderColumn>
                        <TableHeaderColumn dataField='type'>Type</TableHeaderColumn>
                    </BootstrapTable>
                </div>
            );
        }

        // Modal showing a Dropzone with Cancel and Upload button
        return <Modal
            style={modalStyles}
            closeTimeoutMS={150}
            isOpen={this.props.isVisible}
            contentLabel="Upload">
            <div className="modal-content">
                <div className="modal-header">
                    <h2 ref="subtitle">{ this.props.title }</h2>
                </div>
                <Form horizontal>
                    <div className="modal-body">
                        <div className="dataset-metadata">

                            <FormGroup controlId="formName" validationState={this.state.validationState}>
                                <Col componentClass={ ControlLabel } sm={2}>
                                    Name
                                </Col>
                                <Col sm={10}>
                                    { inputName }
                                </Col>
                                <Col sm={10} smOffset={2}>
                                    { this.state.help && <HelpBlock>{this.state.help}</HelpBlock> }
                                </Col>
                            </FormGroup>
                            <FormGroup controlId="formDescription">
                                <Col componentClass={ControlLabel} sm={2}>
                                    Description
                                </Col>
                                <Col sm={10}>
                                    { inputDescription }
                                </Col>
                            </FormGroup>

                        </div>
                        <Dropzone style={dropZoneStyle} onDrop={(acceptedFiles: any, rejectedFiles: any) =>
                            this.onDrop(acceptedFiles, rejectedFiles)}
                        >
                            <div>Try dropping some files here, or click to select files to upload.</div>
                        </Dropzone>
                        <div style={rowUploadFiles}>
                            {uploadedFiles}
                        </div>
                        { previousFiles }
                    </div>
                    <div className="modal-footer">
                        <button type="button" className="btn btn-default" onClick={(e) => {
                            this.requestClose();
                        }}>
                            Close
                        </button>
                        { !this.state.newDatasetVersion && uploadButton }

                        { this.state.newDatasetVersion && newDatasetLink }
                    </div>
                </Form>
            </div>
        </Modal>
    }
}