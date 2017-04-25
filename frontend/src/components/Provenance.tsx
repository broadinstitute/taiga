import * as React from "react";

// import cytoscape from 'cytoscape';
let cytoscape = require('cytoscape');
let dagre = require('dagre');

import {Button, Col, Glyphicon, Grid, Row, OverlayTrigger, Tooltip, Well} from 'react-bootstrap';
import {InputGroup, InputGroupButton, FormGroup, FormControl} from 'react-bootstrap';

import ClipboardButton from '../utilities/r-clipboard';
import {LeftNav, MenuItem} from "./LeftNav";

import {TaigaApi} from "../models/api"
import {User, ProvenanceGraph, ProvenanceGraphFull} from "../models/models";


export interface ProvenanceProps {
    params: any;
}

export interface ProvenanceState {

}

const cyStyle = {
    marginTop: '1%',
    width: '100%',
    height: '97%',
    border: 'solid black'
};

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

    doFetch() {
        return tapi.get_provenance_graph(this.props.params.graphId).then((graph) => {
            // Draw cytoscape graph
            this.draw_cytoscape(graph);
        });
    }

    // exec_resize() {
    //     var container = document.getElementsByClassName(".container");
    //     debugger;
    //
    //     var h = window.innerHeight;
    //     var w = container.width();
    //
    //     var cy_offset = document.getElementById('cy').offset();
    //
    //     var cyel = document.getElementById('cy');
    //     var cy_w = w - 10;
    //     var cy_h = h - cy_offset.top - 10;
    //     if (cy_h < 100) {
    //         cy_h = 100;
    //     }
    //     cyel.width(cy_w);
    //     cyel.height(cy_h);
    //     //console.log("window sized", cy_w, cy_h);
    // }


    draw_cytoscape(graph: ProvenanceGraphFull) {
        let elements = [];
        let possibleRoots: Map<string, boolean> = new Map();
        // debugger;
        graph.provenance_nodes.forEach((node) => {
            elements.push({
                data: {
                    id: "n" + node.node_id,
                    label: node.label,
                    type: node.type,
                    datafile_id: node.datafile_id
                }
            });
            possibleRoots.set("n" + node.node_id, true);

            node.from_edges.forEach((from_edge) => {
                elements.push({
                    data: {
                        id: "e" + from_edge.edge_id,
                        source: "n" + from_edge.from_node_id,
                        target: "n" + from_edge.to_node_id
                    }
                });
                possibleRoots.set("n" + from_edge.to_node_id, false);
            });
        });

        let rootNodeIds = [];

        possibleRoots.forEach((isRoot: boolean, node_id: string) => {
            if (isRoot) {
                rootNodeIds.push(node_id);
            }
        });

        let cy = cytoscape({
            container: document.getElementById('cy'),
            elements: elements,
            style: [ // the stylesheet for the graph
                {
                    selector: 'node[type="External"]',
                    style: {
                        'background-color': '#666',
                        'color': "white",
                        'content': 'data(label)',
                        'shape': 'rectangle',
                        'text-valign': 'center',
                        'text-outline-width': 2,
                        'text-outline-color': '#666',
                        'width': '300',
                    }
                },

                {
                    selector: 'node[type="Dataset"]',
                    style: {
                        'background-color': '#6FB1FC',
                        'color': "white",
                        'content': 'data(label)',
                        'shape': 'rectangle',
                        'text-valign': 'center',
                        'text-outline-width': 2,
                        'text-outline-color': '#6FB1FC',
                        'width': '300',
                    }
                },

                {
                    selector: 'node[type="Process"]',
                    style: {
                        'background-color': '#2ff',
                        'label': 'data(label)',
                        'text-valign': 'center',
                        'shape': 'circle'
                    }
                },

                {
                    selector: 'edge',
                    style: {
                        'width': 3,
                        'line-color': '#ccc',
                        'target-arrow-color': '#ccc',
                        'target-arrow-shape': 'triangle'
                    }
                }
            ],

            //layout: {
            //    name: 'breadthfirst',
            //    spacingFactor: 0.1,
            //    directed: true,
            //    padding: 10
            //}

            layout: {
                name: 'dagre'
            }
        });

        cy.on('tap', 'node', function () {
            console.log("data", this.data());
            let taiga_id = this.data('dataset_id');
            if (taiga_id) {
                let href = "/dataset/show/" + taiga_id

                try { // your browser may block popups
                    window.open(href);
                } catch (e) { // fall back on url change
                    window.location.href = this.data('href');
                }
            }

        });
    }

    render() {
        let navItems: MenuItem[] = [];
        return <div>
            <LeftNav items={navItems}/>
            <div id="main-content">
                <div style={cyStyle} id="cy"></div>
            </div>
        </div>
    }
}