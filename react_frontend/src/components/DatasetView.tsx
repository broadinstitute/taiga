import * as React from "react";
import { RouteComponentProps } from "react-router";
import { Link } from "react-router-dom";
import { OverlayTrigger, Tooltip, Button } from "react-bootstrap";
import { BootstrapTable, TableHeaderColumn } from "react-bootstrap-table";
import update from "immutability-helper";

import { LeftNav } from "./LeftNav";
import { EntryUsersPermissions } from "./modals/EntryUsersPermissions";

import * as Models from "../models/models";
import { TaigaApi } from "../models/api";

import * as Dialogs from "./Dialogs";
import { CreateDatasetDialog, CreateVersionDialog } from "./modals/UploadForm";
import UploadToFigshare from "./modals/UploadToFigshare";

import { toLocalDateString } from "../utilities/formats";
import { LoadingOverlay } from "../utilities/loading";
import { relativePath } from "../utilities/route";
import { DatafileUrl, ConversionStatusEnum, StatusEnum, Entry } from "../models/models";
import { DatasetVersion } from "../models/models";
import { NotFound } from "./NotFound";
import { NamedId } from "../models/models";
import { FolderEntries } from "../models/models";
import {
	ActivityLogEntry,
	ActivityTypeEnum,
	CreationActivityLogEntry,
	NameUpdateActivity,
	DescriptionUpdateActivity,
    VersionAdditionActivity,
    LogStartActivity,
} from "../models/models";
import ClipboardButton from "../utilities/r-clipboard";
import { UploadTracker } from "./UploadTracker";

interface DatasetViewMatchParams {
    datasetId: string;
    datasetVersionId: string;
}

export interface DatasetViewProps extends RouteComponentProps<DatasetViewMatchParams> {
    tapi: TaigaApi;
    user: Models.User;
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
    exportErrorInfo?: { datasetVersionId: string, datafileName: string, conversionType: string };

    initInputFolderId?: string;
    showInputFolderId?: boolean;
    callbackIntoFolderAction?: Function;
    actionIntoFolderValidation?: string;
    actionIntoFolderHelp?: string;

    fetchError?: string;

    showDeprecationReason?: boolean;

    showShareDatasetVersion?: boolean;
    sharingEntries?: Array<Entry>;

    showUploadToFigshare?: boolean;

    activityLog?: Array<ActivityLogEntry>;

    figshare_public_url? : string;
}

const buttonUploadNewVersionStyle = {
    margin: "0 0 10px"
};

const deprecationStyle = {
    color: "orange"
};

const deprecationTitle = {
    color: "orange"
};

const deletionStyle = {
    color: "red"
};

const deletionTitle = {
    color: "red"
};

const descriptionDetailsFormatter = (
	description: string | null,
	title = "Description",
): React.ReactNode => {
	if (!description) {
		return null;
	}
	return (
		<details>
			<summary>{title}</summary>
			<span className="activity-log-description">{description}</span>
		</details>
	);
};

export class DatasetView extends React.Component<DatasetViewProps, DatasetViewState> {
    uploadTracker: UploadTracker;

    constructor(props: DatasetViewProps) {
        super(props);
    }

    getTapi(): TaigaApi {
        return this.props.tapi;
    }

    componentDidUpdate(prevProps: DatasetViewProps) {
        // respond to parameter change in scenario 3
        const oldId = prevProps.match.params.datasetId;
        const newId = this.props.match.params.datasetId;
        const oldVersionId = prevProps.match.params.datasetVersionId;
        const newVersionId = this.props.match.params.datasetVersionId;

        if (newId !== oldId || oldVersionId != newVersionId) {
            this.setLoading(true);

            this.doFetch().then(() => {
                this.logAccess();

                this.getActivityLog();

                if (this.state.datasetVersion.figshare_linked) {
                    this.getFigshareUrl();
                }

                // We close the modal
                this.setState({
                    showUploadDataset: false,
                    showUploadToFigshare: false,
                    loading: false,
                    exportError: false
                });
            });
        }
    }

    componentWillMount() {
        this.uploadTracker = new UploadTracker(this.getTapi());
    }

