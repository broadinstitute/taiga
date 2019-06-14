import * as React from "react";
import {Link} from 'react-router';
import * as update from 'immutability-helper';

import {LeftNav, MenuItem} from "./LeftNav";
import * as Folder from "../models/models";
import {TaigaApi} from "../models/api";

import * as Dialogs from "./Dialogs";
import * as Upload from "./modals/Upload";
import {EntryUsersPermissions} from "./modals/EntryUsersPermissions";
import {NotFound} from "./NotFound";
import {SearchInput} from "./Search";

import {toLocalDateString} from "../utilities/formats";
import {relativePath} from "../utilities/route";
import {LoadingOverlay} from "../utilities/loading";

import {Glyphicon, Form, FormGroup, ControlLabel, FormControl, Button} from "react-bootstrap";
import {Grid, Row, Col} from "react-bootstrap";
import {BootstrapTable, TableHeaderColumn, SelectRow, SelectRowMode, Options, SortOrder, CellEditClickMode, CellEdit} from "react-bootstrap-table";
import {Dataset, Entry, FolderEntries, NamedId} from "../models/models";
import {DatasetVersion} from "../models/models";
import {isUndefined} from "util";
import {DatasetFullDatasetVersions, BootstrapTableFolderEntry} from "../models/models";
// import int = DataPipeline.int;
import {debug} from "util";
import {User} from "../models/models";
import {AccessLog} from "../models/models";
import {ShareEntries} from "./Dialogs";

export interface FolderViewProps {
    params: any;
}

const tableEntriesStyle: any = {
    margin: "initial"
};

export interface FolderViewState {
    folder?: Folder.Folder;
    datasetLastDatasetVersion?: {[dataset_id: string]: Folder.DatasetVersion}
    datasetsVersion?: {[datasetVersion_id: string]: Folder.DatasetVersion}

    showEditName?: boolean;
    showEditDescription?: boolean;
    showUploadDataset?: boolean;
    showCreateFolder?: boolean;
    showEditPermissions?: boolean;
    showShareFolder?: boolean;

    sharingEntries?: Array<Entry>;

    error?: string;
    selection?: any;

    callbackIntoFolderAction?: Function;
    actionName?: string;

    showInputFolderId?: boolean;
    initFolderId?: string;
    inputFolderIdActionDescription?: string;

    actionIntoFolderValidation?: string;
    actionIntoFolderHelp?: string;

    loading?: boolean;

    currentUser?: User;

