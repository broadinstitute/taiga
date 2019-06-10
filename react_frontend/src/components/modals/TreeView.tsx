import * as React from "react";
import {Link} from 'react-router';
import * as Modal from "react-modal";

// import { TreeBeard } from '../treebeard/components/treebeard';
// import * as Treebeard from 'react-treebeard';
// import * as Treebeard from 'react-treebeard';
let Treebeard = require("react-treebeard");

interface TreeViewProps {

}

interface TreeViewState {

}

// Don't forget to modify modalStyles in Upload.tsx if you change the code of modalStyles
const modalStyles : any = {
  content : {
    background: null,
    border: null
  }
};

const data = {
    name: 'root',
    toggled: true,
    children: [
        {
            name: 'parent',
            children: [
                { name: 'child1' },
                { name: 'child2' }
            ]
        },
        {
            name: 'loading parent',
            loading: true,
            children: new Array<any>()
        },
        {
            name: 'parent',
            children: [
                {
                    name: 'nested parent',
                    children: [
                        { name: 'nested child 1' },
                        { name: 'nested child 2' }
                    ]
                }
            ]
        }
    ]
};

export class TreeView extends React.Component<any, any> {
    constructor(props: any) {
        super(props);

        // this.state = {};
        // this.onToggle = (node: any, toggled: any) => this.onToggle(node, toggled);
    }

    onToggle(node: any, toggled: any) {
        console.log('Toggled!');
    }

    render () {
        return <Treebeard.Treebeard
                data={data}
                onToggle={this.onToggle}
            />
    }
}