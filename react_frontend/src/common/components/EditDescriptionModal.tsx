import * as React from "react";
import { Modal, Button } from "react-bootstrap";
import ReactQuill, { Quill } from "react-quill";

interface Props {
  show: boolean;
  initialDescription: string;
  onClose: () => void;
  onSave: (description: string) => void;
}

const EditDescriptionModal = (props: Props) => {
  const [description, setDescription] = React.useState(
    props.initialDescription
  );
  return (
    <Modal show={props.show} onHide={props.onClose}>
      <Modal.Header closeButton>
        <Modal.Title>Modal heading</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <ReactQuill
          theme="snow"
          value={this.props.value}
          onChange={this.props.onChange}
          modules={modules}
          formats={formats}
        />
      </Modal.Body>
      <Modal.Footer>
        <Button onClick={props.onClose}>Cancel</Button>
        <Button onClick={() => props.onSave(description)}></Button>
      </Modal.Footer>
    </Modal>
  );
};

export default EditDescriptionModal;
