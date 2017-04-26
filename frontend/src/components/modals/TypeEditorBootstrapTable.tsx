import * as React from "react";
import { FormGroup, ControlLabel, FormControl } from 'react-bootstrap';
import { InitialFileType } from "../../models/models";
import { getInitialFileTypeFromMimeType } from "../../utilities/formats";

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
        this.setState({
            type: newType
        });
        this.props.onUpdate(newType)
    }

    render() {
        // Options values should also be changed in formats.tsx
        // TODO: Use the same text to print to the user between selection of option and print result in formats.tsx
        return (
            <FormGroup controlId="formControlsSelect">
                <FormControl componentClass="select"
                             value={ this.state.type }
                             onChange={ (evt) => this.updateData(evt) } >
                    <option value={InitialFileType.TableCSV}>{InitialFileType.TableCSV}</option>
                    <option value={InitialFileType.NumericMatrixCSV}>{InitialFileType.NumericMatrixCSV}</option>
                    <option value={InitialFileType.TableTSV}>{InitialFileType.TableTSV}</option>
                    <option value={InitialFileType.NumericMatrixTSV}>{InitialFileType.NumericMatrixTSV}</option>
                    <option value={InitialFileType.GCT}>{InitialFileType.GCT}</option>
                    <option value={InitialFileType.Raw}>{InitialFileType.Raw}</option>
                </FormControl>
            </FormGroup>
        )
    }

}