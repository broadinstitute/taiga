import * as React from "react";
import update from "immutability-helper";
import * as filesize from "filesize";
import { Form } from "react-bootstrap"
import { InitialFileType } from "../../models/models";
import { UploadFileType } from "../UploadTracker";

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


export interface UploadFile {
    name: string; // the name of the datafile record in once dataset has been created
    size: string; // desciption of size

    computeNameFromTaigaId: boolean;

    fileType: UploadFileType;

    gcsPath?: string; // If the path to a GCS object

    existingTaigaId?: string; // the ID of an existing taiga data file.

    uploadFile?: File;
    uploadFormat?: InitialFileType;

    progress?: number; // between 0 and 100
    progressMessage?: string;
}

interface UploadTableProps {
    isProcessing: boolean;
    files: Array<UploadFile>;
    controller: UploadController;
}

interface UploadTableState {
}

export class UploadController {
    files: Readonly<Array<UploadFile>>;
    listener: (x: any) => void;

    constructor(files: Readonly<Array<UploadFile>>, listener: (x: any) => void) {
        this.files = files
        this.listener = listener;
        console.log("constructed");
    }

    getDefaultName(path: string) {
        let lastSlash = path.lastIndexOf("/");
        if (lastSlash >= 0) {
            path = path.substring(lastSlash + 1);
        }

        let lastDot = path.lastIndexOf(".");
        if (lastDot >= 0) {
            path = path.substring(0, lastDot);
        }

        return path;
    }

    addGCS(gcsPath: string) {
        let name = this.getDefaultName(gcsPath);
        this.addFile({
            name: name,
            computeNameFromTaigaId: false,
            fileType: UploadFileType.GCSPath,
            size: "unknown",
            gcsPath: gcsPath
        });
    }

    addUpload(file: File) {
        let name = this.getDefaultName(file.name)
        this.addFile({ name: name, computeNameFromTaigaId: false, fileType: UploadFileType.Upload, size: filesize(file.size), uploadFile: file, uploadFormat: InitialFileType.Raw })
    }

    addTaiga(existingTaigaId: string, size: string) {
        let name = this.getDefaultName(existingTaigaId)
        this.addFile({ name: name, computeNameFromTaigaId: true, fileType: UploadFileType.TaigaPath, size: size, existingTaigaId: existingTaigaId })
    }

    addFile(file: UploadFile) {
        this.files = update(this.files, { $push: [file] })
        this.listener(this.files)
    }

    changeUploadFormat(index: number, format: string) {
        console.log("changeUploadFormat", index, format);
        this.files = update(this.files, { [index]: { uploadFormat: { $set: format } } });
        this.listener(this.files);
    }

    onDelete(index: number) {
        this.files = update(this.files, { $splice: [[index, 1]] });
        this.listener(this.files);
    }

    onTaigaIdChange(index: number, newValue: string) {
        let changes = { existingTaigaId: { $set: newValue } } as any;
        if (this.files[index].computeNameFromTaigaId) {
            changes.name = { "$set": this.getDefaultName(newValue) }
        }
        this.files = update(this.files, { [index]: changes })
        this.listener(this.files)
    }

    onGCSPathChange(index: number, newValue: string) {
        let changes = { gcsPath: { $set: newValue } } as any;
        if (this.files[index].computeNameFromTaigaId) {
            changes.name = { "$set": this.getDefaultName(newValue) }
        }
        this.files = update(this.files, { [index]: changes })
        this.listener(this.files)
    }

    onNameChange(index: number, newName: string) {
        this.files = update(this.files, { [index]: { name: { $set: newName }, computeNameFromTaigaId: { $set: false } } })
        this.listener(this.files)
    }

}

export class UploadTable extends React.Component<UploadTableProps, UploadTableState> {
    constructor(props: any) {
        super(props);
    }

    renderProcessingTable() {
        let rows = this.props.files.map((file, i) => {
            let name = file.name;
            let progressBar = file.progressMessage as any;

            if (file.progress) {
                progressBar = (<div className="progress">
                    <div className="progress-bar" style={{ width: file.progress + "%" }}>{file.progressMessage}</div>
                </div>)
            }

            return (<tr key={"r" + i}>
                <td>
                    {name}
                </td>
                <td>
                    {progressBar}
                </td>
            </tr>);
        });

        return (<table className="table">
            <thead>
                <tr>
                    <th style={{ width: "150px" }} >
                        Name
                    </th>
                    <th>
                        Progress
                    </th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>);

    }

    render() {
        if (this.props.isProcessing) {
            return this.renderProcessingTable();
        } else {
            return this.renderInputForm();
        }
    }

    renderInputForm() {
        let rows = this.props.files.map((file, i) => {
            let name = file.name;
            let source: any = "";
            let typeLabel: any = "";

            if (file.fileType == UploadFileType.GCSPath) {
                typeLabel = "GCS Object";
                source = (
                  <input
                    className="form-control"
                    placeholder="GCS Object Path"
                    type="text"
                    value={file.gcsPath}
                    onChange={event =>
                      this.props.controller.onGCSPathChange(
                        i,
                        event.target.value
                      )
                    }
                  />
                );
            } else if (file.fileType == UploadFileType.TaigaPath) {
                typeLabel = "Taiga file";
                source = <input className="form-control" placeholder="Taiga ID" type="text" value={file.existingTaigaId} onChange={event => this.props.controller.onTaigaIdChange(i, event.target.value)} />
            } else if (file.fileType == UploadFileType.Upload) {
                source = <select className="form-control" value={file.uploadFormat} onChange={event => this.props.controller.changeUploadFormat(i, event.target.value)}>
                    <option value={InitialFileType.TableCSV}>{InitialFileType.TableCSV}</option>
                    <option value={InitialFileType.NumericMatrixCSV}>{InitialFileType.NumericMatrixCSV}</option>
                    <option value={InitialFileType.TableTSV}>{InitialFileType.TableTSV}</option>
                    <option value={InitialFileType.NumericMatrixTSV}>{InitialFileType.NumericMatrixTSV}</option>
                    <option value={InitialFileType.GCT}>{InitialFileType.GCT}</option>
                    <option value={InitialFileType.Raw}>{InitialFileType.Raw}</option>
                </select>

                // source = file.uploadFile.name;
            } else {
                throw "unknown filetype";
            }

            return (<tr key={"r" + i}>
                <td>
                    <input
                        type="text"
                        value={name}
                        onChange={event =>
                            this.props.controller.onNameChange(
                                i,
                                event.target.value
                            )
                        }
                        className="form-control"
                        placeholder="Name"
                        required
                    />
                    </td>
                <td>
                    {source}
                </td>
                <td>
                    <button type="button" className="btn btn-default" aria-label="Left Align" onClick={event => this.props.controller.onDelete(i)}>
                        <span className="glyphicon glyphicon-trash" aria-hidden="true"></span>
                    </button>
                </td>
            </tr>);
        });

        return (<table className="table">
            <thead>
                <tr>
                    <th style={{ width: "150px" }} >
                        Name
                    </th>
                    <th>
                        Source
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

