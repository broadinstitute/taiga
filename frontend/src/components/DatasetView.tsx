import * as React from "react";
import {Link} from 'react-router';
import {Well} from "react-bootstrap";

import {LeftNav} from "./LeftNav"

import * as Models from "../models/models"
import {TaigaApi} from "../models/api"

import * as Dialogs from "./Dialogs"
import * as Upload from "./modals/Upload";

import {toLocalDateString} from "../utilities/formats";
import {LoadingOverlay} from "../utilities/loading";
import {relativePath} from "../utilities/route";
import {DatafileUrl, ConversionStatusEnum} from "../models/models";

export interface DatasetViewProps {
    params: any
}

export interface DatasetViewState {
    dataset?: Models.Dataset;
    datasetVersion?: Models.DatasetVersion;
    showEditName?: boolean;
    showEditDescription?: boolean;
    showUploadDataset?: boolean;
    loading?: boolean;
    loadingMessage?: string;
    exportError?: boolean;
    exportErrorInfo?: {datasetVersionId: string, datafileName: string, conversionType: string}

    showInputFolderId?: boolean;
    callbackIntoFolderAction?: Function;
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
        });
    }

    logAccess() {
        return tapi.create_or_update_dataset_access_log(this.state.dataset.id).then(() => {
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

    getLinkOrNot(dataset_version: Models.DatasetVersion) {
        let dataset = this.state.dataset;
        if (dataset_version.id == this.state.datasetVersion.id) {
            return <span>{dataset_version.name}</span>
        }
        else {
            return <Link to={relativePath("dataset/"+dataset.id+"/"+dataset_version.id)}>{dataset_version.name}</Link>
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
    copyTo() {
        // TODO: Change the string telling the action to an enum, like in the backend

        this.setState({
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

    render() {
        if (!this.state) {
            return     <div>
                <LeftNav items={[]}/>
                <div id="main-content">
                    Loading...
                </div>
            </div>
        }
        let dataset = this.state.dataset;
        let datasetVersion = this.state.datasetVersion;

        let versions = null;
        let folders = null;
        if (dataset) {
            versions = dataset.versions.map((dataset_version: Models.DatasetVersion, index: any) => {
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
            entries = datasetVersion.datafiles.map((df, index) => {
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
                label: "Edit Name", action: () => {
                this.setState({showEditName: true})
            }
            },
            {
                label: "Edit Description", action: () => {
                this.setState({showEditDescription: true})
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
                label: "Copy to...", action: () => {
                    this.copyTo();
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

            leftNavsDialogs = (
                <span>
                    <Dialogs.EditName isVisible={this.state.showEditName}
                                      initialValue={this.state.dataset.name}
                                      cancel={ () => { this.setState({showEditName: false})} }
                                      save={ (name:string) => {
                            this.setState({showEditName: false});
                            this.updateName(name)
                            } }/>
                    < Dialogs.EditDescription isVisible={this.state.showEditDescription}
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
                        currentFolderId={this.state.dataset.folders[0].id}
                        title="New Dataset Version"
                        readOnlyName={ this.state.dataset.name }
                        previousDescription={ this.state.datasetVersion.description }
                        previousVersionName={ this.state.datasetVersion.name }
                        previousVersionFiles={ this.state.datasetVersion.datafiles }
                    />

                    <Dialogs.InputFolderId
                        actionDescription="copy this dataset into it"
                        isVisible={ this.state.showInputFolderId }
                        cancel={ () => { this.setState({showInputFolderId: false}) }}
                        save={ (folderId) => { this.state.callbackIntoFolderAction(folderId) }}
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

                    <h1>{dataset.name}
                        <small>{permaname}</small>
                    </h1>
                    <p>Version {datasetVersion.version} created by {datasetVersion.creator.name}
                        &nbsp;on the {toLocalDateString(datasetVersion.creation_date)}</p>
                    <p>Versions: {versions} </p>

                    { (datasetVersion.creator.id == currentUser ||
                    dataset.folders.some((folder) => {
                        return folder.id == "public"
                    })) &&
                    <p>Contained within {folders}</p>
                    }
                    {/*{ancestor_section}*/}

                    { this.state.datasetVersion.description &&
                    <Well bsSize="sm">{this.state.datasetVersion.description}</Well>
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
                    <h2>Reading from R</h2>
                    <pre>{r_block}</pre>
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


