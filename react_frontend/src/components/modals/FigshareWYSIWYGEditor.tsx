import * as React from "react";

import ReactQuill, { Quill } from "react-quill";
let Inline = Quill.import("blots/inline");

class BoldBlot extends Inline {}
BoldBlot.blotName = "bold";
BoldBlot.tagName = "b";
Quill.register("formats/bold", BoldBlot);

class ItalicBlot extends Inline {}
ItalicBlot.blotName = "italic";
ItalicBlot.tagName = "i";
Quill.register("formats/bold", ItalicBlot);

const modules = {
  toolbar: [
    "bold",
    "italic",
    "underline",
    { script: "sub" },
    { script: "super" },
  ],
};
const formats = ["bold", "italic", "underline", "script"];

type Props = {
  value: string;
  onChange: (value: string) => void;
};

export default class FigshareWYSIWYGEditor extends React.Component<Props> {
  render() {
    return (
      <ReactQuill
        theme="snow"
        value={this.props.value}
        onChange={this.props.onChange}
        modules={modules}
        formats={formats}
      />
    );
  }
}
