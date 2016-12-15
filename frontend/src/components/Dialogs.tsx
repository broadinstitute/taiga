import * as React from "react";
import * as Modal from "react-modal";
import * as Showdown from "showdown";

import * as Dropzone from "react-dropzone";

import * as AWS from "aws-sdk";


import { TaigaApi } from "../models/api";

import { SignedS3Post } from "../models/models";

interface EditStringProps {
    isVisible : boolean;
    initialValue : string;
    cancel: () => void;
    save: (name: string) => void;
}

interface DialogProps {
    isVisible: boolean;
    cancel: () => void;
}

interface DialogState {
}

interface DropzoneProps extends DialogProps {

}

interface DropzoneState extends DialogState {
    files?: Array<any>;
    allowUpload?: boolean;
}

const modalStyles : any = {
  content : {
    background: null,
    border: null
  }
};

export class EditName extends React.Component<EditStringProps, any> {
    textInput : any;

    render() {
        //className="Modal__Bootstrap modal-dialog"
        return <Modal 
          style={ modalStyles }
          closeTimeoutMS={150}
          isOpen={this.props.isVisible}
          onRequestClose={this.props.cancel}>
          <form>
          <div className="modal-content">
            <div className="modal-body">
                <div className="form-group">
                    <label htmlFor="nameInput">Name</label>
                    <input type="text" defaultValue={this.props.initialValue} className="form-control" id="nameInput" ref={ (c) => {this.textInput = c}  }/>
                </div>
              </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-default" onClick={this.props.cancel}>Close</button>
              <button type="button" className="btn btn-primary" onClick={ () => { this.props.save(this.textInput.value) } }>Save changes</button>
            </div>
          </div>
                </form>
        </Modal>
    }
}


export class EditDescription extends React.Component<EditStringProps, any> {
    textArea : any;

    render() {
        //className="Modal__Bootstrap modal-dialog"
        return <Modal 
          style={ modalStyles }
          closeTimeoutMS={150}
          isOpen={this.props.isVisible}
          onRequestClose={this.props.cancel}>
        <form>
          <div className="modal-content">
            <div className="modal-body">
                <div className="form-group">
                    <label htmlFor="descriptionInput">Description</label>
                    <textarea rows={15}  defaultValue={this.props.initialValue} className="form-control" id="descriptionInput" ref={ (c) => {this.textArea = c}  }></textarea>
                </div>
              </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-default" onClick={this.props.cancel}>Close</button>
              <button type="button" className="btn btn-primary" onClick={() => { this.props.save(this.textArea.value) } }>Save changes</button>
            </div>
          </div>
        </form>
        </Modal>
    }
}

export class UploadDataset extends React.Component<DropzoneProps, DropzoneState>{
    static contextTypes = {
        tapi: React.PropTypes.object
    };

    constructor(props: any){
        super(props);
        // How can we ensure we are not erasing/forgetting states defined in the interface?
        this.state = {
            files: new Array<any>(),
            allowUpload: false
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
    }

    requestUpload(){
        console.log("We are in requestUpload!");
        console.log("Uploading through token:");

        // let creds: AWS.Credentials;

        // creds = new AWS.Credentials("bla", "bla");

        let s3 = new AWS.S3({
            apiVersion: '2006-03-01',
            credentials: {
                accessKeyId: "AKIAIRDC67MDYNGUJ6PQ",
                secretAccessKey: "YXADSEN263CYB+5DTjH6Hw6fgvHQfRV/N/nxKxzI"
            }});

        let params = {
            Bucket: 'broadtaiga2prototype',
            Key: 'example2.txt',
            Body: 'Uploaded text using the promise-based method!'
        };

        var putObjectPromise = s3.putObject(params).promise();
        putObjectPromise.then( (data: any) => {
            console.log('Success');
        }).catch((err: any) => {
            console.log(err);
        });


/*
        let creds = new AWS.Credentials({
            accessKeyId: "AKIAIRDC67MDYNGUJ6PQ",
            secretAccessKey: "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"
        });

        AWS.config.update({region: 'us-west-1', credentials: {
            accessKeyId: "AKIAIRDC67MDYNGUJ6PQ",
            secretAccessKey: "YXADSEN263CYB+5DTjH6Hw6fgvHQfRV/N/nxKxzI"
        }});

        let s3 = new AWS.S3();

        var params = {
            Bucket: 'bucket',
            Key: 'example1.txt',
            Body: 'Uploaded text using the simplified callback method!'
        };

        s3.putObject(params, function (err, data) {
            if (err) {
                console.log(err);
            } else {
                console.log('Success');
            }
        });

*/

        /*
        let tapi : TaigaApi = (this.context as any).tapi;

        tapi.get_signed_s3().then((signedS3Post) => {
            console.log("Done! SignedS3Post: " + signedS3Post);
            console.log("Signed object url: " + signedS3Post.url);
            console.log("Signed object fields: " + signedS3Post.fields);
            console.log("Signed object field policy: " + signedS3Post.fields.policy);
            this.setState({
                allowUpload: true,
            });
            this.doUpload(signedS3Post, this.state.files);
        });
        */
    }

    doUpload(signedS3Post: SignedS3Post, files: any){
        let tapi : TaigaApi = (this.context as any).tapi;
        console.log("We are uploading!!");
        // TODO: Handle multiple files at the same time

        tapi._post_upload<SignedS3Post>(signedS3Post.url, this.state.files[0])
            .then(() => console.log("Finished uploading?"));
    }

    render() {
        const files = this.state.files;

        var uploadedFiles: any = null;
        if (files.length > 0){
            uploadedFiles = (
              <div>
                  <h2>Uploading {files.length} files...</h2>
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
              <button type="button" className="btn btn-primary" disabled={this.state.allowUpload} onClick={() => this.requestUpload()}>Upload</button>
            </div>
          </div>
        </Modal>
    }
}


let converter = new Showdown.Converter()

export function renderDescription(description :string) {
    let description_section : any = null;

    if(description) {
        let desc_as_html = {__html: converter.makeHtml(description)};
        description_section = <div className="well well-sm" dangerouslySetInnerHTML={desc_as_html} />
    }

    return description_section;
}
