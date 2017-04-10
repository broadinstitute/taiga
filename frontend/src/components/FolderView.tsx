import * as React from "react";
import {Link} from 'react-router';
import * as update from 'immutability-helper';

import {LeftNav, MenuItem} from "./LeftNav";
import * as Folder from "../models/models";
import {TaigaApi} from "../models/api";

import * as Dialogs from "./Dialogs";
import * as Upload from "./modals/Upload";
import {TreeView} from "./modals/TreeView";

import {toLocalDateString} from "../utilities/formats";
import {relativePath} from "../utilities/route";
import {LoadingOverlay} from "../utilities/loading";

import {Glyphicon} from "react-bootstrap";
import {Dataset} from "../models/models";
import {DatasetVersion} from "../models/models";
import {isUndefined} from "util";
import {DatasetFullDatasetVersions} from "../models/models";

export interface FolderViewProps {
    params: any
}

export interface FolderViewState {
    folder?: Folder.Folder;
    datasetLastDatasetVersion?: {[dataset_id: string]: Folder.DatasetVersion}
    datasetsVersion?: {[datasetVersion_id: string]: Folder.DatasetVersion}
    showEditName?: boolean;
    showEditDescription?: boolean;
    showUploadDataset?: boolean;
    showCreateFolder?: boolean;
    error?: string;
    selection?: any;

    callbackIntoFolderAction?: Function;
    actionName?: string;

    showInputFolderId?: boolean;
    inputFolderIdActionDescription?: string;

    actionIntoFolderValidation?: string;
    actionIntoFolderHelp?: string;

    loading?: boolean;
}

export class Conditional extends React.Component<any, any> {
    render() {
        if (this.props.show) {
            return <div>{this.props.children}</div>
        } else {
            return null;
        }
    }
}

let tapi: TaigaApi = null;
let currentUser: string = null;

export class FolderView extends React.Component<FolderViewProps, FolderViewState> {
    static contextTypes = {
        tapi: React.PropTypes.object,
        currentUser: React.PropTypes.string
    };

    componentDidUpdate(prevProps: FolderViewProps) {
        console.log("We updated folderView");
        // respond to parameter change in scenario 3
        let oldId = prevProps.params.folderId;
        let newId = this.props.params.folderId;
        if (newId !== oldId)
            this.doFetch();
    }

    componentDidMount() {
        tapi = (this.context as any).tapi;
        currentUser = (this.context as any).currentUser;
        this.doFetch();
    }

