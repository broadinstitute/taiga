import * as React from "react";

import { LeftNav, MenuItem } from "./LeftNav"

import { Link } from 'react-router';

import * as Folder from "../models/models"
import { TaigaApi } from "../models/api.ts"
import { AffixWrapper } from "./affix.tsx"

export interface FolderViewProps {
    params : any
}

export interface FolderViewState {
    folder? : Folder.Folder
}

export class Conditional extends React.Component<any, any> {
    render() {
        if(this.props.show) {
            return <div>{this.props.children}</div>
        } else {
            return null;
        }
    }
}

export class FolderView extends React.Component<FolderViewProps, FolderViewState> {
    static contextTypes = {
        tapi: React.PropTypes.object
    };

    componentDidUpdate (prevProps : FolderViewProps) {
        // respond to parameter change in scenario 3
        let oldId = prevProps.params.folderId
        let newId = this.props.params.folderId
        if (newId !== oldId)
            this.doFetch();
    }

    componentDidMount() {
        this.doFetch();
    }

    doFetch() {
        let tapi : TaigaApi = (this.context as any).tapi;
        
        console.log("FolderView: componentDidMount");
        tapi.get_folder(this.props.params.folderId).then(folder => {
            this.setState({folder: folder})
            console.log("FolderView: complete");
            }
        );
    }

    selectRow(i : number) {
        // let newState : FolderViewState = update(self.state, {selections: {"$set": i}});
        // this.setState(newState);
    }

    render() {
        console.log("folderId in render", this.props.params.folderId);
        if(! this.state) {
            return <div>
                <LeftNav items={[]}/>
                <div id="main-content"/>
                </div>
        }
        var folder : Folder.Folder = this.state.folder;

        var parent_links = folder.parents.map( (p : Folder.NamedId) => {
            return <Link to={"/app/folder/"+p.id}>{p.name}</Link>
        });

        var subfolders : Folder.FolderEntries[] = [];
        var others :Folder.FolderEntries[] = [];

        folder.entries.forEach( (e : Folder.FolderEntries) => {
            if(e.type == Folder.FolderEntries.TypeEnum.Folder) {
                subfolders.push(e);
            } else {
                others.push(e);
            }
        })

        var folder_rows = subfolders.map(e => {
            return <tr>
                <td><input type="checkbox"/></td>
                <td><Link to={"/app/folder/"+e.id}><div className="folder-icon"/>{e.name}</Link></td>
                <td>{e.creationDate}</td>
                <td>{e.creator.name}</td>
            </tr>
        });

        var other_rows = others.map(e => {
            var link : any;

            if(e.type == Folder.FolderEntries.TypeEnum.DatasetVersion) {
                link = <Link to={"/app/dataset/"+e.id}>{e.name}</Link>
            } else {
                link = e.name;
            }

            return <tr>
                <td><input type="checkbox"/></td>
                <td>{link}</td>
                <td>{e.creationDate}</td>
                <td>{e.creator.name}</td>
            </tr>
        });
        
        console.log(this.props.params);

        let navItems : MenuItem[] = [];
        let selectionCount = 0;

        if(selectionCount == 0) {
            navItems = navItems.concat([
                {label: "Edit name", action: () => {} },
                {label: "Edit description", action: () => {} },
                {label: "Create a subfolder", action: () => {} },
                {label: "Upload dataset", action: () => {} }
            ])
        } else {
            navItems.push({label: "Move to trash", action: () => {} })
            navItems.push({label: "Move to...", action: () => {} })
            navItems.push({label: "Copy to...", action: () => {} })
        }

        return (
                <div>
                <LeftNav items={navItems}/>
                <div id="main-content">
                    <h1>{folder.name}</h1>

                    <Conditional show={parent_links.length > 0}>
                        <p>Parents: {parent_links}</p>
                    </Conditional>

                    <table className="table">
                        <thead>
                            <tr>
                                <th className="select-column"></th>
                                <th>Name</th>
                                <th>Date</th>
                                <th>Creator</th>
                            </tr>
                        </thead>
                        <tbody>
                            {folder_rows}
                            {other_rows}
                        </tbody>
                    </table>
                </div>
                </div>
            )
        }
    }


