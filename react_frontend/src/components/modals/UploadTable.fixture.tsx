import { UploadTable, UploadFileType, UploadController } from "./UploadTable"
import { CreateVersionDialog } from "./UploadForm"
import * as React from "react";
import * as Dropzone from "react-dropzone";
import { DataFileType } from "../../models/models";

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

        this.controller = new UploadController(props.intialFiles, (files: any) => this.setState({ files: files }));
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

// onFileUploadedAndConverted?: any;

// title: string;
// readOnlyName?: string;
// readOnlyDescription?: string;

// // Determines what is done when opening the modal/componentWillReceiveProps
// onOpen?: Function;
// // Parent gives the previous version files. If it exists, we display another Table
// previousVersionFiles?: Array<DatasetVersionDatafiles>;
// // Parent can give the previous version name. Need it if pass previousVersionFiles
// // TODO: Only pass the previousVersion, so we can take the previous DataFiles from it too
// previousVersionName?: string;
// datasetPermaname?: string;
// previousVersionNumber?: string;

// // If we want to change the description, we can use this to pass the previous description
// // It can't be compatible with readOnlyDescription
// previousDescription?: string;

// validationState?: string;
// help?: string;

// id: string;
// name: string;
// underlying_file_id: string;
// url: string;
// type: DataFileType;
// allowed_conversion_type: Array<string>;
// short_summary: string;
// provenance_nodes?: Array<ProvenanceNode>; // Array of urls to provenance graph



export default [
    {
        component: CreateVersionDialog,
        name: "dialog",
        props: {
            isVisible: true,
            onFileUploadedAndConverted: (sid: string, name: string, description: string, previousDatafileIds: Array<string>) => {
                console.log("onFileUploadedAndConverted")
            },
            previousDescription: "prev Description",
            previousVersionNumber: "100",
            previousVersionFiles: [
                {
                    id: "id",
                    name: "samplename",
                    allowed_conversion_type: ["raw"],
                    short_summary: "200x20",
                    type: DataFileType.Raw
                }
            ],
            datasetPermaname: "permaname-1000"
        },
    }
]