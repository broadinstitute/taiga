import React, { useState, useEffect, useRef } from "react";

import {
  Button,
  Glyphicon,
  OverlayTrigger,
  Popover,
  Form,
  FormControl,
  FormControlProps,
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
    value: initialValue,
    disabled,
    placement,
    onConfirm,
  } = props;
  const [value, setValue] = useState(initialValue);

  const overlayRef = useRef<OverlayTrigger>();

  useEffect(() => {
    setValue(initialValue);
  }, [initialValue]);

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
          onChange={(e: React.FormEvent<FormControl & FormControlProps>) =>
            setValue(e.currentTarget.value as string)
          }
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
      <button
        aria-label={title}
        title={title}
        className="editable"
        type="button"
      >
        {initialValue}
      </button>
    </OverlayTrigger>
  );
};

TextEditable.defaultProps = {
  disabled: false,
  placement: "top",
};

export default TextEditable;
