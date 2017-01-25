import * as React from "react";
import * as Modal from "react-modal";

import * as AWS from "aws-sdk";
import * as Dropzone from "react-dropzone";
import * as filesize from "filesize";
import {BootstrapTable, TableHeaderColumn, SelectRowMode} from "react-bootstrap-table";
import { Form, FormControl, Col, ControlLabel, FormGroup, Grid, Row } from 'react-bootstrap';

import { DialogProps, DialogState } from "../Dialogs";
import {S3Credentials, FileUploadStatus, TaskStatus} from "../../models/models";
import { TaigaApi } from "../../models/api";


interface DropzoneProps extends DialogProps {
    onFileUploadedAndConverted?: any;
    currentFolderId: string;
}

interface DropzoneState extends DialogState {
    filesStatus?: Array<FileUploadStatus>;
    disableUpload?: boolean;
    datasetFormDisabled?: boolean;
    nameValue?: string;
    descriptionValue?: string;
}

// TODO: Duplication of modalStyles in Dialogs.tsx => Find a way to fix this
const modalStyles : any = {
  content : {
    background: null,
    border: null
  }
};

const dropZoneStyle: any = {
    height: '200px',
    borderWidth: '2px',
    borderColor: 'rgb(102, 102, 102)',
    borderStyle: 'dashed',
    borderRadius: '5px'
};

const rowUploadFiles: any = {
    paddingTop: '15px'
};

const dropzoneStyles: any = "width: 100%; height: 200px; border-width: 2px; border-color: #666; border-style: dashed; border-radius: 5px;"

export class UploadDataset extends React.Component<DropzoneProps, DropzoneState>{
    static contextTypes = {
        tapi: React.PropTypes.object
    };

    constructor(props: any){
        super(props);
        // TODO: How can we ensure we are not erasing/forgetting states defined in the interface?
        this.state = {
            filesStatus: new Array<FileUploadStatus>(),
            disableUpload: true,
            datasetFormDisabled: false,
            nameValue: '',
            descriptionValue: ''
        }
    }

    componentDidMount() {
        let tapi: TaigaApi = (this.context as any).tapi;

        console.log("UploadDataset: componentDidMount");
    }

    // When files are put in the drop zone
    onDrop(acceptedFiles: Array<File>, rejectedFiles: Array<File>) {
        console.log('Accepted files: ', acceptedFiles);

        // We construct the FileStatusUpload object for each accepted files
        let filesUploadStatus = acceptedFiles.map((file) => {
            return new FileUploadStatus(file);
        });
        console.log('Files upload status: ', filesUploadStatus);

        this.setState({
            filesStatus: filesUploadStatus
        });
        this.setState({
            disableUpload: false,
            datasetFormDisabled: false
        });
    }

    // Ask the credentials to be able to upload
    requestUpload(){
        // TODO: Use the form features to check the data
        console.log("We are in requestUpload!");
        console.log("Uploading through token:");

        let tapi: TaigaApi = (this.context as any).tapi;

        tapi.get_s3_credentials().then((credentials) => {
            console.log("Received credentials! ");
            console.log("- Access key id: " + credentials.accessKeyId);

            // Request creation of Upload session => sid
            let tapi: TaigaApi = (this.context as any).tapi;
            return tapi.get_new_upload_session().then((sid: string) => {
                console.log("New upload session received: "+sid);
                // doUpload with this sid
                this.doUpload(credentials, this.state.filesStatus, sid);
            });
        });
    }

