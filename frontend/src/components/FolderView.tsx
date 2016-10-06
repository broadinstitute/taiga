import * as React from "react";


import { LeftNav, MenuItem } from "./LeftNav"

import { Link } from 'react-router';

import * as Folder from "../models/models"
import { TaigaApi } from "../models/api.ts"

import * as Dialogs from "./Dialogs"

export interface FolderViewProps {
    params : any
}

export interface FolderViewState {
    folder? : Folder.Folder;
    showEditName? : boolean;
    showEditDescription? : boolean;
    error? : string;
    selection? : any;
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
            this.setState({folder: folder, selection: {}});
            console.log("FolderView: complete");
            }
        );
    }

    selectRow(select_key : string) {
        var s : any = this.state.selection;
        if(!s) {
            s = {};
        } else {
            // ugh, there's got to be a better way.  Make a copy
            // of the selection so we don't mutate the original
            s = JSON.parse(JSON.stringify(s));            
        }

        let isSetAfterToggle = !(s[select_key]);
        if (isSetAfterToggle) {
            s[select_key] = true; 
        } else {
            delete s[select_key];
        }

        this.setState({selection: s});
    }

    updateName(name : string) {
        let tapi : TaigaApi = (this.context as any).tapi;

        tapi.update_folder_name(this.state.folder.id, name).then( () => {
            return this.doFetch()
        } )        
    }

    updateDescription(description : string) {
        let tapi : TaigaApi = (this.context as any).tapi;

        tapi.update_folder_description(this.state.folder.id, description).then( () => {
            return this.doFetch()
        } )        
    }

    render() {
        console.log("folderId in render", this.props.params.folderId);
        if(! this.state) {
            return <div>
                    <LeftNav items={[]}/>
                    <div id="main-content"/>
                </div>
        } else if(this.state.error) {
            return <div>
                    <LeftNav items={[]}/>
                    <div id="main-content">
                        An error occurred: {this.state.error}
                    </div>
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
            let select_key = "folder."+e.id;
            return <tr>
                <td><input type="checkbox" value={ this.state.selection[select_key] } onChange={ () => {this.selectRow(select_key)} }/></td>
                <td><Link to={"/app/folder/"+e.id}><div className="folder-icon"/>{e.name}</Link></td>
                <td>{e.creation_date}</td>
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

            let select_key = "dataset."+e.id;

            return <tr>
                <td><input type="checkbox" value={ this.state.selection[select_key] } onChange={ () => {this.selectRow(select_key)} }/></td>
                <td>{link}</td>
                <td>{e.creation_date}</td>
                <td>{e.creator.name}</td>
            </tr>
        });
        
        console.log(this.props.params);

        let navItems : MenuItem[] = [];
        let selectionCount = Object.keys(this.state.selection).length;

        if(selectionCount == 0) {
            navItems = navItems.concat([
                {label: "Edit name", action: () => {this.setState({ showEditName : true })} },
                {label: "Edit description", action: () => {this.setState({ showEditDescription : true })} },
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
                    <Dialogs.EditName isVisible={this.state.showEditName}
                        initialValue={ this.state.folder.name } 
                        cancel={ () => { this.setState({showEditName: false})} }
                        save={ (name:string) => {
                            console.log("Save name: "+name); 
                            this.setState({showEditName: false})
                            this.updateName(name);    
                    } } />
                            
                    <Dialogs.EditDescription 
                        initialValue={ this.state.folder.description } 
                        isVisible={this.state.showEditDescription}
                        cancel={ () => { this.setState({showEditDescription: false})} }
                        save={ (description:string) => { 
                            this.setState({showEditDescription: false}) 
                            this.updateDescription(description);
                        }} />
                    <h1>{folder.name}</h1>

                    <Conditional show={parent_links.length > 0}>
                        <p>Parents: {parent_links}</p>
                    </Conditional>

                    { Dialogs.renderDescription( this.state.folder.description ) }

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


