import * as React from "react";

import {Button, Col, Glyphicon, Grid, Row, OverlayTrigger, Tooltip, Well} from 'react-bootstrap';
import {InputGroup, InputGroupButton, FormGroup, FormControl} from 'react-bootstrap';

import ClipboardButton from '../utilities/r-clipboard';
import {LeftNav, MenuItem} from "./LeftNav";

import {TaigaApi} from "../models/api"
import {User} from "../models/models";


export interface ProvenanceProps {
    params: any;
}

export interface ProvenanceState {

}

let tapi: TaigaApi = null;
let currentUser: string = null;

export class Provenance extends React.Component<ProvenanceProps, ProvenanceState> {
    static contextTypes = {
        tapi: React.PropTypes.object,
        currentUser: React.PropTypes.string
    };

    componentDidMount() {
        tapi = (this.context as any).tapi;
        currentUser = (this.context as any).currentUser;
        this.doFetch();
    }

    doFetch(){
        return tapi.get_provenance_graph(this.props.params.graphId).then((graph) => {
            // Draw cytoscape graph
        });
    }

    render() {
        let navItems: MenuItem[] = [];
        return <div>
            <LeftNav items={navItems}/>
            <div id="main-content">
                <span>Hello world: {this.props.params.graphId}</span>
            </div>
        </div>
    }
}