import React from "react";
import { Modal, Button } from "react-bootstrap";
import LiveMarkdownEditor from "src/common/components/LiveMarkdownEditor";

import "src/common/styles/edit_description_modal.css";

interface Props {
  show: boolean;
  initialDescription: string;
  onClose: () => void;
  onSave: (description: string) => void;
}

const EditDescriptionModal = (props: Props) => {
  const { initialDescription, show, onClose, onSave } = props;
  const [description, setDescription] = React.useState(initialDescription);
  return (
    <Modal
      show={show}
      onHide={onClose}
      className="taiga-edit-description-modal"
    >
      <Modal.Header closeButton>
        <Modal.Title>Modal heading</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <LiveMarkdownEditor
          description={description}
          onChange={(newDescription) => setDescription(newDescription)}
          defaultShowPreview
        />
      </Modal.Body>
      <Modal.Footer>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={() => {
            onSave(description);
            onClose();
          }}
        >
          Save
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default EditDescriptionModal;
