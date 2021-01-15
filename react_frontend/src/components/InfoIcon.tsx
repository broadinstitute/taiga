import * as React from "react";
import { Glyphicon, OverlayTrigger, Tooltip } from "react-bootstrap";

interface Props {
  tooltipId: string;
  message: React.ReactNode;
}

export default class InfoIcon extends React.Component<Props> {
  render() {
    const tooltip = (
      <Tooltip id={this.props.tooltipId} style={{ zIndex: 1151 }}>
        {this.props.message}
      </Tooltip>
    );

    return (
      <OverlayTrigger placement="top" overlay={tooltip}>
        <Glyphicon glyph="info-sign" />
      </OverlayTrigger>
    );
  }
}
