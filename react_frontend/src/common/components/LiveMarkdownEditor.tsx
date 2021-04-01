import React, { useState, useEffect } from "react";
import Showdown from "showdown";
import {
  FormGroup,
  ControlLabel,
  FormControl,
  Checkbox,
  FormControlProps,
  Well,
} from "react-bootstrap";

const converter = new Showdown.Converter();

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
        />
      </FormGroup>
      {showPreview && (
        <Well>
          <div
            dangerouslySetInnerHTML={{
              __html: converter.makeHtml(description),
            }}
          />
        </Well>
      )}
    </div>
  );
};

LiveMarkdownEditor.defaultProps = {
  defaultShowPreview: false,
};

export default LiveMarkdownEditor;
