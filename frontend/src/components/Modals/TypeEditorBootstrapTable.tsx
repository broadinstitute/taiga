import * as React from "react";
import { FormGroup, ControlLabel, FormControl } from 'react-bootstrap';
import { getFormatType } from "../../Utilities/formats";
import { SupportedTypeEnum } from "../../models/models";

interface TypeEditorProps {
    defaultValue: any;
    onUpdate: any;
}

interface TypeEditorState {
    type: SupportedTypeEnum;
}

export class TypeEditorBootstrapTable extends React.Component<TypeEditorProps, TypeEditorState> {
    constructor(props: any) {
        super(props);
        // TODO: How can we ensure we are not erasing/forgetting states defined in the interface?
        let initType: SupportedTypeEnum = getFormatType(this.props.defaultValue);

        this.state = {
            type: initType
        }
    }

    focus() {
        // this.refs.inputRef.focus();
    }

    updateData(evt: any) {
        let newType: SupportedTypeEnum = evt.currentTarget.value;
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
                    <option value={SupportedTypeEnum.Raw}>{SupportedTypeEnum.Raw}</option>
                    <option value={SupportedTypeEnum.HDF5}>{SupportedTypeEnum.HDF5}</option>
                    <option value={SupportedTypeEnum.Columnar}>{SupportedTypeEnum.Columnar}</option>
                </FormControl>
            </FormGroup>
        )
    }

}