    componentDidMount() {
        this.setLoading(true);

        this.doFetch().then(() => {
            this.setState({
                showInputFolderId: false
            });

            this.logAccess();

            this.getActivityLog();

            if (this.state.datasetVersion.figshare_linked) {
                this.getFigshareUrl();
            }

            this.setLoading(false);

            // Update the url
            let last_index_dataset_permaname = this.state.dataset.permanames.length - 1;
            let url = relativePath("/dataset/" +
                this.state.dataset.permanames[last_index_dataset_permaname] +
                "/" + this.state.datasetVersion.version);
            let history_obj = {
                Title: this.state.dataset.name + " v" + this.state.datasetVersion.version,
                Url: url
            };
            history.replaceState(history_obj, history_obj.Title, history_obj.Url);
            // window.location.pathname = relativePath("/dataset/" +
            //     this.state.dataset.permanames[last_index_dataset_permaname] +
            //     "/" + this.state.datasetVersion.version);
        }).catch((error: any) => {
            console.log("doFetch failed with this error: " + error);
        });
    }

    doFetch() {
        // could do fetches in parallel if url encoded both ids
        return this.getTapi().get_dataset_version_with_dataset(this.props.match.params.datasetId,
            this.props.match.params.datasetVersionId
        ).then((datasetAndDatasetVersion: Models.DatasetAndDatasetVersion | Models.Dataset) => {
            let dataset: Models.Dataset;
            let datasetVersion: Models.DatasetVersion;

            if ((datasetAndDatasetVersion as Models.DatasetAndDatasetVersion).dataset) {
                datasetAndDatasetVersion = (datasetAndDatasetVersion as Models.DatasetAndDatasetVersion);
                // TODO: Build also this Dataset as a Dataset Entry object
                dataset = new Models.Dataset(datasetAndDatasetVersion.dataset);
                datasetVersion = new Models.DatasetVersion(datasetAndDatasetVersion.datasetVersion, dataset);

                this.setState({
                    dataset: dataset, datasetVersion: datasetVersion
                });
            }
            else if ((datasetAndDatasetVersion as Models.Dataset).id) {
                // It means we received a Models.Dataset, we need to get the last datasetVersion now
                // TODO: get_dataset_version_with_dataset should really return a dataset with datasetVersion, and we should not do this extra step
                dataset = new Models.Dataset(datasetAndDatasetVersion);
                return this.getTapi().get_dataset_version_last(dataset.id).then((last_datasetVersion) => {
                    datasetVersion = new DatasetVersion(last_datasetVersion, dataset);
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
            console.log("Error: " + error.stack);
            return Promise.reject("Dataset Version " + this.props.match.params.datasetVersionId + " does not exist");
        });
    }

    // TODO: Refactor logAccess in an util or in RecentlyViewed class
    logAccess() {
        return this.getTapi().create_or_update_entry_access_log(this.state.dataset.id).then(() => {
        });
    }

    getActivityLog() {
        return this.getTapi()
            .get_activity_log_for_dataset_id(
                this.state.dataset.id
            )
            .then((r: Array<ActivityLogEntry>) => {
                this.setState({ activityLog: r });
            });
    }

    getFigshareUrl() {
        this.getTapi().get_figshare_article_public_url(this.state.datasetVersion.id).then((v) => this.setState(v))
    }

    updateName(name: string) {
        this.getTapi()
			.update_dataset_name(
				this.state.datasetVersion.dataset_id,
				name
			)
			.then(() => {
				this.getActivityLog();
				return this.doFetch();
			});
    }

    updateDescription(description: string) {
        this.getTapi()
			.update_dataset_version_description(
				this.state.datasetVersion.id,
				description
			)
			.then(() => {
				this.getActivityLog();
				return this.doFetch();
			});
    }

    getLinkOrNot(dataset_version: NamedId) {
        let dataset = this.state.dataset;
        if (dataset_version.id === this.state.datasetVersion.id) {
            return <span>{dataset_version.name}</span>;
        }
        else {
            let last_index_dataset_permaname = dataset.permanames.length - 1;
            let url = relativePath("/dataset/" +
                dataset.permanames[last_index_dataset_permaname] +
                "/" + dataset_version.name);

            let link = null;

            link = <Link to={url}>{dataset_version.name}</Link>;

            return link;
        }
    }

    // Upload
    showUploadNewVersion() {
        this.setState({
            showUploadDataset: true
        });
    }

    // filesUploadedAndConverted(sid: string, name: string, description: string, previousDatafileIds: Array<string>) {
    //     let datafileIds = previousDatafileIds;
    //     // We ask to create the dataset
    //     return this.getTapi().create_new_dataset_version(sid,
    //         this.state.dataset.id,
    //         description
    //     ).then((dataset_version_id) => {
    //         // We fetch the datasetVersion of the newly created dataset and change the state of it
    //         return this.getTapi().get_dataset_version(dataset_version_id).then((newDatasetVersion) => {
    //             this.doFetch();
    //             return Promise.resolve(newDatasetVersion);
    //         });
    //     }).catch((err: any) => {
    //         console.log(err);
    //         return Promise.reject(err);
    //     });
    // }

    // Download

    // Async function to wait
    delay(milliseconds: number) {
        return new Promise<void>(resolve => {
            setTimeout(resolve, milliseconds);
        });
    }

    getOrLaunchConversion(datasetPermaname: string, version: string, datasetVersionId: string,
        datafileName: string, format: string, force: string): Promise<any> {
        // Ask for conversion, if ok download. Else convert process and loading for user
        // Loading
        this.setLoading(true);

        return this.getTapi().get_datafile(datasetPermaname, version, datasetVersionId, datafileName, format, force)
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
            callbackIntoFolderAction: (folderId: string) => {
                this.getTapi().copy_to_folder([this.state.dataset.id], folderId).then(() => this.afterAction());
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
            if (err.message === "UNPROCESSABLE ENTITY") {
                let err_message_user = "Folder id is not valid. Please check it and retry :)";
                this.setState({
                    actionIntoFolderValidation: "error",
                    actionIntoFolderHelp: err_message_user
                });
            }
        })
    }

    removeAccessLogs(arrayAccessLogs: Array<Models.AccessLog>): Promise<any> {
        return this.getTapi().remove_entry_access_log(arrayAccessLogs).then(() => {

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

    // Deprecation
    askDeprecationReason() {
        // Fetch the deprecation pop-up
        this.setState({
            showDeprecationReason: true
        });
    }

    closeDeprecationReason() {
        this.setState({
            showDeprecationReason: false
        });
    }

    cancelDeprecation() {
        this.closeDeprecationReason();
    }

    deprecateDatasetVersion(reason: string) {
        // Send the deprecation to the server
        this.getTapi().deprecate_dataset_version(this.state.datasetVersion.id, reason).then(() => {
            this.doFetch();
            this.closeDeprecationReason();
        });
    }

    deDeprecateDatasetVersion() {
        this.getTapi().de_deprecate_dataset_version(this.state.datasetVersion.id).then(() => {
            this.doFetch();
            this.closeDeprecationReason();
        });
    }

    // Deletion
    deleteDatasetVersion() {
        let confirmation_deletion = confirm("You are about to delete permanently this version of the dataset. Are you sure?");

        if (confirmation_deletion) {
            this.getTapi().delete_dataset_version(this.state.datasetVersion.id).then(() => {
                // Change the labels on the right. Remove deprecation and remove deletion
                this.doFetch();
            });
        }
    }

    // Figshare
    showUploadToFigshare() {
        this.setState({ showUploadToFigshare: true });
    }

    handleCloseUploadToFigshare(
        uploadComplete: boolean, figsharePrivateUrl: string
    ) {
        if (uploadComplete) {
            this.doFetch().then(() => {
                this.setState({
                    showUploadToFigshare: false,
                    figshare_public_url: figsharePrivateUrl
                });
            });
        } else {
            this.setState({
                showUploadToFigshare: false,
                figshare_public_url: figsharePrivateUrl
            });
        }
    }

    getCopyButton(datafile: Models.DatasetVersionDatafiles) {
        if (this.state.datasetVersion.state !== StatusEnum.Deleted) {
            let dataset = this.state.dataset;
            let datasetVersion = this.state.datasetVersion;


            let clipboard_content = dataset.permanames + "." + datasetVersion.version + "/" + datafile.name;
            const tooltip_copied = (
                <Tooltip id="token_copy_confirmation"><strong>Copied!</strong></Tooltip>
            );

            return <OverlayTrigger placement="left" trigger="click" overlay={tooltip_copied} rootClose={true}>
                <ClipboardButton data-clipboard-text={clipboard_content} className="btn btn-default">
                    Copy
                </ClipboardButton>
            </OverlayTrigger>;
        }
    }

    getConversionTypesOutput(datafile: Models.DatasetVersionDatafiles) {
        if (this.state.datasetVersion.state !== StatusEnum.Deleted) {
            return datafile.allowed_conversion_type.map((conversionType, index) => {
                let dataset = this.state.dataset;
                let datasetVersion = this.state.datasetVersion;

                // TODO: If we have the same name for datafiles, we will run into troubles
                return <span key={conversionType}>
                    <a href="#" onClick={() => {
                        this.setLoadingMessage("Sent the request to the server...");
                        return this.getOrLaunchConversion(undefined, undefined,
                            datasetVersion.id, datafile.name, conversionType, "N");
                    }}>
                        {conversionType}
                    </a>
                    {datafile.allowed_conversion_type.length !== index + 1 &&
                        <span>, </span>
                    }
                </span>;
            });
        }
    }

    onlyRawAvailable(df: Models.DatasetVersionDatafiles): boolean {
        const onlyRawAvailable =
            df.allowed_conversion_type.length == 1 &&
            df.allowed_conversion_type[0] == "raw";
        return onlyRawAvailable;
    }

    activityLogTypeFormatter(cell: ActivityTypeEnum, row: ActivityLogEntry) {
        if (cell == ActivityTypeEnum.created) {
			return (
				<div>
					<div>
						Created dataset{" "}
						<strong>
							{
								(row as CreationActivityLogEntry)
									.dataset_name
							}
						</strong>
					</div>
					{descriptionDetailsFormatter(
						(row as CreationActivityLogEntry)
							.dataset_description
					)}
				</div>
			);
		} else if (cell == ActivityTypeEnum.changed_name) {
			return (
				<span>
					Changed name to{" "}
					<strong>
						{(row as NameUpdateActivity).dataset_name}
					</strong>
				</span>
			);
		} else if (cell == ActivityTypeEnum.changed_description) {
			const changeDescriptionAction = !!(row as DescriptionUpdateActivity)
				.dataset_description
				? "Changed"
				: "Deleted";
			return (
				<div>
					<div>
						{`${changeDescriptionAction} description for version `}
						<strong>
							{
								(row as DescriptionUpdateActivity)
									.dataset_version
							}
						</strong>
					</div>
					{descriptionDetailsFormatter(
						(row as DescriptionUpdateActivity)
							.dataset_description
					)}
				</div>
			);
		} else if (cell == ActivityTypeEnum.added_version) {
			return (
				<div>
					<div>
						Added dataset version{" "}
						<strong>
							{
								(row as VersionAdditionActivity)
									.dataset_version
							}
						</strong>
					</div>
					{descriptionDetailsFormatter(row.comments, "Changelog")}
					{descriptionDetailsFormatter(
						(row as VersionAdditionActivity)
							.dataset_description
					)}
				</div>
			);
		} else if (cell == ActivityTypeEnum.started_log) {
			return (
				<div>
					<div>
						Logs started for{" "}
						<strong>
							{(row as LogStartActivity).dataset_name}
						</strong>{" "}
						version{" "}
						<strong>
							{(row as LogStartActivity).dataset_version}
						</strong>
					</div>
					{descriptionDetailsFormatter(
						(row as LogStartActivity).dataset_description
					)}
				</div>
			);
		}
		return cell;
    }

    activityLogDateFormatter(cell: string, row: ActivityLogEntry): string {
        return new Date(cell).toLocaleString();
    }

    renderActivityLog() {
        if (!this.state.activityLog) {
			return null;
        }
		const options = {
			noDataText: "No activity logged yet",
			defaultSortName: "timestamp",
			defaultSortOrder: "desc"
		};
		return (
			<React.Fragment>
				<h2>Activity Log</h2>
				<BootstrapTable
					data={this.state.activityLog}
					options={options}
					pagination
					striped
				>
					<TableHeaderColumn dataField="id" isKey hidden>
						ID
					</TableHeaderColumn>
					<TableHeaderColumn
						dataField="timestamp"
						dataFormat={this.activityLogDateFormatter}
						dataSort
						width="200"
					>
						Date
					</TableHeaderColumn>
					<TableHeaderColumn
						dataField="user_name"
						dataSort
						width="150"
					>
						Editor
					</TableHeaderColumn>
					<TableHeaderColumn
						dataField="type"
						dataFormat={this.activityLogTypeFormatter}
					>
						Type
					</TableHeaderColumn>
				</BootstrapTable>
			</React.Fragment>
		);
    }

    renderChangesDescription() {
        const { datasetVersion } = this.state;
        if (!datasetVersion || !datasetVersion.changes_description) {
          return null;
        }

        return (
          <React.Fragment>
            <h4>Changes this version</h4>
            {Dialogs.renderDescription(
              datasetVersion.changes_description
            )}
          </React.Fragment>
        );
    }

    render() {
        if (!this.state) {
            return <div>
                <LeftNav items={[]} />
                <div id="main-content">
                    Loading...
                </div>
            </div>;
        }
        else if (this.state && this.state.fetchError) {
            let message = "Dataset version " + this.props.match.params.datasetVersionId + " does not exist. Please check this id "
                + "is correct. We are also available via the feedback button.";
            return <div>
                <LeftNav items={[]} />
                <div id="main-content">
                    <NotFound message={message} />
                </div>
            </div>;
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
                        {dataset.versions.length !== index + 1 &&
                            <span>, </span>
                        }
                    </span>;
                });

                folders = dataset.folders.map((f, index) => {
                    return (
                        <span key={index}>
                            <Link to={relativePath("folder/" + f.id)}>
                                {f.name}
                            </Link>
                            {dataset.folders.length !== index + 1 &&
                                <span>, </span>
                            }
                        </span>
                    );
                });
            }

            let entries = null;
            if (datasetVersion) {
                entries = datasetVersion.datafiles.sort((datafile_one, datafile_two) => {
                    let datafile_one_upper = datafile_one.name.toUpperCase();
                    let datafile_two_upper = datafile_two.name.toUpperCase();
                    if (datafile_one_upper === datafile_two_upper) {
                        return 0;
                    }
                    else if (datafile_one_upper > datafile_two_upper) {
                        return 1;
                    }
                    else {
                        return -1;
                    }
                }).map((df, index) => {

                    let conversionTypesOutput = this.getConversionTypesOutput(df);
                    let copy_button = this.getCopyButton(df);

                    let linkToUnderlying = null;
                    let gsPath = null;
                    if (df.underlying_file_id) {
                        let m = df.underlying_file_id.match(/([^.]+)\.([^/]+)\/.+/);

                        let permaname = m[1];
                        let version = m[2];

                        linkToUnderlying = <div> (<Link to={relativePath("dataset/" + permaname + "/" + version)}>
                            {df.underlying_file_id}
                        </Link>)</div>
                    }
                    if (df.gcs_path) {
                        gsPath = <div>({"gs://" + df.gcs_path})</div>;
                    }

                    return <tr key={index}>
                        <td>{df.name}{linkToUnderlying}{gsPath}</td>
                        <td>{df.short_summary}</td>
                        {this.state.datasetVersion.figshare_linked && (
                                <td>
                                    {df.figshare_linked && <i className="fa fa-check" aria-label="yes"></i>}
                                </td>
                            )}
                        <td>
                            {conversionTypesOutput}
                        </td>
                        <td>
                            {copy_button}
                        </td>
                    </tr>;
                });
            }


            let navItems = [];

            navItems.push({
                label: "Share dataset", action: () => {
                    this.setState({ showShareDatasetVersion: true });
                }
            });

            // TODO: Look into why we are here despite the fact dataset is undefined
            if (dataset && dataset.can_edit) {
                navItems.push({
                    label: "Edit name", action: () => {
                        this.setState({ showEditName: true })
                    }
                },
                    {
                        label: "Edit description", action: () => {
                            this.setState({ showEditDescription: true })
                        }
                    },
                    {
                        label: "Edit permissions", action: () => {
                            this.setState({ showEditPermissions: true })
                        }
                    });
            }
            if (datasetVersion && datasetVersion.can_edit) {
                navItems.push({
                    label: "Create new version", action: () => {
                        this.showUploadNewVersion();
                    }
                });
                if (datasetVersion.state === StatusEnum.Approved) {
                    navItems.push({
                        label: "Deprecate this version", action: () => {
                            this.askDeprecationReason();
                        }
                    });
                } else if (datasetVersion.state === StatusEnum.Deprecated) {
                    navItems.push({
                        label: "De-deprecate this version", action: () => {
                            this.deDeprecateDatasetVersion();
                        }
                    });
                    navItems.push({
                        label: "Delete this version", action: () => {
                            this.deleteDatasetVersion();
                        }
                    });
                } else if (datasetVersion.state === StatusEnum.Deleted) {
                    // Don't add anything so we can't change the state anymore
                }
            }

            navItems.push(
                // {
                //     label: "Add permaname", action: function () {
                // }
                // },
                {
                    label: "Add to Home", action: () => {
                        this.copyTo(this.props.user.home_folder_id);
                    }
                },
                {
                    label: "Add to a folder", action: () => {
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
            );

            let permaname: string = null;
            let r_block = null;
            let python_block = null;
            let leftNavsDialogs = null;

            if (dataset && datasetVersion) {
                permaname = dataset.permanames[dataset.permanames.length - 1];
                r_block = "library(taigr);\n";

                const s3AndVirtualDatafiles = datasetVersion.datafiles.filter(df => !df.gcs_path);

                let r_block_lines = s3AndVirtualDatafiles.map((df, index) => {
                    let r_name = df.name.replace(/[^A-Za-z0-9]+/g, ".");
                    if (this.onlyRawAvailable(df)) {
                        return `${r_name} <- download.raw.from.taiga(data.name='${permaname}', data.version=${datasetVersion.version}, data.file='${df.name}')`;
                    }
                    else {
                        return `${r_name} <- load.from.taiga(data.name='${permaname}', data.version=${datasetVersion.version}, data.file='${df.name}')`;
                    }
                });
                r_block += r_block_lines.join("\n");

                python_block = "from taigapy import TaigaClient\n";
                python_block += "tc = TaigaClient()\n";

                let python_block_lines = s3AndVirtualDatafiles.map((df, index) => {
                    let python_name = df.name.replace(/[^A-Za-z0-9]+/g, "_");;

                    if (this.onlyRawAvailable(df)) {
                        return `${python_name} = tc.download_to_cache(name='${permaname}', version=${datasetVersion.version}, file='${df.name}')  # download_to_cache for raw`;
                    }
                    else {
                        return `${python_name} = tc.get(name='${permaname}', version=${datasetVersion.version}, file='${df.name}')`;
                    }
                });
                python_block += python_block_lines.join("\n");

                leftNavsDialogs = (
                    <span>
                        <Dialogs.EditName isVisible={this.state.showEditName}
                            initialValue={this.state.dataset.name}
                            cancel={() => {
                                this.setState({ showEditName: false })
                            }}
                            save={(name: string) => {
                                this.setState({ showEditName: false });
                                this.updateName(name)
                            }} />
                        <Dialogs.EditDescription isVisible={this.state.showEditDescription}
                            cancel={() => {
                                this.setState({ showEditDescription: false })
                            }}
                            initialValue={this.state.datasetVersion.description}
                            save={(description: string) => {
                                this.setState({ showEditDescription: false });
                                console.log("Save description: " + description);
                                this.updateDescription(description);
                            }} />
                        {this.state.showUploadDataset &&
                            <CreateVersionDialog
                                datasetId={this.state.dataset.id}
                                isVisible={this.state.showUploadDataset}
                                cancel={() => {
                                    this.setState({ showUploadDataset: false })
                                }}
                                upload={this.uploadTracker.upload.bind(this.uploadTracker)}
                                datasetName={this.state.dataset.name}
                                previousDescription={this.state.datasetVersion.description}
                                previousVersionNumber={this.state.datasetVersion.name}
                                previousVersionFiles={this.state.datasetVersion.datafiles}
                                datasetPermaname={this.state.dataset.permanames[0]}
                            />}
                        
                        <UploadToFigshare
                            tapi={this.props.tapi}
                            handleClose={(uploadComplete, figsharePrivateUrl) =>
                                this.handleCloseUploadToFigshare(
                                    uploadComplete, figsharePrivateUrl
                                )
                            }
                            show={this.state.showUploadToFigshare}
                            userFigshareLinked={this.props.user.figshare_linked}
                            datasetVersion={this.state.datasetVersion}
                        />

                        <Dialogs.InputFolderId
                            actionDescription="Link this dataset into the chosen folder"
                            isVisible={this.state.showInputFolderId}
                            cancel={() => {
                                this.setState({ showInputFolderId: false })
                            }}
                            save={(folderId) => {
                                this.state.callbackIntoFolderAction(folderId)
                            }}
                            initFolderId={this.state.initInputFolderId}
                        />

                        <EntryUsersPermissions
                            isVisible={this.state.showEditPermissions}
                            cancel={() => {
                                this.setState({ showEditPermissions: false })
                            }}
                            entry_id={this.state.dataset.id}
                            handleDeletedRow={(arrayAccessLogs) => {
                                return this.removeAccessLogs(arrayAccessLogs)
                            }}
                            tapi={this.props.tapi}
                        />
                        <Dialogs.ShareEntries isVisible={this.state.showShareDatasetVersion}
                            cancel={() => {
                                this.setState({ showShareDatasetVersion: false });
                            }}
                            entries={[this.state.datasetVersion]}
                        />
                    </span>
                );
            }

            return <div>
                <LeftNav items={navItems} />
                <div id="main-content">
                    {dataset && datasetVersion &&
                        <span>
                            {leftNavsDialogs}

                            <h1>
                                {dataset.name}
                                &nbsp;
                            <small>{permaname}</small>
                                {this.state.datasetVersion.state === StatusEnum.Deprecated &&
                                    <span>&nbsp;
                                <small className="glyphicon glyphicon-warning-sign"
                                            style={deprecationTitle}>Deprecated</small>
                                    </span>
                                }
                                {this.state.datasetVersion.state === StatusEnum.Deleted &&
                                    <span>&nbsp;
                                <small className="glyphicon glyphicon-exclamation-sign"
                                            style={deletionTitle}>Deleted</small>
                                    </span>
                                }
                            </h1>
                            <p>Version {datasetVersion.version} created by {datasetVersion.creator.name}
                                &nbsp;on the {toLocalDateString(datasetVersion.creation_date)}</p>
                            <p>Versions: {versions} </p>

                            {folders.length > 0 &&
                                <p>Contained within {folders}</p>
                            }

                            {this.state.datasetVersion.state === StatusEnum.Deprecated &&
                                <div className="well well-sm" style={deprecationStyle}>
                                    <i>Deprecation reason:</i>
                                    <br />
                                    <span>&emsp;{this.state.datasetVersion.reason_state}</span>
                                </div>
                            }

                            {this.state.datasetVersion.figshare_linked ? (
                                this.state.figshare_public_url ? (
                                    <Button
                                        bsSize="xs"
                                        bsStyle="link"
                                        href={this.state.figshare_public_url}
                                        target="_blank"
                                    >
                                        See the Figshare article created from this
                                        dataset version{" "}
                                        <i
                                            className="fa fa-external-link"
                                            aria-hidden="true"
                                        ></i>
                                    </Button>
                                ) : (
                                    <Button
                                        bsSize="xs"
                                        bsStyle="link"
                                        disabled={true}
                                    >
                                        This dataset version is linked to a private
                                        article on Figshare.
                                    </Button>
                                )
                            ) : (
                                <Button
                                    bsSize="xs"
                                    onClick={() => this.showUploadToFigshare()}
                                >
                                    Upload to Figshare
                                </Button>
                            )}

                        {this.state.datasetVersion.description &&
                                Dialogs.renderDescription(this.state.datasetVersion.description)
                            }

                            {this.renderChangesDescription()}

                            <h2>Contents</h2>
                            <table className="table">
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        {/*<th>Description</th>*/}
                                        <th>Summary</th>
                                        {this.state.datasetVersion.figshare_linked && <th>Uploaded to Figshare</th>}
                                        <th>Download</th>
                                        <th>Datafile Id</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {entries}
                                </tbody>
                            </table>


                            <h2>Direct access from R (<a
                                href="https://github.com/broadinstitute/taigr"
                                target="_blank">TaigR Documentation</a>)</h2>
                            <pre>{r_block}</pre>
                            <h2>
                                Direct access from Python (<a
                                    href="https://github.com/broadinstitute/taigapy"
                                    target="_blank">Taigapy Documentation</a>)
                            </h2>
                            <pre>{python_block}</pre>

                            {this.renderActivityLog()}

                            </span>
                    }
                </div>
                {this.state.loading && <LoadingOverlay message={this.state.loadingMessage}></LoadingOverlay>}
                <Dialogs.ExportError isVisible={this.state.exportError}
                    cancel={() => this.setState({ exportError: false })}
                    retry={() => this.forceExport()}
                    message={this.state.loadingMessage} />

                <Dialogs.DeprecationReason isVisible={this.state.showDeprecationReason}
                    cancel={() => this.cancelDeprecation()}
                    save={(reason) => this.deprecateDatasetVersion(reason)}
                />
            </div>;
        }
    }
}


