import * as React from "react";
import {Link} from 'react-router';
import {Well} from "react-bootstrap";

import {LeftNav} from "./LeftNav";
import {EntryUsersPermissions} from "./modals/EntryUsersPermissions";

import * as Models from "../models/models"
import {TaigaApi} from "../models/api"

import * as Dialogs from "./Dialogs"
import * as Upload from "./modals/Upload";

import {toLocalDateString} from "../utilities/formats";
import {LoadingOverlay} from "../utilities/loading";
import {relativePath} from "../utilities/route";
import {DatafileUrl, ConversionStatusEnum} from "../models/models";
import {DatasetVersion} from "../models/models";
import {NotFound} from "./NotFound";
import {NamedId} from "../models/models";

export interface DatasetViewProps {
    params: any
}

export interface DatasetViewState {
    dataset?: Models.Dataset;
    datasetVersion?: Models.DatasetVersion;

    showEditName?: boolean;
    showEditDescription?: boolean;
    showEditPermissions?: boolean;

    showUploadDataset?: boolean;
    loading?: boolean;
    loadingMessage?: string;
    exportError?: boolean;
    exportErrorInfo?: {datasetVersionId: string, datafileName: string, conversionType: string}

    initInputFolderId?: string;
    showInputFolderId?: boolean;
    callbackIntoFolderAction?: Function;

    fetchError?: string;
}

const buttonUploadNewVersionStyle = {
    margin: '0 0 10px'
};

let tapi: TaigaApi = null;
let currentUser: string = null;

export class DatasetView extends React.Component<DatasetViewProps, DatasetViewState> {
    static contextTypes = {
        tapi: React.PropTypes.object,
        currentUser: React.PropTypes.string
    };

    componentDidUpdate(prevProps: DatasetViewProps) {
        // respond to parameter change in scenario 3
        let oldId = prevProps.params.datasetVersionId;
        let newId = this.props.params.datasetVersionId;
        if (newId !== oldId) {
            this.doFetch();
            // We close the modal
            this.setState({
                showUploadDataset: false,
                loading: false,
                exportError: false
            })
        }
    }

    componentDidMount() {
        tapi = (this.context as any).tapi;
        currentUser = (this.context as any).currentUser;

        this.setLoading(true);

        this.doFetch().then(() => {
            this.setState({
                showInputFolderId: false
            });

            this.logAccess();

            this.setLoading(false);

            // Update the url
            let last_index_dataset_permaname = this.state.dataset.permanames.length - 1;
            let url =  relativePath("/dataset/" +
                this.state.dataset.permanames[last_index_dataset_permaname] +
                "/" + this.state.datasetVersion.version);
            let history_obj = { Title: this.state.dataset.name + " v" + this.state.datasetVersion.version,
                Url: url };
            history.replaceState(history_obj, history_obj.Title, history_obj.Url);
            // window.location.pathname = relativePath("/dataset/" +
            //     this.state.dataset.permanames[last_index_dataset_permaname] +
            //     "/" + this.state.datasetVersion.version);
        }).catch((error) => {
            console.log("doFetch failed with this error: "+error);
        });
    }

    doFetch() {
        // could do fetches in parallel if url encoded both ids
        return tapi.get_dataset_version_with_dataset(this.props.params.datasetId,
            this.props.params.datasetVersionId
        ).then((datasetAndDatasetVersion: Models.DatasetAndDatasetVersion | Models.Dataset) => {
            let dataset: Models.Dataset;
            let datasetVersion: Models.DatasetVersion;

            if ((datasetAndDatasetVersion as Models.DatasetAndDatasetVersion).dataset) {
                datasetAndDatasetVersion = (datasetAndDatasetVersion as Models.DatasetAndDatasetVersion);
                dataset = datasetAndDatasetVersion.dataset;
                datasetVersion = datasetAndDatasetVersion.datasetVersion;

                this.setState({
                    dataset: dataset, datasetVersion: datasetVersion
                });
            }
            else if ((datasetAndDatasetVersion as Models.Dataset).id) {
                // It means we received a Models.Dataset, we need to get the last datasetVersion now
                // TODO: get_dataset_version_with_dataset should really return a dataset with datasetVersion, and we should not do this extra step
                dataset = (datasetAndDatasetVersion as Models.Dataset);
                return tapi.get_dataset_version_last(dataset.id).then((last_datasetVersion) => {
                    datasetVersion = last_datasetVersion;
                }).then(() => {
                    this.setState({
                        dataset: dataset, datasetVersion: datasetVersion
                    });
                });
            }
            else {
                console.log("Error in doFetch DatasetView. Type received is not a Dataset or a DatasetAndDatasetVersion");
            }
        }).catch((error) => {
            this.setState({
               fetchError: error.message
            });
            console.log("Error: "+error.stack);
            return Promise.reject("Dataset Version " + this.props.params.datasetVersionId + " does not exist");
        });
    }

