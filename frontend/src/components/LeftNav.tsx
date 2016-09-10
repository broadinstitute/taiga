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
        let items = this.props.items.map(element => {
            return <div>{element.label}</div>;
        });

        console.log("props", this.props);
        console.log("items", items);

        return <div id="left-nav">{ items }</div>
    }
}