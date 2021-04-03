import React, { useState, useEffect } from "react";
import {
  FormGroup,
  ControlLabel,
  FormControl,
  Checkbox,
  FormControlProps,
} from "react-bootstrap";
import { renderDescription } from "src/components/Dialogs";

interface LiveMarkdownEditorProps {
  description: string;
  onChange: (description: string) => void;
  defaultShowPreview?: boolean;
}

const LiveMarkdownEditor = (props: LiveMarkdownEditorProps) => {
  const { description, onChange, defaultShowPreview } = props;

  const [showPreview, setShowPreview] = useState(defaultShowPreview);

  useEffect(() => {
    setShowPreview(defaultShowPreview);
  }, [defaultShowPreview]);

  return (
    <div>
      <FormGroup controlId="markdown-editor">
        <ControlLabel>Description</ControlLabel>
        <Checkbox
          inline
          checked={showPreview}
          onChange={() => setShowPreview((cur) => !cur)}
          bsClass="pull-right checkbox"
        >
          Show preview
        </Checkbox>
        <FormControl
          componentClass="textarea"
          placeholder="No description"
          value={description}
          onChange={(e: React.FormEvent<FormControl & FormControlProps>) =>
            onChange(e.currentTarget.value as string)
          }
          rows={5}
        />
      </FormGroup>
      {showPreview &&
        (description ? (
          renderDescription(description)
        ) : (
          <div className="italicize">None</div>
        ))}
    </div>
  );
};

LiveMarkdownEditor.defaultProps = {
  defaultShowPreview: false,
};

export default LiveMarkdownEditor;
