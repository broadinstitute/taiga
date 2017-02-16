"use strict";
var __extends = (this && this.__extends) || function (d, b) {
    for (var p in b) if (b.hasOwnProperty(p)) d[p] = b[p];
    function __() { this.constructor = d; }
    d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
};
var React = require("react");
var Modal = require("react-modal");
var AWS = require("aws-sdk");
var Dropzone = require("react-dropzone");
// TODO: Duplication of modalStyles in Dialogs.tsx => Find a way to fix this
var modalStyles = {
    content: {
        background: null,
        border: null
    }
};
var UploadDataset = (function (_super) {
    __extends(UploadDataset, _super);
    function UploadDataset(props) {
        _super.call(this, props);
        // How can we ensure we are not erasing/forgetting states defined in the interface?
        this.state = {
            files: new Array(),
            disableUpload: true
        };
    }
    UploadDataset.prototype.componentDidMount = function () {
        var tapi = this.context.tapi;
        console.log("UploadDataset: componentDidMount");
    };
    UploadDataset.prototype.onDrop = function (acceptedFiles, rejectedFiles) {
        console.log('Accepted files: ', acceptedFiles);
        this.setState({
            files: acceptedFiles
        });
        this.setState({
            disableUpload: false
        });
    };
    UploadDataset.prototype.requestUpload = function () {
        var _this = this;
        console.log("We are in requestUpload!");
        console.log("Uploading through token:");
        var tapi = this.context.tapi;
        tapi.get_s3_credentials().then(function (credentials) {
            console.log("Received credentials! ");
            console.log("- Access key id: " + credentials.accessKeyId);
            _this.doUpload(credentials, _this.state.files);
        });
    };
    UploadDataset.prototype.doUpload = function (s3_credentials, files) {
        var _this = this;
        var s3 = new AWS.S3({
            apiVersion: '2006-03-01',
            credentials: {
                accessKeyId: s3_credentials.accessKeyId,
                secretAccessKey: s3_credentials.secretAccessKey,
                sessionToken: s3_credentials.sessionToken
            }
        });
        console.log("Uploading now: " + files[0].name);
        var params = {
            Bucket: 'broadtaiga2prototype',
            Key: files[0].name,
            Body: files[0]
        };
        var putObjectPromise = s3.putObject(params).promise();
        putObjectPromise.then(function (data) {
            console.log('Success');
            _this.setState({
                files: new Array(),
                disableUpload: true
            });
        }).catch(function (err) {
            console.log(err);
        });
    };
    UploadDataset.prototype.render = function () {
        var _this = this;
        var files = this.state.files;
        var uploadedFiles = null;
        if (files.length > 0) {
            uploadedFiles = (<div>
                  <h2>Waiting to upload {files.length} files...</h2>
                  <div>{files.map(function (file, index) {
                if (file.type.startsWith("image")) {
                    return <img key={index} src={file.preview}/>;
                }
                else {
                    return <img key={index} src={"/static/taiga3.png"}/>;
                }
            })}</div>
              </div>);
        }
        else {
            uploadedFiles = (<div>Nothing uploaded yet!</div>);
        }
        return <Modal style={modalStyles} closeTimeoutMS={150} isOpen={this.props.isVisible} onRequestClose={this.props.cancel}>
            <div className="modal-content">
            <div className="modal-body">
                <Dropzone onDrop={function (acceptedFiles, rejectedFiles) {
            return _this.onDrop(acceptedFiles, rejectedFiles);
        }}>
                    <div>Try dropping some files here, or click to select files to upload.</div>
                </Dropzone>

                {uploadedFiles}
            </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-default" onClick={this.props.cancel}>Close</button>
              <button type="button" className="btn btn-primary" disabled={this.state.disableUpload} onClick={function () { return _this.requestUpload(); }}>Upload</button>
            </div>
          </div>
        </Modal>;
    };
    UploadDataset.contextTypes = {
        tapi: React.PropTypes.object
    };
    return UploadDataset;
}(React.Component));
exports.UploadDataset = UploadDataset;
