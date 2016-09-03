import * as React from "react";

import { LeftNav } from "./LeftNav"

import { Link } from 'react-router';

import * as Folder from "../models/models"
import { TaigaApi } from "../models/api.ts"

export interface FolderViewProps {
    params : any
}

export interface FolderViewState {
    folder? : Folder.Folder
}

const static_folder : Folder.Folder = {
    id: "x",
    name: "Child Dir",
    type: Folder.Folder.TypeEnum.Folder,
    parents: [ {id: "home-id", name: "Home"} ],
    entries: [ 
        {id: "a-id", 
        name: "A Folder", 
        type: Folder.FolderEntries.TypeEnum.Folder,
        creationDate: "2009",
        creator: {name: "joe", id: "joe-id"} },

        {id: "B-id", 
        name: "B Dataset", 
        type: Folder.FolderEntries.TypeEnum.Dataset,
        creationDate: "2011",
        creator: {name: "joe", id: "joe-id"} },

        {id: "C-id", 
        name: "C Dataset Version", 
        type: Folder.FolderEntries.TypeEnum.DatasetVersion,
        creationDate: "2012",
        creator: {name: "joe", id: "joe-id"} },
         ]    
};

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
        
        console.log("componentDidMount");
        tapi.get_folder(this.props.params.folderId).then(folder => {
            this.setState({folder: folder})
            console.log("complete");
            }
        );
    }

    render() {
        console.log("folderId in render", this.props.params.folderId);
        if(! this.state) {
            return <div>Loading...</div>
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
                <td><Link to={"/app/folder/"+e.id}>{e.name}</Link></td>
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

        return (
                <div>
                <LeftNav/>
                <h1>{folder.name}</h1>
                <p>Parents: {parent_links}</p>
                <table>
                    <thead>
                        <tr>
                            <th></th>
                            <th>Name</th>
                            <th>Date</th>
                            <th>Creator</th>
                        </tr>
                    </thead>
                    <tbody>
                        {folder_rows}
                    </tbody>
                </table>
                <h2>Datasets</h2>
                <table>
                    <thead>
                        <tr>
                            <th></th>
                            <th>Name</th>
                            <th>Date</th>
                            <th>Creator</th>
                        </tr>
                    </thead>
                    <tbody>
                        {other_rows}
                    </tbody>
                </table>
                </div>
            )
        }
    }


