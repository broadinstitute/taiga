import * as React from "react";
import {Link} from 'react-router';
import * as update from 'immutability-helper';

import {LeftNav, MenuItem} from "./LeftNav";
import * as Folder from "../models/models";
import {TaigaApi} from "../models/api";

import * as Dialogs from "./Dialogs";
import * as Upload from "./modals/Upload";
import {TreeView} from "./modals/TreeView";

import {toLocalDateString} from "../utilities/formats";
import {relativePath} from "../utilities/route";
import {LoadingOverlay} from "../utilities/loading";

interface NotFoundProps {
    message?: string;
}

export class NotFound extends React.Component<NotFoundProps, any> {
    render() {
        return <div className="notFound">
                <h1>Not found :(</h1>
                <p>
                    {this.props.message}
                </p>
            </div>
    }
}