    searchQuery?: string;
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
        currentUser: React.PropTypes.string,
    };

    constructor(props: any) {
        super(props);
    }

    private bootstrapTable: any;

    componentDidUpdate(prevProps: FolderViewProps) {
        // respond to parameter change in scenario 3
        let oldId = prevProps.params.folderId;
        let newId = this.props.params.folderId;
        if (newId !== oldId) {
            this.doFetch().then(() => {
                this.logAccess();
            });

            // Clean selected
            this.bootstrapTable.cleanSelected();
        }
    }

    componentDidMount() {
        tapi = (this.context as any).tapi;
        currentUser = (this.context as any).currentUser;
        this.setState({
           searchQuery: ""
        });

        this.doFetch().then(() => {
            this.logAccess();
        });

        tapi.get_user().then(user => {
            this.setState({currentUser: user});
        });
    }

    doFetch() {
        this.setState({
            loading: true
        });
        // TODO: Revisit the way we handle the Dataset/DatasetVersion throughout this View
        let datasetsLatestDv: {[dataset_id: string]: Folder.DatasetVersion} = {};
        let datasetsVersion: {[datasetVersion_id: string]: Folder.DatasetVersion} = {};
        let _folder: Folder.Folder = null;

        return tapi.get_folder(this.props.params.folderId).then(folder => {
                _folder = new Folder.Folder(folder);
                this.setState({sharingEntries: [_folder]});
                return folder.entries;
            }
        ).then((entries: Array<Folder.FolderEntries>) => {
            // We want to ask the server a bulk of the datasets and the datasetVersions
            let datasetIds = entries.filter((entry: Folder.FolderEntries) => {
                return (entry.type === Folder.FolderEntriesTypeEnum.Dataset) || (entry.type === Folder.FolderEntriesTypeEnum.VirtualDataset);
            }).map((datasetEntry: Folder.FolderEntries) => {
                return datasetEntry.id;
            });
            let datasetVersionIds = entries.filter((entry: Folder.FolderEntries) => {
                return (entry.type === Folder.FolderEntriesTypeEnum.DatasetVersion) || (entry.type === Folder.FolderEntriesTypeEnum.VirtualDatasetVersion);
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
                return tapi.get_datasetVersions(datasetVersionIds).then((arrayDatasetVersions: Array<DatasetVersion>) => {
                    arrayDatasetVersions.forEach((datasetVersion: DatasetVersion) => {
                        datasetsVersion[datasetVersion.id] = datasetVersion
                    });
                });
            });
        }).then(() => {
            this.setState({
                folder: _folder,
                selection: new Array<string>(),
                datasetLastDatasetVersion: datasetsLatestDv,
                datasetsVersion: datasetsVersion,
                loading: false
            });
        }).catch((error) => {
            this.setState({
                error: error.message
            });
            console.log("Error: " + error.stack);
        });
    }

    // TODO: Refactor logAccess in an util or in RecentlyViewed class
    logAccess() {
        return tapi.create_or_update_entry_access_log(this.state.folder.id).then(() => {
        });
    }

    updateName(name: string) {
        tapi.update_folder_name(this.state.folder.id, name).then(() => {
            return this.doFetch();
        })
    }

    updateDescription(description: string) {
        tapi.update_folder_description(this.state.folder.id, description).then(() => {
            return this.doFetch();
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

        if (actionName === "move") {
            actionDescription = "Move the selected file(s) into the chosen folder";
        }
        else if (actionName === "link") {
            this.setState({initFolderId: ""});
            actionDescription = "Add the selected file(s) into the chosen folder";
        }
        else if (actionName === "linkToHome") {
            this.setState({initFolderId: this.state.currentUser.home_folder_id});
            actionDescription = "Add the selected file(s) into your Home folder";
        }
        else if (actionName === "currentFolderLinkToHome") {
            this.setState({initFolderId: this.state.currentUser.home_folder_id});
            actionDescription = "Add the current folder into your Home folder";
        }
        else if (actionName === "currentFolderLink") {
            this.setState({initFolderId: ""});
            actionDescription = "Add the current folder into another folder";
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
        if (this.state.actionName === "move") {
            tapi.move_to_folder(this.state.selection, this.state.folder.id, folderId).then(() => this.afterAction());
        }
        else if (this.state.actionName === "link" || this.state.actionName == "linkToHome") {
            tapi.copy_to_folder(this.state.selection, folderId).then(() => this.afterAction());
        }
        else if (this.state.actionName === "currentFolderLinkToHome") {
            tapi.copy_to_folder([this.props.params.folderId], folderId).then(() => this.afterAction());
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
            return tapi.get_dataset_version_last(dataset_id).then((newDatasetVersion) => {
                this.doFetch();
                return Promise.resolve(newDatasetVersion);
            });
        }).catch((err: any) => {
            console.log(err);
            return Promise.reject(err);
        });
    }

    getMostRecentDateEntry(entry: Folder.FolderEntries) {
        // TODO: Think about Command Pattern instead of repeating this dangerous check here and in models.ts
        if (entry.type === Folder.FolderEntriesTypeEnum.Folder) {
            return entry.creation_date;
        }
        else if (entry.type === Folder.FolderEntriesTypeEnum.Dataset || entry.type == Folder.FolderEntriesTypeEnum.VirtualDataset) {
            let latestDatasetVersion = this.state.datasetLastDatasetVersion[entry.id];
            return latestDatasetVersion.creation_date;
        }
        else if (entry.type === Folder.FolderEntriesTypeEnum.DatasetVersion) {
            return entry.creation_date;
        }
    }

    // BootstrapTable Entries
    nameUrlFormatter(cell, row: BootstrapTableFolderEntry) {
        // TODO: Think about Command Pattern instead of repeating this dangerous check here and in models.ts
        let glyphicon = null;
        if (row.type === Folder.FolderEntriesTypeEnum.Folder) {
            glyphicon = <Glyphicon glyph="glyphicon glyphicon-folder-close"/>
        }
        else if (row.type === Folder.FolderEntriesTypeEnum.Dataset) {
            glyphicon = <Glyphicon glyph="glyphicon glyphicon-inbox"/>
        }
        else if (row.type === Folder.FolderEntriesTypeEnum.DatasetVersion) {
            glyphicon = <Glyphicon glyph="glyphicon glyphicon-file"/>
        } else if (row.type === Folder.FolderEntriesTypeEnum.VirtualDataset) {
            glyphicon = <Glyphicon glyph="glyphicon glyphicon-flash"/>
        } else {
            console.log("unknown type:", row.type)
        }

        return (
            <span title={cell}>
                {glyphicon}
                <span> </span>
                <Link key={row.id} to={row.url}>
                    {cell}
                </Link>
            </span>
        );
    }

    typeFormatter(cell: string, row: BootstrapTableFolderEntry) {
        if (cell) {
            return cell[0].toUpperCase() + cell.slice(1, cell.length);
        }
        else {
            return "";
        }
    }

    dataFormatter(cell: Date, row: BootstrapTableFolderEntry) {
        return toLocalDateString(cell.toDateString());
    }

    onRowSelect(row: BootstrapTableFolderEntry, isSelected: Boolean, e) {
        let select_key = row.id;
        const original_selection: any = this.state.selection;

        let updated_selection: Array<string>;

        let index = original_selection.indexOf(select_key);
        if (index !== -1) {
            updated_selection = update(original_selection, {$splice: [[index, 1]]});
        }
        else {
            updated_selection = update(original_selection, {$push: [select_key]});
        }

        this.setState({selection: updated_selection});
    }

    onAllRowsSelect(isSelected: Boolean, rows: Array<BootstrapTableFolderEntry>) {
        const original_selection: any = this.state.selection;
        let updated_selection: Array<string> = original_selection;

        let select_key = null;
        let index = null;
        rows.forEach((row) => {
            select_key = row.id;
            index = updated_selection.indexOf(select_key);

            if (index != -1) {
                updated_selection = update(updated_selection, {$splice: [[index, 1]]});
            }
            else {
                updated_selection = update(updated_selection, {$push: [select_key]});
            }
        });

        this.setState({selection: updated_selection});
    }

    wrap_parent_link(folder_named_id: NamedId, index: number, total_length: number) {
        return <span key={index}>
                    <Link to={relativePath("folder/"+folder_named_id.id)}>{folder_named_id.name}</Link>
            {total_length != index + 1 &&
            <span>, </span>
            }
                </span>
    }

    get_parent_links(parents: Array<NamedId>, public_only: Boolean, is_owner: Boolean) {
        let parent_links = [];
        parent_links = parents.map((p: NamedId, index: number) => {
            return this.wrap_parent_link(p, index, parents.length);
        });
        return parent_links;
    }

    removeAccessLogs(arrayAccessLogs: Array<AccessLog>): Promise<any> {
        return tapi.remove_entry_access_log(arrayAccessLogs).then(() => {

        });
    }

    // Search
    executeSearch(searchQuery) {
        let url = relativePath("search/" + this.state.folder.id + "/" + searchQuery);
        window.location.href = url;
    }

    searchKeyPress(event, searchQuery) {
        if (event.key === "Enter") {
            this.executeSearch(searchQuery);
        }
    }

    // region Sharing

    loadSelectionAndShare(){
        // Process the selection into Folder | FolderEntries
        if (this.state.selection.length === 0) {
            this.setState({
                sharingEntries: [this.state.folder]
            });
        }
        else {
            let selectedEntries = this.state.selection.map((entryID) => {
                return this.state.folder.entries.find((folderEntry) => {
                   return folderEntry.id === entryID;
                });
            });
            this.setState({
                sharingEntries: selectedEntries
            });
        }

        // Show share dialog
        this.setState({showShareFolder: true});
    }

    // endregion

    render() {
        let entriesOutput: Array<any> = [];
        let navItems: MenuItem[] = [];
        let folderEntriesTableFormatted: Array<BootstrapTableFolderEntry> = [];

        if (!this.state) {
            return <div>
                <LeftNav items={[]}/>
                <div id="main-content"/>
            </div>;
        } else if (this.state.error && this.state.error.toUpperCase() === "NOT FOUND".toUpperCase()) {
            let message = "The folder " + this.props.params.folderId + " does not exist. Please check this id " +
                "is correct. We are also available via the feedback button.";
            return <div>
                <LeftNav items={[]}/>
                <div id="main-content">
                    <NotFound message={message}/>
                </div>
            </div>
        } else if (this.state.error) {
            return <div>
                <LeftNav items={[]}/>
                <div id="main-content">
                    An error occurred: {this.state.error}
                </div>
            </div>
        }

        if (this.state && this.state.folder) {

            var folder: Folder.Folder = this.state.folder;

            let parent_public = folder.parents.some((parent) => {
                return parent.id == 'public';
            });
            let is_owner = (folder.creator && folder.creator.id === currentUser);
            var parent_links = this.get_parent_links(folder.parents, parent_public, is_owner);

            folderEntriesTableFormatted = folder.entries.map((entry: Folder.FolderEntries, index: number) => {
                let latestDatasetVersion = this.state.datasetLastDatasetVersion[entry.id];
                let full_datasetVersion: Folder.DatasetVersion = this.state.datasetsVersion[entry.id];
                return new BootstrapTableFolderEntry(entry, latestDatasetVersion, full_datasetVersion);
            });

            let selectionCount = this.state.selection.length;

            if (selectionCount === 0) {
                let add_folder_items = [];

                navItems.push({
                        label: "Share folder", action: () => {
                            this.loadSelectionAndShare();
                        }
                });

                // If the user can edit, then it has access to the actions
                if (folder.can_edit) {
                    add_folder_items.push(
                        {
                            label: "Create a subfolder", action: () => {
                                this.setState({showCreateFolder: true});
                            }
                        },
                        {
                            label: "Upload dataset", action: () => {
                                this.setState({showUploadDataset: true});
                            }
                        }
                    );
                    navItems.push({
                        label: "Edit name", action: () => {
                            this.setState({showEditName: true})
                        }
                    });
                    navItems.push(
                        {
                            label: "Edit description", action: () => {
                            this.setState({showEditDescription: true})
                        }
                        });
                    navItems.push({
                        label: "Edit permissions", action: () => {
                            this.setState({showEditPermissions: true})
                        }
                    });
                }
                navItems.push({
                    label: "Add to Home", action: () => {
                        this.openActionTo("currentFolderLinkToHome");
                    }
                });
                navItems.push({
                    label: "Add to a folder", action: () => {
                        this.openActionTo("currentFolderLink");
                    }
                });

                navItems = navItems.concat(add_folder_items);
            } else {
                navItems.push({
                    label: "Share selected items", action: () => {
                        this.loadSelectionAndShare();
                    }
                });
                if (folder.can_edit) {
                    // Don't display this if we are in the trash of the user
                    if (this.state.folder.folder_type !== Folder.TypeFolderEnum.Trash) {
                        navItems.push({
                            label: "Move to trash", action: () => this.moveToTrash()
                        });
                    }
                    navItems.push({
                        label: "Move to...", action: () => {
                            this.openActionTo("move");
                        }
                    });
                }

                navItems.push({
                    label: "Add to Home", action: () => {
                        this.openActionTo("linkToHome");
                    }
                });
                navItems.push({
                    label: "Add to a folder", action: () => {
                        this.openActionTo("link");
                    }
                });

            }
        }

        // Bootstrap Table configuration
        const check_mode: SelectRowMode = 'checkbox';
        const selectRowProp: SelectRow = {
            mode: check_mode,
            onSelect: (row: any, isSelected: Boolean, e: any) => {
                this.onRowSelect(row, isSelected, e);
                return true;
            },
            onSelectAll: (isSelected: Boolean, currentSelectedAndDisplayData: Array<BootstrapTableFolderEntry>) => {
                this.onAllRowsSelect(isSelected, currentSelectedAndDisplayData);
                return true;
            }
        };

        const desc_sortOrder: SortOrder = 'desc';
        const options: Options = {
            noDataText: 'Nothing created yet',
            defaultSortName: 'creation_date',  // default sort column name
            defaultSortOrder: desc_sortOrder  // default sort order
        };

        return (
            <div>
                <LeftNav items={navItems}/>
                <div id="main-content">
                    { folder && <span>
                        <Dialogs.EditName isVisible={this.state.showEditName}
                                          initialValue={ this.state.folder.name }
                                          cancel={ () => { this.setState({showEditName: false})} }
                                          save={ (name:string) => {
                                this.setState({showEditName: false});
                                this.updateName(name);
                        } }/>

                        <Dialogs.EditDescription
                            initialValue={ this.state.folder.description }
                            isVisible={this.state.showEditDescription}
                            cancel={ () => { this.setState({showEditDescription: false})} }
                            save={ (description:string) => {
                                this.setState({showEditDescription: false});
                                this.updateDescription(description);
                            }}/>

                        <Upload.UploadDataset
                            isVisible={this.state.showUploadDataset}
                            cancel={ () => { this.setState({showUploadDataset: false}) } }

                            onFileUploadedAndConverted={ (sid: string, name: string , description: string) =>
                                this.filesUploadedAndConverted(sid, name, description) }
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
                            initFolderId={ this.state.initFolderId }
                        />

                        <EntryUsersPermissions
                            isVisible={ this.state.showEditPermissions }
                            cancel={ () => { this.setState({showEditPermissions: false})}}
                            entry_id={ this.state.folder.id }
                            handleDeletedRow={ (arrayAccessLogs) => {return this.removeAccessLogs(arrayAccessLogs)} }
                        />

                        <Dialogs.ShareEntries
                            isVisible={ this.state.showShareFolder }
                            cancel={ () => {this.setState({showShareFolder: false});}}
                            entries={ this.state.sharingEntries }
                        />

                        <h1>{folder.name}</h1>

                        <Conditional show={ parent_links.length > 0 }>
                            <p>Parents: {parent_links}</p>
                        </Conditional>

                        <Grid fluid={true} style={{
                            padding: "0px 15px 0px 0px"
                        }}>
                          <Row className="show-grid">
                            <Col md={8}>
                              { Dialogs.renderDescription(this.state.folder.description) }
                            </Col>
                            <Col md={4}>
                                <SearchInput onKeyPress={(event, searchQuery) => this.searchKeyPress(event, searchQuery)}
                                            onClick={(searchQuery) => this.executeSearch(searchQuery)}/>
                                <br/>
                            </Col>
                          </Row>
                        </Grid>

                        <BootstrapTable data={ folderEntriesTableFormatted }
                                        bordered={ false }
                                        tableStyle={ tableEntriesStyle }
                                        selectRow={ selectRowProp }
                                        ref={(ref) => { this.bootstrapTable = ref }}
                                        options={ options }
                                        striped hover
                        >
                            <TableHeaderColumn dataField='id' isKey hidden>ID</TableHeaderColumn>
                            <TableHeaderColumn dataField='name' dataSort
                                               dataFormat={ this.nameUrlFormatter }>Name</TableHeaderColumn>
                            <TableHeaderColumn dataField='creation_date' dataSort
                                               dataFormat={ this.dataFormatter }
                                               width="100">Date</TableHeaderColumn>
                            <TableHeaderColumn dataField='type'
                                               dataFormat={ this.typeFormatter }
                                               dataSort
                                               width="100">Type</TableHeaderColumn>
                            <TableHeaderColumn dataField='creator_name'
                                               dataSort
                                               width="150">Creator</TableHeaderColumn>
                        </BootstrapTable>

                        {this.state.loading && <LoadingOverlay></LoadingOverlay>}
                    </span> }
                </div>
            </div>
        )
    }
}