    // TODO: Refactor logAccess in an util or in RecentlyViewed class
    logAccess() {
        return tapi.create_or_update_entry_access_log(this.state.dataset.id).then(() => {
        });
    }

    updateName(name: string) {
        tapi.update_dataset_name(this.state.datasetVersion.dataset_id, name).then(() => {
            return this.doFetch()
        })
    }

    updateDescription(description: string) {
        tapi.update_dataset_version_description(this.state.datasetVersion.id, description).then(() => {
            return this.doFetch();
        })
    }

    getLinkOrNot(dataset_version: NamedId) {
        let dataset = this.state.dataset;
        if (dataset_version.id == this.state.datasetVersion.id) {
            return <span>{dataset_version.name}</span>
        }
        else {
            let last_index_dataset_permaname = dataset.permanames.length - 1;
            let url =  relativePath("/dataset/" +
                dataset.permanames[last_index_dataset_permaname] +
                "/" + dataset_version.name);
            return <Link to={url}>{dataset_version.name}</Link>
        }
    }

    // Upload
    showUploadNewVersion() {
        this.setState({
            showUploadDataset: true
        })
    }

    filesUploadedAndConverted(sid: string, name: string, description: string, previousDatafileIds: Array<string>) {
        let datafileIds = previousDatafileIds;
        // We ask to create the dataset
        return tapi.create_new_dataset_version(sid,
            this.state.dataset.id,
            description,
            datafileIds
        ).then((dataset_version_id) => {
            // We fetch the datasetVersion of the newly created dataset and change the state of it
            return tapi.get_dataset_version(dataset_version_id).then((newDatasetVersion) => {
                this.doFetch();
                return Promise.resolve(newDatasetVersion);
            });
        }).catch((err: any) => {
            console.log(err);
            return Promise.reject(err);
        });
    }

    // Download

    // Async function to wait
    delay(milliseconds: number) {
        return new Promise<void>(resolve => {
            setTimeout(resolve, milliseconds);
        });
    }

    getOrLaunchConversion(datasetPermaname: string, version: string, datasetVersionId: string,
                          datafileName: string, format: string, force: string) {
        // Ask for conversion, if ok download. Else convert process and loading for user
        // Loading
        this.setLoading(true);

        return tapi.get_datafile(datasetPermaname, version, datasetVersionId, datafileName, format, force)
            .then((result: DatafileUrl) => {
                if (!result.urls) {
                    // While we don't receive urls, it means we are still converting/downloading
                    return this.delay(500).then(() => {
                        this.setLoadingMessage(result.status + "...");
                        return this.getOrLaunchConversion(datasetPermaname, version, datasetVersionId, datafileName, format, 'N');
                    });
                }
                else {
                    this.setLoading(false);
                    // We stop the loading, and download the file because it is ready
                    result.urls.forEach((url) => {
                        window.location.href = url;
                        console.log("- " + url);
                    });
                }
            }).catch((reason: any) => {
                // TODO: Replace here with a DialogModal which is going to ask about retry or cancel
                this.setLoading(false);

                const exportErrorInfo = {
                    datasetVersionId: datasetVersionId,
                    datafileName: datafileName,
                    conversionType: format
                };
                // TODO: The reason should be passed along, but the other message should be written in the Dialog.ExportError module
                this.setLoadingMessage("Conversion error on server side: " + reason + ". Please inform the admin." +
                    " You can retry now, or later on.");
                this.setState({
                    exportError: true,
                    exportErrorInfo: exportErrorInfo
                });
            });
    }