    // Use the credentials received to upload the files dropped in the module
    doUpload(s3_credentials: S3Credentials, filesStatus: Array<FileUploadStatus>, sid: string){
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
        let promises_fileUpload: Array<Promise<string>> = filesStatus.map((file: FileUploadStatus) =>
            {
                console.log("Uploading now: " + file.fileName);

                // TODO: Configure this elsewhere as a const configuration (settings.cfg?)
                let params = {
                    Bucket: 'broadtaiga2prototype',
                    Key: file.fileName,
                    Body: file.file
                };

                let upload = new AWS.S3.ManagedUpload({
                    params: params,
                    service: s3
                });

                // Subscribe to measure progress
                upload.on('httpUploadProgress', (evt) => {
                    // TODO: evt.key is not recognized in the DefinitelyType AWS, but it works. Raise an issue in Git
                    console.log('Progress:', evt.loaded, '/', evt.total, 'of ', evt.key);

                    let updatedFilesStatus = this.state.filesStatus;

                    // Get the file who received this progress notification
                    let updatedFileStatus = updatedFilesStatus.find((element: FileUploadStatus) => {
                        return element.fileName == evt.key;
                    });

                    let progressPercentage = Math.floor(evt.loaded/evt.total * 100);
                    updatedFileStatus.progress = progressPercentage;

                    this.setState({
                        filesStatus: updatedFilesStatus,
                        disableUpload: true,
                        datasetFormDisabled: true
                    });
                });

                // Create an upload promise via the aws sdk and launch it
                let uploadPromise = upload.promise();
                // TODO: Manage all the errors that can come along the way
                return uploadPromise.then((data: any) => {
                    console.log('Success uploading to S3. Data received: '+data);
                    console.log('Here is the url of the file: '+data.Location);
                    console.log('Here is the Key of the file: '+data.ETag);
                    // TODO: Send the signal the upload is done on the AWS side, so you can begin the conversion on the backend
                    // POST
                    let tapi: TaigaApi = (this.context as any).tapi;
                    return tapi.process_new_datafile(data.Location, data.ETag,
                                                data.Bucket, data.Key, sid
                    ).then((taskStatusId) => {
                        console.log("The new datafile " +  data.Key + " has been sent!");
                        console.log("We now check the task until we receive success");
                        return tapi.get_task_status(taskStatusId);
                    }).then((status) => {
                        console.log("Received the first status: "+status.state);
                        return this.checkOrContinue(status);
                    }).then(() => {
                        console.log("Task finished!");
                        // Get the file who received this progress notification
                        let updatedFileStatus = this.retrieveFileStatus(data.Key);
                        updatedFileStatus.conversionProgress = "Done";
                        this.saveFileStatus(updatedFileStatus);

                        return Promise.resolve(sid)
                    })
                }).catch((err: any) => {
                    console.log(err);
                    this.setState({
                        disableUpload: false,
                        datasetFormDisabled: false
                    });
                    return Promise.reject(err);
                });
            });
        // Then we create the dataset if all have been resolved
        Promise.all(promises_fileUpload).then((sids) => {
            // TODO: Check all sids are the same
            console.log("All datafiles have been uploaded and converted successfully!");
            console.log("Asking to create a dataset from session id "+sid[0]);
            let tapi: TaigaApi = (this.context as any).tapi;
            return tapi.create_dataset(sids[0].toString(),
                this.state.nameValue,
                this.state.descriptionValue,
                this.props.currentFolderId.toString());
        }).then((dataset_id) => {
            console.log("Dataset "+dataset_id+" has been created!");
        }).catch((err: any) => {
           console.log(err);
        });
    }

    retrieveFileStatus(fileName: string){
        let updatedFilesStatus = this.state.filesStatus;

        // Get the file who received this progress notification
        let updatedFileStatus = updatedFilesStatus.find((element: FileUploadStatus) => {
            return element.fileName == fileName;
        });

        return updatedFileStatus;
    }

