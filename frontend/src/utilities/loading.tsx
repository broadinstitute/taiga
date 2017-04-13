import * as React from "react";

import {Well} from "react-bootstrap";

interface LoadingOverlayProps {
    message?: string;
}

export class LoadingOverlay extends React.Component<LoadingOverlayProps, any> {
    render() {
        return <div className="loadingOverlay">
            { this.props.message &&
                <Well>{ this.props.message }</Well>
            }
        </div>
    }
}