    doFetch() {
        console.log("FolderView: componentDidMount");
        this.setState({
            loading: true
        });
        // TODO: Revisit the way we handle the Dataset/DatasetVersion throughout this View
        let datasetsLatestDv: {[dataset_id: string]: Folder.DatasetVersion} = {};
        let datasetsVersion: {[datasetVersion_id: string]: Folder.DatasetVersion} = {};
        let _folder: Folder.Folder = null;
        return tapi.get_folder(this.props.params.folderId).then(folder => {
                _folder = folder;
                console.log("FolderView: complete");
                return folder.entries
            }
        ).then((entries: Array<Folder.FolderEntries>) => {
            // We want to ask the server a bulk of the datasets and the datasetVersions
            let datasetIds = entries.filter((entry: Folder.FolderEntries) => {
                return entry.type == Folder.FolderEntries.TypeEnum.Dataset;
            }).map((datasetEntry: Folder.FolderEntries) => {
                return datasetEntry.id;
            });
            let datasetVersionIds = entries.filter((entry: Folder.FolderEntries) => {
                return entry.type == Folder.FolderEntries.TypeEnum.DatasetVersion;
            }).map((datasetVersionEntry: Folder.FolderEntries) => {
                return datasetVersionEntry.id;
            });

            // First we ask the dataset bulk

            return tapi.get_datasets(datasetIds).then((arrayDatasets: Array<DatasetFullDatasetVersions>) => {
                arrayDatasets.forEach((dataset: DatasetFullDatasetVersions) => {
                    // We get the latest datasetVersion
                    let latestDatasetVersion: DatasetVersion = dataset.versions[0];
                    dataset.versions.forEach((datasetVersion: DatasetVersion) => {
                        if (latestDatasetVersion.version < datasetVersion.version) {
                            latestDatasetVersion = datasetVersion;
                        }
                    });
                    datasetsLatestDv[dataset.id] = latestDatasetVersion;
                });
            }).then(() => {
                // Then we ask the datasetVersion bulk
                console.log("Success to get the datasets!");
                return tapi.get_datasetVersions(datasetVersionIds).then((arrayDatasetVersions: Array<DatasetVersion>) => {
                    arrayDatasetVersions.forEach((datasetVersion: DatasetVersion) => {
                        datasetsVersion[datasetVersion.id] = datasetVersion
                    });
                    // this.setState({
                    //     loading: false
                    // });
                });
            });


            // let all_dataset_versions: Array<Promise<void>> = null;
            // all_dataset_versions = entries.map((entry: Folder.FolderEntries) => {
            //     if (entry.type == Folder.FolderEntries.TypeEnum.Dataset) {
            //
            //         return tapi.get_dataset_version_last(entry.id).then((datasetVersion: Folder.DatasetVersion) => {
            //             datasetsLatestDv[entry.id] = datasetVersion;
            //         });
            //     }
            //     else if (entry.type == Folder.FolderEntries.TypeEnum.DatasetVersion) {
            //         return tapi.get_dataset_version(entry.id).then((datasetVersion: Folder.DatasetVersion) => {
            //             datasetsVersion[datasetVersion.id] = datasetVersion
            //         });
            //     }
            // });
            // return Promise.all(all_dataset_versions);
        }).then(() => {
            console.log("We reset the states");
            this.setState({
                folder: _folder,
                selection: new Array<string>(),
                datasetLastDatasetVersion: datasetsLatestDv,
                datasetsVersion: datasetsVersion,
                loading: false
            });
        });
    }

    selectRow(select_key: string) {
        const original_selection: any = this.state.selection;

        let updated_selection: Array<string>;

        let index = original_selection.indexOf(select_key);
        if (index != -1) {
            updated_selection = update(original_selection, {$splice: [[index, 1]]});
        }
        else {
            updated_selection = update(original_selection, {$push: [select_key]});
        }

        this.setState({selection: updated_selection});
    }

    updateName(name: string) {
        tapi.update_folder_name(this.state.folder.id, name).then(() => {
            return this.doFetch()
        })
    }

    updateDescription(description: string) {
        tapi.update_folder_description(this.state.folder.id, description).then(() => {
            return this.doFetch()
        })
    }

    createFolder(name: string, description: string) {
        const current_folder_id: string = this.state.folder.id;
        // TODO: To fetch instead the current user once we have the authentication
        const current_creator_id: string = currentUser;

        tapi.create_folder(current_folder_id, current_creator_id, name, description).then(() => {
            return this.doFetch();
        });
    }

    moveToTrash() {
        // move_to_folder takes the entryIds, the current folder id and the target folder id as parameters
        // If the target folder is null, the backend will move this symbolic link to the trash
        tapi.move_to_folder(this.state.selection, this.state.folder.id, null).then(() => {
            return this.doFetch();
        }).catch((err: any) => {
            console.log("Error when moving to trash :/ : " + err);
        });
    }

    openActionTo(actionName: string) {
        // TODO: Change the string telling the action to an enum, like in the backend

        let actionDescription = "";

        if (actionName == "move") {
            actionDescription = "move the selected file(s) into it";
        }
        else if (actionName == "copy") {
            actionDescription = "copy the selected file(s) into it";
        }

        this.setState({
            callbackIntoFolderAction: (folderId) => this.actionIntoFolder(folderId),
            actionName: actionName,
            inputFolderIdActionDescription: actionDescription,
            showInputFolderId: true,
            actionIntoFolderValidation: null,
            actionIntoFolderHelp: null
        });
    }

