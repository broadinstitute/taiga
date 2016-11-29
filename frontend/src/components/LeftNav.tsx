import * as React from "react";

export interface MenuItem {
    label : string;
    action : () => void;
}

export interface LeftNavProps { 
    items : MenuItem[];
}

export class LeftNav extends React.Component<LeftNavProps, {}> {
    render() {
        let items = this.props.items.map((element, index) => {
            return <li key={index} onClick={ element.action }>{element.label}</li>;
        });

        return <div id="left-nav"><ul>{ items }</ul></div>
    }
}