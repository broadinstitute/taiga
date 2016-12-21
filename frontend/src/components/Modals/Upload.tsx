import * as React from "react";
import * as Modal from "react-modal";

import * as AWS from "aws-sdk";
import * as Dropzone from "react-dropzone";

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
        // How can we ensure we are not erasing/forgetting states defined in the interface?
        this.state = {
            files: new Array<any>(),
            disableUpload: true
        }
    }

    componentDidMount() {
        let tapi: TaigaApi = (this.context as any).tapi;

        console.log("UploadDataset: componentDidMount");
    }

    onDrop(acceptedFiles: Array<any>, rejectedFiles: Array<any>) {
        console.log('Accepted files: ', acceptedFiles);
        this.setState({
            files: acceptedFiles
        });
        this.setState({
            disableUpload: false
        });
    }

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

    doUpload(s3_credentials: S3Credentials, files: any){
        let s3 = new AWS.S3({
            apiVersion: '2006-03-01',
            credentials: {
                accessKeyId: s3_credentials.accessKeyId,
                secretAccessKey: s3_credentials.secretAccessKey,
                sessionToken: s3_credentials.sessionToken
            }
        });

        console.log("Uploading now: " + files[0].name);

        let params = {
            Bucket: 'broadtaiga2prototype',
            Key: files[0].name,
            Body: files[0]
        };

        let putObjectPromise = s3.putObject(params).promise();
        putObjectPromise.then((data: any) => {
            console.log('Success');
            this.setState({
                files: new Array<any>(),
                disableUpload: true
            })
        }).catch((err: any) => {
            console.log(err);
        });

    }

    render() {
        const files = this.state.files;

        var uploadedFiles: any = null;
        if (files.length > 0){
            uploadedFiles = (
              <div>
                  <h2>Waiting to upload {files.length} files...</h2>
                  <div>{
                    files.map((file, index) => {
                      if(file.type.startsWith("image")){
                          return <img key={index} src={file.preview}/>
                      }
                      else{
                          return <img key={index} src={"/static/taiga3.png"}/>
                      }
                    })
                  }</div>
              </div>
            );
        }
        else {
            uploadedFiles = (
                <div>Nothing uploaded yet!</div>
            );
        }

        return <Modal
            style={modalStyles}
            closeTimeoutMS={150}
            isOpen={this.props.isVisible}
            onRequestClose={this.props.cancel}>
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