    saveFileStatus(fileStatus: FileUploadStatus){
        let updatedFilesStatus = this.state.filesStatus;

        let oldFileStatus = this.retrieveFileStatus(fileStatus.fileName);
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

    checkOrContinue(status: TaskStatus) {
        // If status == SUCCESS, return the last check
        // If status != SUCCESS, wait 1 sec and check again
        // TODO: Make an enum from the task state
        let updatedFilesStatus = this.state.filesStatus;

        console.log('The name of the file we are processing is: '+status.fileName);

        // Get the file who received this progress notification
        let updatedFileStatus = updatedFilesStatus.find((element: FileUploadStatus) => {
            return element.fileName == status.fileName;
        });

        if (updatedFileStatus) {
            updatedFileStatus.conversionProgress = status.message;
            console.log("We just updated "+updatedFileStatus.fileName+" with this message '"+ updatedFileStatus.conversionProgress+"'");
            this.setState({
                filesStatus: updatedFilesStatus,
                disableUpload: true
            });
        }
        console.log(status.message);

        if(status.state == 'SUCCESS') {
            console.log("Success of task: " + status.id);
            return Promise.resolve(status.id)
        }
        else if(status.state == 'FAILURE') {
            return Promise.reject('Failure of task ' + status.id);
        }
        else {
            let tapi: TaigaApi = (this.context as any).tapi;
            return tapi.get_task_status(status.id).then((new_status: TaskStatus) => {
                // Wait one sec Async then check again
                // setTimeout(() => {return this.checkOrContinue(status)}, 1000);
                return this.delay(1000).then(() => {
                   return this.checkOrContinue(new_status)
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
    onAfterDeleteRow(rowKeys : Array<string>) {
        const remaining_filesStatus = this.state.filesStatus.filter((fileStatus) => {
            // We only return the fileStatus that do NOT match any of the rowKeys (file name)0
            return rowKeys.indexOf(fileStatus.file.name) === -1
        });

        this.setState({
            filesStatus: remaining_filesStatus
        })
    }

    progressFormatter(cell: any, row: any) {
        return (
          <span>{cell}%</span>
        );
    }

    sizeFormatter(cell: any, row: any) {
        let cellFileSize = filesize(cell, {base: 10});
        return (
            <span>{cellFileSize}</span>
        )
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
        if (row instanceof FileUploadStatus && row.conversionProgress == "Done") {
            return 'progressDownloadComplete';
        }
        else {
            return '';
        }
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

        // Show the uploaded files if we have some, otherwise say we have nothing yet
        // TODO: Use Colum Format to make a button on Remove boolean => http://allenfang.github.io/react-bootstrap-table/example.html#column-format -->
        let uploadedFiles = (
            <div>
                <BootstrapTable data={filesStatus} deleteRow={ true }
                                selectRow={ selectRowProp }
                                options={ options }>
                    <TableHeaderColumn isKey dataField='fileName'>Name</TableHeaderColumn>
                    <TableHeaderColumn dataField='fileType'>Type</TableHeaderColumn>
                    <TableHeaderColumn dataField='fileSize'
                                       dataFormat={ this.sizeFormatter }>Size</TableHeaderColumn>
                    <TableHeaderColumn dataField='progress'
                                       dataFormat={ this.progressFormatter }
                                       columnClassName={
                                           (fieldValue: any, row: any, rowIdx: any, colIds: any) =>
                                           this.columnClassProgressFormat(fieldValue, row, rowIdx, colIds) }>Progress</TableHeaderColumn>
                    <TableHeaderColumn dataField='conversionProgress'
                                       columnClassName={
                                           (fieldValue: any, row: any, rowIdx: any, colIds: any) =>
                                           this.columnClassProgressUploadFormat(fieldValue, row, rowIdx, colIds) }>Conversion Progress</TableHeaderColumn>
                </BootstrapTable>
            </div>
        );

        // Modal showing a Dropzone with Cancel and Upload button
        return <Modal
            style={modalStyles}
            closeTimeoutMS={150}
            isOpen={this.props.isVisible}
            onRequestClose={this.props.cancel}
            contentLabel="Upload">
            <div className="modal-content">
                <div className="modal-header">
                    <h2 ref="subtitle">New dataset</h2>
                </div>
                <div className="modal-body">
                    <Grid>
                        <Row>
                            <Col>
                                <div className="dataset-metadata">
                                    <Form horizontal>
                                        <FormGroup controlId="formName">
                                            <Col componentClass={ControlLabel} sm={2}>
                                                Name
                                            </Col>
                                            <Col sm={10}>
                                                <FormControl value={this.state.nameValue}
                                                             onChange={(evt) => {this.handleFormNameChange(evt)}}
                                                             type="text"
                                                             placeholder="Dataset name"/>
                                            </Col>
                                        </FormGroup>
                                        <FormGroup controlId="formDescription">
                                            <Col componentClass={ControlLabel} sm={2}>
                                                Description
                                            </Col>
                                            <Col sm={10}>
                                                <FormControl value={this.state.descriptionValue}
                                                             onChange={(evt) => {this.handleFormDescriptionChange(evt)}}
                                                             type="textarea"
                                                             placeholder="Dataset description"/>
                                            </Col>
                                        </FormGroup>
                                    </Form>
                                </div>
                            </Col>
                        </Row>
                        <Row>
                            <Col>
                                <Dropzone style={dropZoneStyle} onDrop={(acceptedFiles: any, rejectedFiles: any) =>
                                        this.onDrop(acceptedFiles, rejectedFiles)}
                                >
                                    <div>Try dropping some files here, or click to select files to upload.</div>
                                </Dropzone>
                            </Col>
                        </Row>
                        <Row style={rowUploadFiles}>
                            <Col>
                                {uploadedFiles}
                            </Col>
                        </Row>
                    </Grid>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-default" onClick={this.props.cancel}>Close</button>
                  <button type="button" className="btn btn-primary" disabled={this.state.disableUpload} onClick={() => this.requestUpload()}>Upload</button>
                </div>
            </div>
        </Modal>
    }
}