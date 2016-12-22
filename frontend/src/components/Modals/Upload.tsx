import * as React from "react";
import * as Modal from "react-modal";

import * as AWS from "aws-sdk";
import * as Dropzone from "react-dropzone";
import { BootstrapTable, TableHeaderColumn } from "react-bootstrap-table";

import { DialogProps, DialogState } from "../Dialogs";
import { S3Credentials } from "../../models/models";
import { TaigaApi } from "../../models/api";


interface DropzoneProps extends DialogProps {

}

interface DropzoneState extends DialogState {
    files?: Array<any>;
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
            files: new Array<File>(),
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
        this.setState({
            files: acceptedFiles
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
            this.doUpload(credentials, this.state.files);
        });
    }

    // Use the credentials received to upload the files dropped in the module
    doUpload(s3_credentials: S3Credentials, files: Array<File>){
        // Configure the AWS S3 object with the received credentials
        let s3 = new AWS.S3({
            apiVersion: '2006-03-01',
            credentials: {
                accessKeyId: s3_credentials.accessKeyId,
                secretAccessKey: s3_credentials.secretAccessKey,
                sessionToken: s3_credentials.sessionToken
            }
        });

        console.log("Uploading now: " + files[0].name);

        // TODO: Configure this elsewhere as a const configuration (settings.cfg?)
        let params = {
            Bucket: 'broadtaiga2prototype',
            Key: files[0].name,
            Body: files[0]
        };

        // Create an upload promise via the aws sdk and launch it
        let putObjectPromise = s3.putObject(params).promise();
        putObjectPromise.then((data: any) => {
            console.log('Success. Data received: '+data);
            this.setState({
                files: new Array<File>(),
                disableUpload: true
            })
        }).catch((err: any) => {
            console.log(err);
        });

    }

    render() {
        const files = this.state.files;

        var uploadedFiles: any = null;

        // Show the uploaded files if we have some, otherwise say we have nothing yet
        uploadedFiles = (
            <div>
                <BootstrapTable data={files} striped hover options={ { noDataText: 'Nothing uploaded yet' } }>
                    <TableHeaderColumn isKey dataField='name'>Name</TableHeaderColumn>
                    <TableHeaderColumn dataField='type'>Type</TableHeaderColumn>
                    <TableHeaderColumn dataField='size'>Size</TableHeaderColumn>
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