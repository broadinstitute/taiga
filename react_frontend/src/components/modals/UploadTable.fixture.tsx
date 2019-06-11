import { UploadTable, UploadFileType, UploadController } from "./UploadTable"
import { UploadForm } from "./UploadForm"
import * as React from "react";
import * as Dropzone from "react-dropzone";

let files = [
    { name: "taigafile", fileType: UploadFileType.TaigaPath, size: "100", existingTaigaId: "original-123183.2/sample" }
];

//let w = window as any;
//w.update_hack = update;

const dropZoneStyle: any = {
    height: '150px',
    borderWidth: '2px',
    borderColor: 'rgb(102, 102, 102)',
    borderStyle: 'dashed',
    borderRadius: '5px'
};

export class UploadTableWrapper extends React.Component<any, any> {
    controller: UploadController

    constructor(props: any) {
        super(props);
        this.state = { files: props.initialFiles }

        this.controller = new UploadController((files: any) => this.setState({ files: files }));
        this.controller.files = props.initialFiles;
    }

    onDrop(acceptedFiles: Array<File>, rejectedFiles: Array<File>) {
        console.log(acceptedFiles)
        acceptedFiles.forEach((file) => this.controller.addUpload(file))
    }

    render() {
        return (<div>
            <button onClick={(event) => this.controller.addGCS("gs://bucket/key/c.txt", 100000)}>Add GCS object</button>
            <button onClick={(event) => this.controller.addTaiga("something-taiga-1231cae.2/filename", "200x30")}>Add Taiga</button>
            <Dropzone style={dropZoneStyle} onDrop={(acceptedFiles: any, rejectedFiles: any) =>
                this.onDrop(acceptedFiles, rejectedFiles)}
            />

            <UploadTable controller={this.controller} files={this.state.files} />
        </div>)
    }
}

export default [
    {
        component: UploadTableWrapper,
        name: "simple",
        props: {
            initialFiles: files
        },
    },
    {
        component: UploadForm,
        name: "stuff",
        props: {

        }
    }
]