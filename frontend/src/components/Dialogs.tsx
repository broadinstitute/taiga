import * as React from "react";
import * as Modal from "react-modal";
import * as Showdown from "showdown";

import {ControlLabel, FormControl, FormGroup, HelpBlock} from "react-bootstrap";

interface InputFolderIdProps extends DialogProps {
    cancel: () => void;
    save: (folderId: string) => void;
    actionDescription: string;

    validationState?: string;
    help?: string;
}

interface InputFolderIdState extends DialogState {
    folderId: string;
}


interface CreateFolderProps extends DialogProps {
    save: (name: string, description: string) => void;
}

interface EditStringProps {
    isVisible: boolean;
    initialValue: string;
    cancel: () => void;
    save: (name: string) => void;
}

export interface DialogProps {
    isVisible: boolean;
    cancel: () => void;
}

export interface DialogState {
}

// Don't forget to modify modalStyles in Upload.tsx if you change the code of modalStyles
const modalStyles: any = {
    content: {
        background: null,
        border: null
    }
};

export class EditName extends React.Component<EditStringProps, any> {
    textInput: any;

    render() {
        //className="Modal__Bootstrap modal-dialog"
        return <Modal
            style={ modalStyles }
            closeTimeoutMS={150}
            isOpen={this.props.isVisible}
            onRequestClose={this.props.cancel}
            contentLabel="EditName">
            <form>
                <div className="modal-content">
                    <div className="modal-body">
                        <div className="form-group">
                            <label htmlFor="nameInput">Name</label>
                            <input type="text" defaultValue={this.props.initialValue} className="form-control"
                                   id="nameInput" ref={ (c) => {this.textInput = c}  }/>
                        </div>
                    </div>
                    <div className="modal-footer">
                        <button type="button" className="btn btn-default" onClick={this.props.cancel}>Close</button>
                        <button type="button" className="btn btn-primary"
                                onClick={ () => { this.props.save(this.textInput.value) } }>Save changes
                        </button>
                    </div>
                </div>
            </form>
        </Modal>
    }
}


export class EditDescription extends React.Component<EditStringProps, any> {
    textArea: any;

    render() {
        //className="Modal__Bootstrap modal-dialog"
        return <Modal
            style={ modalStyles }
            closeTimeoutMS={150}
            isOpen={this.props.isVisible}
            onRequestClose={this.props.cancel}
            contentLabel="EditDescription">
            <form>
                <div className="modal-content">
                    <div className="modal-body">
                        <div className="form-group">
                            <label htmlFor="descriptionInput">Description</label>
                            <textarea rows={15} defaultValue={this.props.initialValue} className="form-control"
                                      id="descriptionInput" ref={ (c) => {this.textArea = c}  }></textarea>
                        </div>
                    </div>
                    <div className="modal-footer">
                        <button type="button" className="btn btn-default" onClick={this.props.cancel}>Close</button>
                        <button type="button" className="btn btn-primary"
                                onClick={() => { this.props.save(this.textArea.value) } }>Save changes
                        </button>
                    </div>
                </div>
            </form>
        </Modal>
    }
}

export class CreateFolder extends React.Component<CreateFolderProps, any> {
    textInput: any;
    textArea: any;

    render() {
        //className="Modal__Bootstrap modal-dialog"
        return <Modal
            style={ modalStyles }
            closeTimeoutMS={150}
            isOpen={this.props.isVisible}
            onRequestClose={this.props.cancel}
            contentLabel="CreateFolder">
            <form>
                <div className="modal-content">
                    <div className="modal-body">
                        <div className="form-group">
                            <label htmlFor="nameInput">Name</label>
                            <input type="text" placeholder="A name is required"
                                   className="form-control"
                                   id="nameInput"
                                   ref={ (c) => {this.textInput = c}  }/>

                            <label htmlFor="descriptionInput">Description</label>
                            <textarea rows={15}
                                      placeholder="No description given"
                                      className="form-control" id="descriptionInput"
                                      ref={ (c) => {this.textArea = c}  }
                            />
                        </div>
                    </div>
                    <div className="modal-footer">
                        <button type="button" className="btn btn-default" onClick={this.props.cancel}>Close</button>
                        <button type="button" className="btn btn-primary" onClick={() => {
                  this.props.save(this.textInput.value, this.textArea.value)
              } }>Save changes
                        </button>
                    </div>
                </div>
            </form>
        </Modal>
    }
}

let converter = new Showdown.Converter()

export function renderDescription(description: string) {
    let description_section: any = null;

    if (description) {
        let desc_as_html = {__html: converter.makeHtml(description)};
        description_section = <div className="well well-sm" dangerouslySetInnerHTML={desc_as_html}/>
    }

    return description_section;
}

export class InputFolderId extends React.Component<InputFolderIdProps, InputFolderIdState> {
    constructor(props) {
        super(props);
    }

    componentWillMount() {
        this.setState({
            folderId: ""
        })
    }

    componentWillReceiveProps(nextProps: any) {
        // When we open the component, we reset it
        if (nextProps.isVisible && this.props.isVisible != nextProps.isVisible) {
            this.setState({
                folderId: ""
            })
        }
    }

    handleChange(e) {
        this.setState({
                folderId: e.target.value
            }
        );
    }

    render() {
        let textPlaceHolder = "Enter here the id of the folder to " + this.props.actionDescription;

        return (
            <Modal
                style={ modalStyles }
                closeTimeoutMS={150}
                isOpen={this.props.isVisible}
                onRequestClose={this.props.cancel}
                contentLabel="InputFolderId">
                <form>
                    <div className="modal-content">
                        <div className="modal-body">
                            <FormGroup validationState={this.props.validationState}>
                                <ControlLabel>Folder ID</ControlLabel>
                                <FormControl
                                    type="text"
                                    value={this.state.folderId}
                                    placeholder={ textPlaceHolder }
                                    onChange={(e) => this.handleChange(e)}
                                />
                                { this.props.help && <HelpBlock>{this.props.help}</HelpBlock> }
                            </FormGroup>
                        </div>

                        <div className="modal-footer">
                            <button type="button" className="btn btn-default" onClick={ () => this.props.cancel() }>
                                Close
                            </button>
                            <button type="button" className="btn btn-primary" onClick={ () => {
                                this.props.save(this.state.folderId)}
                            }>
                                Save changes
                            </button>
                        </div>
                    </div>
                </form>
            </Modal>
        )
    }
}
