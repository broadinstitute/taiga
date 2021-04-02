import * as React from "react";
import { useState, useEffect, useRef } from "react";
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
  const {
    id,
    title,
    value: defaultValue,
    disabled,
    placement,
    onConfirm,
  } = props;
  const [value, setValue] = useState(defaultValue);

  const overlayRef = useRef<OverlayTrigger>();

  useEffect(() => {
    setValue(defaultValue);
  }, [defaultValue]);

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
          value={value}
          bsClass="form-control input-fixed-width"
        />
        <span className="spacer-xs" />
        <Button
          bsStyle="primary"
          onClick={() => {
            onConfirm(value);
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
      <a aria-label={title} title={title} className="editable">
        {value}
      </a>
    </OverlayTrigger>
  );
};

export default TextEditable;
