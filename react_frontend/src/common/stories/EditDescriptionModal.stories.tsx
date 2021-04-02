import React, { useState } from "react";
import { Story, Meta } from "@storybook/react/types-6-0";
import { Button } from "react-bootstrap";

import EditDescriptionModal from "src/common/components/EditDescriptionModal";

export default {
  title: "Common/EditDescriptionModal",
  component: EditDescriptionModal,
} as Meta;

interface WrapperProps {
  initialDescription: string;
}

const Template: Story<WrapperProps> = (args) => {
  const { initialDescription } = args;
  const [show, setShow] = useState(false);
  const [description, setDescription] = useState(initialDescription);

  const onClose = () => {
    setShow(false);
  };
  const onSave = (newDescription: string) => {
    setDescription(newDescription);
  };

  return (
    <>
      <Button
        onClick={() => {
          setShow(true);
        }}
      >
        Open modal
      </Button>
      <div>Current description:</div>
      <div>{description}</div>
      <EditDescriptionModal
        title="Edit description story"
        initialDescription={description}
        show={show}
        onClose={onClose}
        onSave={onSave}
      />
    </>
  );
};

export const Default = Template.bind({});

Default.args = {
  initialDescription: null,
} as WrapperProps;
