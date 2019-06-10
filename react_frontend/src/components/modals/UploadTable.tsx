import * as React from "react";
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

interface UploadFile {
    name: string; // the name of the datafile record in once dataset has been created

    gcsPath: string; // If the path to a GCS object
    uploadName: string; // the filename if was uploaded from local machine
    exitingTaigaId: string; // the ID of an existing taiga data file.
}

interface UploadTableProps {

}

interface UploadTableState {
    files: Array<UploadFile>;
}

export class UploadTable extends React.Component<UploadTableProps, UploadTableState> {
    constructor(props: any) {
        super(props);
    }
}
