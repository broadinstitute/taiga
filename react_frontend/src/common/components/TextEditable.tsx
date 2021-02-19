import * as React from "react";
import { useState, useRef } from "react";
import * as ReactDOM from "react-dom";
import {
  Button,
  Glyphicon,
  OverlayTrigger,
  Popover,
  Form,
  FormControl,
} from "react-bootstrap";

import "src/common/styles/editable.css";

interface Props {
  id: string;
  title: string;
  value: string;
  disabled?: boolean;
  placement?: "top" | "bottom" | "left" | "right";
  onConfirm: (newValue: string) => void;
}
const TextEditable = (props: Props) => {
  const { id, title, value, disabled, placement, onConfirm } = props;

  const overlayRef = useRef<OverlayTrigger>();
  const buttonRef = useRef<HTMLAnchorElement>();
  const inputRef = useRef<FormControl>();

  if (disabled) {
    return <span>{value}</span>;
  }

  const hideOverlay = () => {
    overlayRef.current.setState({ show: false });
  };

  const popover = (
    <Popover id={id} title={title}>
      <Form inline>
        <FormControl
          type="text"
          defaultValue={value}
          ref={inputRef}
          bsClass="form-control input-fixed-width"
        />
        <span className="spacer-xs" />
        <Button
          bsStyle="primary"
          onClick={() => {
            const newValue = (ReactDOM.findDOMNode(
              inputRef.current
            ) as HTMLInputElement).value;
            onConfirm(newValue);
            hideOverlay();
          }}
          bsClass="btn btn-primary "
        >
          <Glyphicon glyph="ok" />
        </Button>
        <span className="spacer-xs" />

        <Button onClick={hideOverlay}>
          <Glyphicon glyph="ban-circle" />
        </Button>
      </Form>
    </Popover>
  );

  return (
    <OverlayTrigger
      trigger="click"
      placement={placement || "top"}
      rootClose
      overlay={popover}
      ref={overlayRef}
    >
      <a ref={buttonRef} aria-label={title} title={title} className="editable">
        {value}
      </a>
    </OverlayTrigger>
  );
};

export default TextEditable;