    actionIntoFolder(folderId: string) {
        // TODO: Call to move the files

        // TODO: Find the right way to put the function in a variable but not carry this into tapi
        if (this.state.actionName == "move") {
            tapi.move_to_folder(this.state.selection, this.state.folder.id, folderId).then(() => this.afterAction());
        }
        else if (this.state.actionName == "copy") {
            tapi.copy_to_folder(this.state.selection, folderId).then(() => this.afterAction());
        }
    }

    afterAction() {
        // TODO: We don't need to do that if we are copying
        this.doFetch().then(() => {
            this.setState({
                showInputFolderId: false
            });
        }).catch((err) => {
            console.log(err);

            // If we receive 422 error
            if (err.message == "UNPROCESSABLE ENTITY") {
                let err_message_user = "Folder id is not valid. Please check it and retry :)";
                this.setState({
                    actionIntoFolderValidation: 'error',
                    actionIntoFolderHelp: err_message_user
                });
            }
        })
    }

    // Upload
    filesUploadedAndConverted(sid: string, datasetName: string, datasetDescription: string) {
        // We ask to create the dataset
        return tapi.create_dataset(sid,
            datasetName,
            datasetDescription,
            this.state.folder.id
        ).then((dataset_id) => {
            // We fetch the datasetVersion of the newly created dataset and change the state of it
            return tapi.get_dataset_version_first(dataset_id).then((newDatasetVersion) => {
                this.doFetch();
                return Promise.resolve(newDatasetVersion);
            });
        }).catch((err: any) => {
            console.log(err);
            return Promise.reject(err);
        });
    }

    getMostRecentDateEntry(entry: Folder.FolderEntries) {
        if (entry.type == Folder.FolderEntries.TypeEnum.Folder) {
            return entry.creation_date;
        }
        else if (entry.type == Folder.FolderEntries.TypeEnum.Dataset) {
            let latestDatasetVersion = this.state.datasetLastDatasetVersion[entry.id];
            return latestDatasetVersion.creation_date;
        }
        else if (entry.type == Folder.FolderEntries.TypeEnum.DatasetVersion) {
            return entry.creation_date;
        }
    }

