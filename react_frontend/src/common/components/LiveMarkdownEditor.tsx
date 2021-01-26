import * as React from "react";
import * as Showdown from "showdown";
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

  const [showPreview, setShowPreview] = React.useState(
    defaultShowPreview || false
  );

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
          ></div>
        </Well>
      )}
    </div>
  );
};

export default LiveMarkdownEditor;