    setLoading(requireLoading: boolean, message?: string) {
        if (message) {
            this.setState({
                loading: requireLoading,
                loadingMessage: message
            });
        }
        else {
            this.setState({
                loading: requireLoading
            })
        }
    }

    setLoadingMessage(message: string) {
        this.setState({
            loadingMessage: message
        });
    }

    forceExport() {
        this.setLoadingMessage("Sent the request to the server...");
        this.setState({
            exportError: false
        });
        this.getOrLaunchConversion(undefined, undefined,
            this.state.exportErrorInfo.datasetVersionId,
            this.state.exportErrorInfo.datafileName,
            this.state.exportErrorInfo.conversionType, 'Y');
    }

    // Move/Copy
    copyTo(alreadyFilledFolderId: string) {
        // TODO: Change the string telling the action to an enum, like in the backend
        this.setState({
            initInputFolderId: alreadyFilledFolderId,
            callbackIntoFolderAction: (folderId) => {
                tapi.copy_to_folder([this.state.dataset.id], folderId).then(() => this.afterAction());
            },
            showInputFolderId: true,
            actionIntoFolderValidation: null,
            actionIntoFolderHelp: null
        });
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

    removeAccessLogs(arrayAccessLogs: Array<Models.AccessLog>): Promise {
        return tapi.remove_entry_access_log(arrayAccessLogs).then(() => {

        });
    }

    // DatasetVersions
    compareDatasetVersionsByVersionNumber(a: NamedId, b: NamedId) {
        // VersionNumber == Name
        let int_name_a = parseInt(a.name);
        let int_name_b = parseInt(b.name);
        if (int_name_a < int_name_b) {
            return -1;
        }
        else if (int_name_a > int_name_b) {
            return 1;
        }
        else {
            return 0;
        }
    }

    render() {
        if (!this.state) {
            return     <div>
                <LeftNav items={[]}/>
                <div id="main-content">
                    Loading...
                </div>
            </div>
        }
        else if (this.state && this.state.fetchError){
            let message = "Dataset version " + this.props.params.datasetVersionId + " does not exist. Please check this id "
                + "is correct. We are also available via the feedback button.";
            return <div>
                <LeftNav items={[]}/>
                <div id="main-content">
                    <NotFound message={message}/>
                </div>
            </div>
        }
        else {
            let dataset = this.state.dataset;
            let datasetVersion = this.state.datasetVersion;

            let versions = null;
            let folders = null;
            if (dataset) {
                dataset.versions.sort((datasetVersionA: NamedId, datasetVersionB: NamedId) => {
                    return this.compareDatasetVersionsByVersionNumber(datasetVersionA, datasetVersionB);
                });
                versions = dataset.versions.map((dataset_version: NamedId, index: any) => {
                    return <span key={dataset_version.id}>
                    {this.getLinkOrNot(dataset_version)}
                        {dataset.versions.length != index + 1 &&
                        <span>, </span>
                        }
                </span>
                });

                folders = dataset.folders.map((f, index) => {
                    return (
                        <span key={index}>
                        <Link to={relativePath("folder/"+f.id)}>
                            {f.name}
                        </Link>
                            {dataset.folders.length != index + 1 &&
                            <span>, </span>
                            }
                    </span>
                    )
                });
            }

            let entries = null;
            let weHaveProvenanceGraphs = null;
            if (datasetVersion) {
                entries = datasetVersion.datafiles.sort((datafile_one, datafile_two) => {
                    let datafile_one_upper = datafile_one.name.toUpperCase();
                    let datafile_two_upper = datafile_two.name.toUpperCase();
                    if (datafile_one_upper == datafile_two_upper) {
                        return 0;
                    }
                    else if (datafile_one_upper > datafile_two_upper ){
                        return 1;
                    }
                    else {
                        return -1;
                    }
                }).map((df, index) => {
                    let conversionTypesOutput = df.allowed_conversion_type.map((conversionType, index) => {
                        // TODO: If we have the same name for datafiles, we will run into troubles
                        return <span key={conversionType}>
                    <a href="#" onClick={() => {
                        this.setLoadingMessage("Sent the request to the server...");
                        return this.getOrLaunchConversion(undefined, undefined,
                            datasetVersion.id, df.name, conversionType, 'N'); }}>
                        { conversionType }
                        </a>
                            { df.allowed_conversion_type.length != index + 1 &&
                            <span>, </span>
                            }
                </span>
                    });


                    let provenanceGraphs = null;
                    if (df.provenance_nodes) {

                        provenanceGraphs = df.provenance_nodes.map((provenance_node, index) => {
                            return <span key={provenance_node.graph.graph_id}>
                        <Link to={relativePath("provenance/"+provenance_node.graph.graph_id)}>
                            {provenance_node.graph.name}
                            { df.provenance_nodes.length != index + 1 &&
                            <span>, </span>
                            }
                        </Link>
               </span>
                        });
                    }

                    return <tr key={index}>
                        <td>{df.name}</td>
                        <td>{df.short_summary}</td>
                        <td>
                            { conversionTypesOutput }
                        </td>

                        { df.provenance_nodes.length > 0 &&
                        <td>
                            { provenanceGraphs }
                        </td>
                        }
                    </tr>
                });

                weHaveProvenanceGraphs = datasetVersion.datafiles.some((element, index, array) => {
                    return element.provenance_nodes.length > 0;
                });
            }


            let navItems = [];
            navItems = [
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
                    label: "Edit permissions", action: () => {
                        this.setState({showEditPermissions: true})
                }
                },
                // {
                //     label: "Add permaname", action: function () {
                // }
                // },
                {
                    label: "Create new version", action: () => {
                        this.showUploadNewVersion();
                    }
                },
                {
                    label: "Link to Home", action: () => {
                        // TODO: Fetch the current user only once, and reuse it as a state OR better, get it as a props from parent
                        tapi.get_user().then(user => {
                            this.copyTo(user.home_folder_id);
                        })
                    }
                },
                {
                    label: "Link to...", action: () => {
                    this.copyTo("");
                }
                }
                // {
                //     label: "Deprecate version", action: function () {
                // }
                // },
                // {
                //     label: "Show History", action: function () {
                // }
                // }
            ]
            ;

            let permaname = null;
            let r_block = null;
            let python_block = null;
            let leftNavsDialogs = null;

            if (dataset && datasetVersion) {
                permaname = dataset.permanames[dataset.permanames.length - 1];
                r_block = "library(taigr);\n";

                if (datasetVersion.datafiles.length == 1) {
                    r_block += `data <- load.from.taiga(data.name='${permaname}', data.version=${datasetVersion.version})`;
                } else {
                    let r_block_lines = datasetVersion.datafiles.map((df, index) => {
                        let r_name = df.name.replace(/[^A-Za-z0-9]+/g, ".");
                        return `${r_name} <- load.from.taiga(data.name='${permaname}', data.version=${datasetVersion.version}, data.file='${df.name}')`;
                    });
                    r_block += r_block_lines.join("\n")
                }

                python_block = "from taigapy import TaigaClient\n";
                python_block += "tc = TaigaClient()\n";
                if (datasetVersion.datafiles.length == 1) {
                    let has_raw = datasetVersion.datafiles[0].allowed_conversion_type.some((conversion_type) => {
                       return conversion_type === 'raw';
                    });

                    if (has_raw) {
                        python_block += `data = tc.download_to_cache(name='${permaname}', version='${datasetVersion.version}')  # download_to_cache for raw`;
                    }
                    else {
                        python_block += `data = tc.get(name='${permaname}', version='${datasetVersion.version}')`;
                    }
                } else {
                    let python_block_lines = datasetVersion.datafiles.map((df, index) => {
                        let has_raw = df.allowed_conversion_type.some((conversion_type) => {
                            return conversion_type === 'raw';
                        });

                        let python_name = df.name;

                        if(has_raw) {
                            return `${python_name} = tc.download_to_cache(name='${permaname}', version=${datasetVersion.version}, file='${df.name}')  # download_to_cache for raw`;
                        }
                        else {
                            return `${python_name} = tc.get(name='${permaname}', version=${datasetVersion.version}, file='${df.name}')`;
                        }
                    });
                    python_block += python_block_lines.join("\n")
                }

                leftNavsDialogs = (
                    <span>
                    <Dialogs.EditName isVisible={this.state.showEditName}
                                      initialValue={this.state.dataset.name}
                                      cancel={ () => { this.setState({showEditName: false})} }
                                      save={ (name:string) => {
                            this.setState({showEditName: false});
                            this.updateName(name)
                            } }/>
                    <Dialogs.EditDescription isVisible={this.state.showEditDescription}
                                              cancel={ () => { this.setState({showEditDescription: false}) } }
                                              initialValue={this.state.datasetVersion.description}
                                              save={ (description: string) => {
                    this.setState({showEditDescription: false});
                    console.log("Save description: " + description); this.updateDescription(description); } }/>

                    <Upload.UploadDataset
                        isVisible={this.state.showUploadDataset}
                        cancel={ () => { this.setState({showUploadDataset: false}) } }
                        onFileUploadedAndConverted={ (sid: string, name: string, description: string, previousDatafileIds: Array<string>) =>
                            this.filesUploadedAndConverted(sid, name, description, previousDatafileIds)
                        }
                        title="New Dataset Version"
                        readOnlyName={ this.state.dataset.name }
                        previousDescription={ this.state.datasetVersion.description }
                        previousVersionName={ this.state.datasetVersion.name }
                        previousVersionFiles={ this.state.datasetVersion.datafiles }
                    />

                    <Dialogs.InputFolderId
                        actionDescription="link this dataset into it"
                        isVisible={ this.state.showInputFolderId }
                        cancel={ () => { this.setState({showInputFolderId: false}) }}
                        save={ (folderId) => { this.state.callbackIntoFolderAction(folderId) }}
                        initFolderId={ this.state.initInputFolderId }
                    />

                    <EntryUsersPermissions
                        isVisible={ this.state.showEditPermissions }
                        cancel={ () => { this.setState({showEditPermissions: false})}}
                        entry_id={ this.state.dataset.id }
                        handleDeletedRow={ (arrayAccessLogs) => {return this.removeAccessLogs(arrayAccessLogs)} }
                    />
                </span>
                );
            }


            return <div>
                <LeftNav items={navItems}/>
                <div id="main-content">
                    { dataset && datasetVersion &&
                    <span>
                    { leftNavsDialogs }

                        <h1>
                            {dataset.name} <small>{ permaname }</small>
                        </h1>
                    <p>Version {datasetVersion.version} created by {datasetVersion.creator.name}
                        &nbsp;on the {toLocalDateString(datasetVersion.creation_date)}</p>
                    <p>Versions: {versions} </p>

                        { folders.length > 0 &&
                        <p>Contained within {folders}</p>
                        }

                        { this.state.datasetVersion.description &&
                            Dialogs.renderDescription(this.state.datasetVersion.description)
                        }

                        <h2>Contents</h2>
                    <table className="table">
                        <thead>
                        <tr>
                            <th>Name</th>
                            {/*<th>Description</th>*/}
                            <th>Summary</th>
                            <th>Download</th>

                            { weHaveProvenanceGraphs &&
                            <th>Provenance Graph</th>
                            }
                        </tr>
                        </thead>
                        <tbody>
                        {entries}
                        </tbody>
                    </table>
                        <h2>Reading from R (<a href="https://stash.broadinstitute.org/projects/CPDS/repos/taigr/browse" target="_blank">TaigaR</a>)</h2>
                    <pre>{r_block}</pre>
                        <h2>
                            Reading from Python (<a href="https://stash.broadinstitute.org/projects/CPDS/repos/taigapy/browse" target="_blank">Taigapy</a>)
                        </h2>
                    <pre>{python_block}</pre>
                </span>
                    }
                </div>
                {this.state.loading && <LoadingOverlay message={ this.state.loadingMessage }></LoadingOverlay>}
                <Dialogs.ExportError isVisible={this.state.exportError}
                                     cancel={ () => this.setState({exportError: false})}
                                     retry={ () => this.forceExport() }
                                     message={this.state.loadingMessage}/>
            </div>
        }
    }
}


