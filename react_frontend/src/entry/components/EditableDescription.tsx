import React, { useState } from "react";
import { Button } from "react-bootstrap";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faEdit } from "@fortawesome/free-solid-svg-icons";

import { renderDescription } from "src/components/Dialogs";
import EditDescriptionModal from "src/common/components/EditDescriptionModal";

interface Props {
  description: string;
  title: string;
  onSave: (newDescription: string) => void;
}

const EditableDescription = (props: Props) => {
  const { description, title, onSave } = props;
  const [showEditDescriptionModal, setShowEditDescriptionModal] = useState(
    false
  );

  return (
    <>
      <h3 className="h5 mb-1">
        <span className="mr-2">{title}</span>
        <Button bsSize="xs" onClick={() => setShowEditDescriptionModal(true)}>
          <FontAwesomeIcon icon={faEdit} />
        </Button>
      </h3>

      {description ? (
        renderDescription(description)
      ) : (
        <div className="italicize">None</div>
      )}

      <EditDescriptionModal
        title="Edit description"
        show={showEditDescriptionModal}
        initialDescription={description}
        onClose={() => setShowEditDescriptionModal(false)}
        onSave={onSave}
      />
    </>
  );
};

export default EditableDescription;
