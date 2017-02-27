'use strict';

import * as React from 'react';
import Radium from 'radium';
import VelocityComponent from 'velocity-react';

const Loading = (props) => {
    return (
        <div style={props.style}>
            loading...
        </div>
    );
};

const Toggle = (props) => {
    const style = props.style;
    const height = style.height;
    const width = style.width;
    let midHeight = height * 0.5;
    let points = `0,0 0,${height} ${width},${midHeight}`;
    return (
        <div style={style.base}>
            <div style={style.wrapper}>
                <svg height={height} width={width}>
                    <polygon
                        points={points}
                        style={style.arrow}
                    />
                </svg>
            </div>
        </div>
    );
};

const Header = (props) => {
    const style = props.style;
    return (
        <div style={style.base}>
            <div style={style.title}>
                {props.node.name}
            </div>
        </div>
    );
};

interface ContainerProps {
    style: Object,
    decorators: Object,
    terminal: Boolean,
    onClick: any,
    animations: Object | Boolean,
    node: Object
}

@Radium
export class Container extends React.Component<ContainerProps, any> {
    constructor(props){
        super(props);
    }
    render(){
        const {style, decorators, terminal, onClick, node} = this.props;
        return (
            <div
                ref="clickable"
                onClick={onClick}
                style={style.container}>
                {/*{ !terminal ? this.renderToggle() : null }*/}
                <decorators.Header
                    node={node}
                    style={style.header}
                />
            </div>
        );
    }
    renderToggle(){
        const animations: Animations = this.props.animations;
        if(!animations){ return this.renderToggleDecorator(); }
        return (
            <VelocityComponent ref="velocity"
                duration={animations.toggle.duration}
                animation={animations.toggle.animation}>
                {this.renderToggleDecorator()}
            </VelocityComponent>
        );
    }
    renderToggleDecorator(){
        const {style, decorators} = this.props;
        return (<decorators.Toggle style={style.toggle}/>);
    }
}

export default {
    Loading,
    Toggle,
    Header,
    Container
};

