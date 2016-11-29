import * as React from "react";

export interface MenuItem {
    label : string;
    action : () => void;
    id: number;
}

export interface LeftNavProps { 
    items : MenuItem[];
}

export class LeftNav extends React.Component<LeftNavProps, {}> {
    render() {
        let items = this.props.items.map(element => {
            return <li key={element.id} onClick={ element.action }>{element.label}</li>;
        });

        return <div id="left-nav"><ul>{ items }</ul></div>
    }
}