import * as React from "react";
import * as Modal from "react-modal";

import * as AWS from "aws-sdk";
import * as Dropzone from "react-dropzone";
import { BootstrapTable, TableHeaderColumn } from "react-bootstrap-table";

import { DialogProps, DialogState } from "../Dialogs";
import {S3Credentials, FileUploadStatus} from "../../models/models";
import { TaigaApi } from "../../models/api";


interface DropzoneProps extends DialogProps {

}

interface DropzoneState extends DialogState {
    filesStatus?: Array<FileUploadStatus>;
    disableUpload?: boolean;
}

// TODO: Duplication of modalStyles in Dialogs.tsx => Find a way to fix this
const modalStyles : any = {
  content : {
    background: null,
    border: null
  }
};

export class UploadDataset extends React.Component<DropzoneProps, DropzoneState>{
    static contextTypes = {
        tapi: React.PropTypes.object
    };

    constructor(props: any){
        super(props);
        // TODO: How can we ensure we are not erasing/forgetting states defined in the interface?
        this.state = {
            filesStatus: new Array<FileUploadStatus>(),
            disableUpload: true
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
            disableUpload: false
        });
    }

    // Ask the credentials to be able to upload
    requestUpload(){
        console.log("We are in requestUpload!");
        console.log("Uploading through token:");

        let tapi: TaigaApi = (this.context as any).tapi;

        tapi.get_s3_credentials().then((credentials) => {
            console.log("Received credentials! ");
            console.log("- Access key id: " + credentials.accessKeyId);
            this.doUpload(credentials, this.state.filesStatus);
        });
    }

    // Use the credentials received to upload the files dropped in the module
    doUpload(s3_credentials: S3Credentials, filesStatus: Array<FileUploadStatus>){
        // TODO: For now, we only upload the first file. But next commits will manage all of them
        let file = filesStatus[0].file;

        // Configure the AWS S3 object with the received credentials
        let s3 = new AWS.S3({
            apiVersion: '2006-03-01',
            credentials: {
                accessKeyId: s3_credentials.accessKeyId,
                secretAccessKey: s3_credentials.secretAccessKey,
                sessionToken: s3_credentials.sessionToken
            }
        });

        console.log("Uploading now: " + file.name);

        // TODO: Configure this elsewhere as a const configuration (settings.cfg?)
        let params = {
            Bucket: 'broadtaiga2prototype',
            Key: file.name,
            Body: file
        };

        let upload = new AWS.S3.ManagedUpload({
            params: params,
            service: s3
        });

        // Measure progress
        upload.on('httpUploadProgress', (evt) => {
            console.log('Progress:', evt.loaded, '/', evt.total);
            let updatedFilesStatus = this.state.filesStatus;

            let progressPercentage = Math.floor(evt.loaded/evt.total * 100);
            updatedFilesStatus[0].progress = progressPercentage;

            this.setState({
                filesStatus: updatedFilesStatus,
                disableUpload: true
            });
        });

        // Create an upload promise via the aws sdk and launch it
        let uploadPromise = upload.promise();
        uploadPromise.then((data: any) => {
            console.log('Success. Data received: '+data);
            // TODO: Change this to take into account all the submitted files
            let updatedFilesStatus = this.state.filesStatus;
            updatedFilesStatus[0].progress = 100;
            this.setState({
                filesStatus: updatedFilesStatus
            })
        }).catch((err: any) => {
            console.log(err);
            this.setState({
                disableUpload: false
            })
        });

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


    render() {
        // TODO: Since the module to have the upload status grows bigger and bigger, think about refactoring it in another file or module
        var uploadedFiles: any = null;

        const filesStatus = this.state.filesStatus;

        const selectRowProp = {
            mode: 'checkbox'
        };

        const options = {
            noDataText: 'Nothing uploaded yet',
            afterDeleteRow: (rowKeys: Array<string>) => this.onAfterDeleteRow(rowKeys) // A hook for after droping rows.
        };

        // Show the uploaded files if we have some, otherwise say we have nothing yet
        // TODO: Use Colum Format to make a button on Remove boolean => http://allenfang.github.io/react-bootstrap-table/example.html#column-format -->
        uploadedFiles = (
            <div>
                <BootstrapTable data={filesStatus} deleteRow={ true }
                                selectRow={ selectRowProp }
                                striped hover options={ options }>
                    <TableHeaderColumn isKey dataField='fileName'>Name</TableHeaderColumn>
                    <TableHeaderColumn dataField='fileType'>Type</TableHeaderColumn>
                    <TableHeaderColumn dataField='fileSize'>Size</TableHeaderColumn>
                    <TableHeaderColumn dataField='progress' dataFormat={ this.progressFormatter }>Progress</TableHeaderColumn>
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
            <div className="modal-body">
                <Dropzone onDrop={(acceptedFiles: any, rejectedFiles: any) =>
                        this.onDrop(acceptedFiles, rejectedFiles)}>
                    <div>Try dropping some files here, or click to select files to upload.</div>
                </Dropzone>

                {uploadedFiles}
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-default" onClick={this.props.cancel}>Close</button>
              <button type="button" className="btn btn-primary" disabled={this.state.disableUpload} onClick={() => this.requestUpload()}>Upload</button>
            </div>
          </div>
        </Modal>
    }
}