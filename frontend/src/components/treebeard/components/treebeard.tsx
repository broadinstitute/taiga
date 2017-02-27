'use strict';

import * as React from 'react';

import { TreeNode } from './node';
import defaultDecorators from './decorators';
import defaultTheme from '../themes/default';
import defaultAnimations from '../themes/animations';

interface TreeBeardProps {
    style?: Object,
    data: Object | Array<any>,
    animations: Object | Boolean,
    onToggle?: Function,
    decorators?: Object,
}

export class TreeBeard extends React.Component<TreeBeardProps, any> {
    constructor(props) {
        super(props);
    }

    static defaultProps: TreeBeardProps = {
        style: defaultTheme,
        data: null,
        animations: defaultAnimations,
        decorators: defaultDecorators
    };

    render() {
        let data = this.props.data;
        // Support Multiple Root Nodes. Its not formally a tree, but its a use-case.
        if (!Array.isArray(data)) {
            data = [data];
        }
        return (
            <ul style={this.props.style.tree.base} ref="treeBase">
                {data.map((node, index) => {
                        return <TreeNode
                            key={node.id || index}
                            node={node}
                            onToggle={this.props.onToggle}
                            animations={this.props.animations}
                            decorators={this.props.decorators}
                            style={this.props.style.tree.node}
                        />
                    }
                )}
            </ul>
        );
    }
}
