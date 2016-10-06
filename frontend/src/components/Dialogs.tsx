import * as React from "react";
import * as Modal from "react-modal";
import * as Showdown from "showdown";

interface EditStringProps {
    isVisible : boolean;
    initialValue : string;
    cancel: () => void;
    save: (name: string) => void;
}

const modalStyles : any = {
  content : {
    background: null,
    border: null
  }
};

export class EditName extends React.Component<EditStringProps, any> {
    textInput : any;

    render() {
        //className="Modal__Bootstrap modal-dialog"
        return <Modal 
          style={ modalStyles }
          closeTimeoutMS={150}
          isOpen={this.props.isVisible}
          onRequestClose={this.props.cancel}>
          <form>
          <div className="modal-content">
            <div className="modal-body">
                <div className="form-group">
                    <label for="nameInput">Name</label>
                    <input type="text" defaultValue={this.props.initialValue} className="form-control" id="nameInput" ref={ (c) => {this.textInput = c}  }/>
                </div>
              </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-default" onClick={this.props.cancel}>Close</button>
              <button type="button" className="btn btn-primary" onClick={ () => { this.props.save(this.textInput.value) } }>Save changes</button>
            </div>
          </div>
                </form>
        </Modal>
        }
    }


export class EditDescription extends React.Component<EditStringProps, any> {
    textArea : any;

    render() {
        //className="Modal__Bootstrap modal-dialog"
        return <Modal 
          style={ modalStyles }
          closeTimeoutMS={150}
          isOpen={this.props.isVisible}
          onRequestClose={this.props.cancel}>
        <form>
          <div className="modal-content">
            <div className="modal-body">
                <div className="form-group">
                    <label for="descriptionInput">Description</label>
                    <textarea rows="15"  defaultValue={this.props.initialValue} className="form-control" id="descriptionInput" ref={ (c) => {this.textArea = c}  }></textarea>
                </div>
              </div>
            <div className="modal-footer">
              <button type="button" className="btn btn-default" onClick={this.props.cancel}>Close</button>
              <button type="button" className="btn btn-primary" onClick={() => { this.props.save(this.textArea.value) } }>Save changes</button>
            </div>
          </div>
        </form>
        </Modal>
        }
    }

let converter = new Showdown.Converter()

export function renderDescription(description :string) {
    let description_section : any = null;

    if(description) {
        let desc_as_html = {__html: converter.makeHtml(description)};
        description_section = <div className="well well-sm" dangerouslySetInnerHTML={desc_as_html} />
    }

    return description_section;
}
