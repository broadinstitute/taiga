import * as React from "react";
import { FormGroup, ControlLabel, FormControl } from 'react-bootstrap';
import { InitialFileType } from "../../models/models";
import { getInitialFileTypeFromMimeType } from "../../Utilities/formats";

interface TypeEditorProps {
    defaultValue: any;
    onUpdate: any;
}

interface TypeEditorState {
    type: InitialFileType;
}

export class TypeEditorBootstrapTable extends React.Component<TypeEditorProps, TypeEditorState> {
    constructor(props: any) {
        super(props);
        // TODO: How can we ensure we are not erasing/forgetting states defined in the interface?
        let initType: InitialFileType = getInitialFileTypeFromMimeType(this.props.defaultValue);

        this.state = {
            type: initType
        }
    }

    focus() {
        // this.refs.inputRef.focus();
    }

    updateData(evt: any) {
        let newType: InitialFileType = evt.currentTarget.value;
        console.log("We just updated the value of the control: " + evt.currentTarget.value);
        this.setState({
            type: newType
        });
        this.props.onUpdate(newType)
    }

    render() {
        return (
            <FormGroup controlId="formControlsSelect">
                <FormControl componentClass="select"
                             value={ this.state.type }
                             onChange={ (evt) => this.updateData(evt) } >
                    <option value={InitialFileType.NumericMatrixCSV}>{InitialFileType.NumericMatrixCSV}</option>
                    <option value={InitialFileType.Raw}>{InitialFileType.Raw}</option>
                    <option value={InitialFileType.Table}>{InitialFileType.Table}</option>
                </FormControl>
            </FormGroup>
        )
    }

}