import * as React from "react";
import * as ReactDOM from "react-dom";
import { useState, useRef } from "react";
import { Button, Glyphicon, Overlay, Tooltip } from "react-bootstrap";

interface Props {
  textToCopy: string;
  tooltipId: string;
  disabled?: boolean;
}

const ClipboardButton = (props: Props) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const buttonRef = useRef();
  return (
    <>
      <Button
        disabled={props.disabled}
        ref={buttonRef}
        onClick={() => {
          navigator.clipboard.writeText(props.textToCopy);
          setShowTooltip(true);
          setTimeout(() => {
            setShowTooltip(false);
          }, 2000);
        }}
        aria-label="Copy to clipboard"
        title="Copy"
      >
        <Glyphicon glyph="copy" />
      </Button>
      <Overlay
        placement="top"
        show={showTooltip}
        target={() => ReactDOM.findDOMNode(buttonRef.current)}
      >
        <Tooltip id={props.tooltipId}>Copied</Tooltip>
      </Overlay>
    </>
  );
};

export default ClipboardButton;