    render() {
        console.log("folderId in render", this.props.params.folderId);
        if (!this.state) {
            return <div>
                <LeftNav items={[]}/>
                <div id="main-content"/>
            </div>
        } else if (this.state.error) {
            return <div>
                <LeftNav items={[]}/>
                <div id="main-content">
                    An error occurred: {this.state.error}
                </div>
            </div>
        }
        var folder: Folder.Folder = this.state.folder;

        var parent_links = folder.parents.map((p: Folder.NamedId, index: number) => {
            return <Link key={index} to={relativePath("folder/"+p.id)}>{p.name}</Link>
        });

        let entriesOutput: Array<any> = [];
        var subfolders: Folder.FolderEntries[] = [];
        var others: Folder.FolderEntries[] = [];


        let sortedEntries = folder.entries.sort((elementA, elementB) => {
            // Sorting by descending order
            let keyA = new Date(this.getMostRecentDateEntry(elementA));
            let keyB = new Date(this.getMostRecentDateEntry(elementB));

            if (keyA > keyB) return -1;
            if (keyA < keyB) return 1;
            return 0;
        });

        sortedEntries.forEach((e: Folder.FolderEntries, index: number) => {
            if (e.type == Folder.FolderEntries.TypeEnum.Folder) {
                entriesOutput.push(
                    <tr key={e.id}>
                        <td><input type="checkbox" checked={ this.state.selection.includes(e.id) }
                                   onChange={ () => {this.selectRow(e.id)} }/></td>
                        <td><Glyphicon glyph="glyphicon glyphicon-folder-close"/>
                            <span> </span>
                            <Link key={index} to={relativePath("folder/"+e.id)}>
                                {e.name}
                            </Link>
                        </td>
                        <td>{toLocalDateString(e.creation_date)}</td>
                        <td>Folder</td>
                        <td>{e.creator.name}</td>
                    </tr>
                );
            } else {
                var link: any;
                let entryType: any;
                let creation_date: string = toLocalDateString(e.creation_date);

                if (e.type == Folder.FolderEntries.TypeEnum.DatasetVersion) {
                    entryType = 'Dataset Version';
                    let full_datasetVersion: Folder.DatasetVersion = this.state.datasetsVersion[e.id];
                    // Since we don't have the id of the dataset, we need to ask the api for it
                    link =
                        <span>
                            <Glyphicon glyph="glyphicon glyphicon-file"/>
                            <span> </span>
                            <Link key={index} to={relativePath("dataset/"+full_datasetVersion.dataset_id+"/"+e.id)}>
                                {e.name}
                            </Link>
                        </span>
                } else if (e.type == Folder.FolderEntries.TypeEnum.Dataset) {
                    entryType = 'Dataset';
                    // TODO: Be careful about this add, not sure if we should access Dataset data like this
                    // TODO: We need to get the latest datasetVersion from this dataset
                    let latestDatasetVersion = this.state.datasetLastDatasetVersion[e.id];
                    link =
                        <span>
                        <Glyphicon glyph="glyphicon glyphicon-inbox"/>
                        <span> </span>
                        <Link key={index} to={relativePath("dataset/"+e.id+"/"+latestDatasetVersion.id)}>{e.name}</Link>
                    </span>;
                    creation_date = toLocalDateString(latestDatasetVersion.creation_date);
                }
                else {
                    link = e.name;
                }

                entriesOutput.push(
                    <tr key={e.id}>
                        <td><input type="checkbox" checked={ this.state.selection.includes(e.id) }
                                   onChange={ () => {this.selectRow(e.id)} }/></td>
                        <td>{link}</td>
                        <td>{creation_date}</td>
                        <td>{entryType}</td>
                        <td>{e.creator.name}</td>
                    </tr>
                );
            }
        });

        // var folder_rows = subfolders.map((e, index) => {
        //     let select_key = e.id;
        //     return <tr key={e.id}>
        //         <td><input type="checkbox" checked={ this.state.selection.includes(select_key) }
        //                    onChange={ () => {this.selectRow(select_key)} }/></td>
        //         <td><Glyphicon glyph="glyphicon glyphicon-folder-close"/>
        //             <span> </span>
        //             <Link key={index} to={relativePath("folder/"+e.id)}>
        //                 {e.name}
        //             </Link>
        //         </td>
        //         <td>{toLocalDateString(e.creation_date)}</td>
        //         <td>Folder</td>
        //         <td>{e.creator.name}</td>
        //     </tr>
        // });
        //
        // var other_rows = others.map((e, index) => {
        //     var link: any;
        //     let entryType: any;
        //     let creation_date: string = toLocalDateString(e.creation_date);
        //
        //     if (e.type == Folder.FolderEntries.TypeEnum.DatasetVersion) {
        //         entryType = 'Dataset Version';
        //         let full_datasetVersion: Folder.DatasetVersion = this.state.datasetsVersion[e.id];
        //         // Since we don't have the id of the dataset, we need to ask the api for it
        //         link =
        //             <span>
        //                     <Glyphicon glyph="glyphicon glyphicon-file"/>
        //                     <span> </span>
        //                     <Link key={index} to={relativePath("dataset/"+full_datasetVersion.dataset_id+"/"+e.id)}>
        //                         {e.name}
        //                     </Link>
        //                 </span>
        //     } else if (e.type == Folder.FolderEntries.TypeEnum.Dataset) {
        //         entryType = 'Dataset';
        //         // TODO: Be careful about this add, not sure if we should access Dataset data like this
        //         // TODO: We need to get the latest datasetVersion from this dataset
        //         let latestDatasetVersion = this.state.datasetLastDatasetVersion[e.id];
        //         link =
        //             <span>
        //                 <Glyphicon glyph="glyphicon glyphicon-inbox"/>
        //                 <span> </span>
        //                 <Link key={index} to={relativePath("dataset/"+e.id+"/"+latestDatasetVersion.id)}>{e.name}</Link>
        //             </span>;
        //         creation_date = toLocalDateString(latestDatasetVersion.creation_date);
        //     }
        //     else {
        //         link = e.name;
        //     }
        //
        //     let select_key = e.id;
        //     return <tr key={e.id}>
        //         <td><input type="checkbox" checked={ this.state.selection.includes(select_key) }
        //                    onChange={ () => {this.selectRow(select_key)} }/></td>
        //         <td>{link}</td>
        //         <td>{creation_date}</td>
        //         <td>{entryType}</td>
        //         <td>{e.creator.name}</td>
        //     </tr>
        // });

        console.log(this.props.params);

        let navItems: MenuItem[] = [];
        let selectionCount = this.state.selection.length;

        if (selectionCount == 0) {
            navItems = navItems.concat([
                {
                    label: "Edit name", action: () => {
                    this.setState({showEditName: true})
                }
                },
                {
                    label: "Edit description", action: () => {
                    this.setState({showEditDescription: true})
                }
                },
                {
                    label: "Create a subfolder", action: () => {
                    this.setState({showCreateFolder: true})
                }
                },
                {
                    label: "Upload dataset", action: () => {
                    this.setState({showUploadDataset: true})
                }
                }
            ])
        } else {
            navItems.push({
                label: "Move to trash", action: () => this.moveToTrash()
            })
            navItems.push({
                label: "Move to...", action: () => {
                    this.openActionTo("move");
                }
            })
            navItems.push({
                label: "Copy to...", action: () => {
                    this.openActionTo("copy");
                }
            })
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
                    } }/>

