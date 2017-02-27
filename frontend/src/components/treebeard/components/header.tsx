'use strict';

import * as React from 'react';
import shallowEqual from 'shallowequal';
import deepEqual from 'deep-equal';

import { Container } from './decorators';

interface NodeHeaderProps {
    style: Object,
    decorators: Object,
    animations: Object | Boolean,
    node: Object,
    onClick?: Function
}

export class NodeHeader extends React.Component<NodeHeaderProps, any> {
    constructor(props){
        super(props);
    }
    shouldComponentUpdate(nextProps){
        const props = this.props;
        const nextPropKeys = Object.keys(nextProps);
        for(let i = 0; i < nextPropKeys.length; i++){
            const key = nextPropKeys[i];
            if(key === 'animations'){ continue; }
            const isEqual = shallowEqual(props[key], nextProps[key]);
            if(!isEqual){ return true; }
        }
        return !deepEqual(props.animations, nextProps.animations, { strict: true });
    }
    render(){
        debugger;
        const {style, decorators} = this.props;
        const terminal = !this.props.node.children;
        const active = this.props.node.active;
        const container = [style.link, active ? style.activeLink : null];
        const headerStyles = Object.assign({ container }, this.props.style);
        return (
            <Container
                style={headerStyles}
                decorators={decorators}
                terminal={terminal}
                onClick={this.props.onClick}
                animations={this.props.animations}
                node={this.props.node}
            />
        );
    }
}
