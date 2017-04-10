import * as React from "react";
import {Link} from 'react-router';
import * as update from 'immutability-helper';

import {Button, Col, Glyphicon, Grid, Row, OverlayTrigger, Tooltip, Well} from 'react-bootstrap';
import {InputGroup, InputGroupButton, FormGroup, FormControl} from 'react-bootstrap';

import {BootstrapTable, TableHeaderColumn, SortOrder} from "react-bootstrap-table";

import ClipboardButton from '../utilities/r-clipboard';
import {LeftNav} from "./LeftNav"

import {TaigaApi} from "../models/api"
import {User, AccessLog} from "../models/models";

import {relativePath} from "../utilities/route";
import {toLocalDateString} from "../utilities/formats";


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

            let mappedAL = userAccessLogs.map((userAccessLog) => {
                return new AccessLog(userAccessLog);
            });

            this.setState({
                accessLogs: mappedAL
            })
        })
    }

    datasetFormatter(cell: any, row: any) {
        return <Link to={relativePath(
                      "dataset/" + row.dataset_id)}>{ cell }</Link>
    }

    lastAccessFormatter(cell: any, row: any) {
        let _date = new Date(cell);
        var options = {
            month: "2-digit", day: "2-digit", year: "2-digit",
            hour: "2-digit", minute: "2-digit"
        };
        return _date.toLocaleTimeString("en-us", options);
    }

    render() {
        let navItems: Array<any> = [];

        let displayAccessLogs = null;

        const options = {
            defaultSortName: 'last_access',
            defaultSortOrder: 'desc' as SortOrder,
            sizePerPageList: [
                25, 30, 50, 100
            ],
            sizePerPage: 50
        };

        if (this.state.accessLogs.length != 0) {
            displayAccessLogs = (
                <BootstrapTable data={this.state.accessLogs} striped hover options={options} pagination>
                    <TableHeaderColumn isKey dataField='dataset_id' hidden>Dataset Id</TableHeaderColumn>
                    <TableHeaderColumn dataField='dataset_name'
                                       dataFormat={ this.datasetFormatter }
                                       headerAlign='center'
                                       dataSort>Dataset</TableHeaderColumn>
                    <TableHeaderColumn dataField='last_access'
                                       headerAlign="center"
                                       dataAlign='center'
                                       dataFormat={ this.lastAccessFormatter }
                                       dataSort>Last access</TableHeaderColumn>
                </BootstrapTable>
            );
        }

        return <div>
            <LeftNav items={navItems}/>

            <div id="main-content">
                <Grid>
                    <Row>
                        <h1>Your dataset access history</h1>
                    </Row>
                    <Row>
                        {displayAccessLogs}
                    </Row>
                </Grid>
            </div>
        </div>
    }
}