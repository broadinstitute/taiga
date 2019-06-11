import * as React from "react";
import { Form, FormControl, Col, ControlLabel, FormGroup, Grid, Row, Glyphicon, HelpBlock } from 'react-bootstrap';
import * as Dropzone from "react-dropzone";

import update from "immutability-helper";
import { UploadTable, UploadFile, UploadController } from "./UploadTable";

interface UploadFormProps {

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
        let help = "help";

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

