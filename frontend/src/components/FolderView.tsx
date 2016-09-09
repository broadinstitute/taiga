import * as React from "react";

import { LeftNav } from "./LeftNav"

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
                <AffixWrapper className="left-panel" offset={30}>
                    <div>LeftNav</div>
                </AffixWrapper>
                <div>
                <h1>{folder.name}</h1>

                <Conditional show={parent_links.length > 0}>
                    <p>Parents: {parent_links}</p>
                </Conditional>

                <Conditional show={folder_rows.length > 0}>
                    <h2>Folders</h2>
                    <table className="table">
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
                </Conditional>

                <Conditional show={other_rows.length > 0}>
                    <h2>Datasets</h2>
                    <table className="table">
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
                </Conditional>
                </div>
                </div>
            )
        }
    }


