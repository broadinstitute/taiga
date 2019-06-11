import * as React from "react";
import update from "immutability-helper";
import * as filesize from "filesize";

// import { FormGroup, ControlLabel, FormControl } from 'react-bootstrap';
// import { InitialFileType } from "../../models/models";
// import { getInitialFileTypeFromMimeType } from "../../utilities/formats";

// interface TypeEditorProps {
//     defaultValue: any;
//     onUpdate: any;
// }

// interface TypeEditorState {
//     type: InitialFileType;
// }

export enum UploadFileType {
    Upload,
    TaigaPath,
    GCSPath
}

export interface UploadFile {
    name: string; // the name of the datafile record in once dataset has been created
    size: string; // desciption of size

    fileType: UploadFileType;

    gcsPath?: string; // If the path to a GCS object

    exitingTaigaId?: string; // the ID of an existing taiga data file.

    uploadFile?: File;
    uploadFormat?: string;
    progress?: number; // between 0 and 1
    progressMessage?: string;
}

interface UploadTableProps {
    files: Array<UploadFile>;
    controller: UploadController;
}

interface UploadTableState {
}

export class UploadController {
    files: Readonly<Array<UploadFile>>;
    listener: (any) => void;

    constructor(listener: (any) => void) {
        this.files = []
        this.listener = listener;
        console.log("constructed");
    }


    getDefaultName(path: string) {
        return "foo";
    }

    addGCS(gcsPath: string, size: number) {
        let name = this.getDefaultName(gcsPath)
        this.addFile({ name: name, fileType: UploadFileType.GCSPath, size: "unknown", gcsPath: gcsPath })
    }

    addUpload(file: File) {
        let name = this.getDefaultName(file.name)
        console.log("file", file);
        this.addFile({ name: name, fileType: UploadFileType.Upload, size: filesize(file.size), uploadFile: file })
    }

    addTaiga(exitingTaigaId: string, size: string) {
        let name = this.getDefaultName(exitingTaigaId)
        this.addFile({ name: name, fileType: UploadFileType.TaigaPath, size: size, exitingTaigaId: exitingTaigaId })
    }

    addFile(file: UploadFile) {
        console.log("files", this.files);
        this.files = update(this.files, { $push: [file] })
        this.listener(this.files)
    }

    onDelete(index: number) {
        this.files = update(this.files, { $splice: [[index, 1]] });
        this.listener(this.files)
    }

    onNameChange(index: number, newName: string) {
        this.files = update(this.files, { [index]: { name: { $set: newName } } })
        this.listener(this.files)
    }
}

export class UploadTable extends React.Component<UploadTableProps, UploadTableState> {
    constructor(props: any) {
        super(props);
    }

    render() {
        let rows = this.props.files.map((file, i) => {
            let name = file.name;
            let source = "";
            let typeLabel = "";
            let progress = "";

            if (file.fileType == UploadFileType.GCSPath) {
                typeLabel = "GCS Object"
                source = file.gcsPath;
            } else if (file.fileType == UploadFileType.TaigaPath) {
                typeLabel = "Taiga file"
                source = file.exitingTaigaId;
            } else if (file.fileType == UploadFileType.Upload) {
                typeLabel = "Upload";
                source = file.uploadFile.name;
            } else {
                throw "unknown filetype";
            }

            return (<tr>
                <td>
                    <input type="text" value={name} onChange={event => this.props.controller.onNameChange(i, event.target.value)} />
                </td>
                <td>
                    {source}
                </td>
                <td>
                    {typeLabel}
                </td>
                <td>
                    {file.size}
                </td>
                <td>
                    {progress}
                </td>
                <td>
                    <button type="button" className="btn btn-default" aria-label="Left Align" onClick={event => this.props.controller.onDelete(i)}>
                        <span className="glyphicon glyphicon-trash" aria-hidden="true"></span>
                    </button>
                </td>
            </tr>);
        });

        return (<table>
            <thead>
                <tr>
                    <th style={{ width: "100px" }} >
                        Name
                    </th>
                    <th>
                        Source
                    </th>
                    <th>
                        Type
                    </th>
                    <th>
                        Size
                    </th>
                    <th>
                        Progress
                    </th>
                    <th>
                        Delete
                    </th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>);
    }
}

