import * as React from "react";
import {Link} from 'react-router';
import * as Modal from "react-modal";

import * as TreeBeard from 'react-treebeard';

interface TreeViewProps {

}

interface TreeViewState {

}

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
        return <TreeBeard
            data={data}
            onToggle={this.onToggle}
        />
    }
}