                    <Dialogs.EditDescription
                        initialValue={ this.state.folder.description }
                        isVisible={this.state.showEditDescription}
                        cancel={ () => { this.setState({showEditDescription: false})} }
                        save={ (description:string) => { 
                            this.setState({showEditDescription: false}) 
                            this.updateDescription(description);
                        }}/>

                    <Upload.UploadDataset
                        isVisible={this.state.showUploadDataset}
                        cancel={ () => { this.setState({showUploadDataset: false}) } }

                        onFileUploadedAndConverted={ (sid: string, name: string , description: string) =>
                            this.filesUploadedAndConverted(sid, name, description) }
                        currentFolderId={this.state.folder.id}
                        title="New Dataset"
                    />

                    <Dialogs.CreateFolder
                        isVisible={this.state.showCreateFolder}
                        cancel={ () => { this.setState({showCreateFolder: false}) }}
                        save={ (name, description) => {
                            this.setState({showCreateFolder: false});
                            this.createFolder(name, description);
                        }}
                    />

                    <Dialogs.InputFolderId
                        actionDescription={ this.state.inputFolderIdActionDescription }
                        isVisible={ this.state.showInputFolderId }
                        cancel={ () => { this.setState({showInputFolderId: false}) }}
                        save={ (folderId) => { this.state.callbackIntoFolderAction(folderId) }}
                    />

                    <h1>{folder.name}</h1>

                    <Conditional show={parent_links.length > 0}>
                        <p>Parents: {parent_links}</p>
                    </Conditional>

                    { Dialogs.renderDescription(this.state.folder.description) }

                    <table className="table">
                        <thead>
                        <tr>
                            <th className="select-column"></th>
                            <th>Name</th>
                            <th>Date</th>
                            <th>Type</th>
                            <th>Creator</th>
                        </tr>
                        </thead>
                        <tbody>

                        {entriesOutput}
                        {/*{folder_rows}*/}
                        {/*{other_rows}*/}
                        </tbody>
                    </table>
                    {this.state.loading && <LoadingOverlay></LoadingOverlay>}
                </div>
            </div>
        )
    }
}
