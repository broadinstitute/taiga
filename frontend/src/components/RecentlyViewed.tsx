import * as React from "react";
import {Link} from 'react-router';
import * as update from 'immutability-helper';

import {Button, Col, Glyphicon, Grid, Row, OverlayTrigger, Tooltip, Well} from 'react-bootstrap';
import {InputGroup, InputGroupButton, FormGroup, FormControl} from 'react-bootstrap';

import ClipboardButton from '../utilities/r-clipboard';
import {LeftNav} from "./LeftNav"

import {TaigaApi} from "../models/api"
import {User, AccessLog} from "../models/models";

import {relativePath} from "../utilities/route";


interface RecentlyViewedProps {

}

interface RecentlyViewedState {
    accessLogs?: Array<AccessLog>
}

let tapi: TaigaApi = null;

export class RecentlyViewed extends React.Component<RecentlyViewedProps, RecentlyViewedState> {
    static contextTypes = {
        tapi: React.PropTypes.object
    };

    constructor(props: any) {
        super(props);

        this.state = {
            accessLogs: []
        }
    }

    componentDidMount() {
        tapi = (this.context as any).tapi;
        this.doFetch();
    }

    doFetch() {
        return tapi.get_user_dataset_access_log().then((userAccessLogs) => {
            // TODO: Think about not using it as State because it does not change during the page lifecycle

            const original_accessLogs: any = this.state.accessLogs;
            const new_accessLogs = update(original_accessLogs, {$set: userAccessLogs});
            this.setState({
               accessLogs: new_accessLogs
            })
        })
    }

    render() {
        let navItems: Array<any> = [];

        let displayAccessLogs = null;

        if(this.state.accessLogs.length != 0){
            displayAccessLogs = this.state.accessLogs.map((accessLog: AccessLog) => {
                // return <li>{accessLog.last_access} {accessLog.dataset}</li>
                return <li key={accessLog.dataset.id}>
                    {accessLog.last_access}:
                    <Link to={relativePath("dataset/"+accessLog.dataset.id)}>
                        {accessLog.dataset.name}
                        </Link>
                    </li>
            });
        }

        return <div>
            <LeftNav items={navItems}/>

            <div id="main-content">
                <ul>
                    {displayAccessLogs}
                </ul>
            </div>
        </div>
    }
}