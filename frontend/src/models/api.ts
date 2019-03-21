import 'whatwg-fetch';

import {
    User, Folder, Dataset, DatasetVersion, S3Credentials,
    TaskStatus, DatasetAndDatasetVersion, S3UploadedFileMetadata, NamedId, DatasetFullDatasetVersions,
    AccessLog, DatafileUrl, ProvenanceGraphFull, SearchResult
} from './models';

import { currentUserToken } from '../utilities/route';
import {isUndefined} from "util";
import {Token} from "../components/Token";
import {isNullOrUndefined} from "util";

export class TaigaApi {
    baseUrl: string;
    authHeaders: any;
    loading: boolean;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
        // TODO: Don't pass the name and email as clear strings. We could use a hash function shared between api_app and ui_app to encode/decode
        this.authHeaders = {
            "auth": "Bearer "+currentUserToken
        };
        this.loading = false;
    }

    _fetch<T>(url: string): Promise<T> {
        return window.fetch(this.baseUrl + url, {
            headers: {
                "Authorization": this.authHeaders.auth,
            }
        })
            .then(function (response: Response): Promise<Response> {
                if (response.status >= 200 && response.status < 300) {
                    return Promise.resolve(response)
                } else {
                    return Promise.reject<Response>(new Error(response.statusText))
                }
            })
            .then<T>((response: Response) => {
                return response.json();
            });
    }

    _post<T>(url: string, args: any): Promise<T> {
        return window.fetch(this.baseUrl + url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": this.authHeaders.auth
            },
            body: JSON.stringify(args)
        })
            .then((response: Response) => {
                if (response.status >= 200 && response.status < 300) {
                    return Promise.resolve(response)
                } else {
                    return Promise.reject<Response>(new Error(response.statusText))
                }
            })
            .then<T>((response: Response) => {
                return response.json();
            })
    }

    get_user(): Promise<User> {
        return this._fetch<User>("/user")
    }

    // TODO: Replace with FolderFullDatasetVersions
    get_folder(folderId: string): Promise<Folder> {
        return this._fetch<Folder>("/folder/" + folderId);
    }

    get_dataset(dataset_id: string): Promise<Dataset> {
        return this._fetch<Dataset>("/dataset/" + dataset_id)
    }

    get_user_entry_access_log(): Promise<Array<AccessLog>> {
        // TODO: Change this api to get a better meaning. We want all the entries for a specific user
        return this._fetch<Array<AccessLog>>("/entry/logAccess");
    }

    get_entry_access_log(entry_id): Promise<Array<AccessLog>> {
        // We fetch all the AccessLog for a specific entry
        return this._fetch<Array<AccessLog>>("/entry/" + entry_id + "/logAccess")
    }

    remove_entry_access_log(accessLogsToRemove: Array<AccessLog>) {
        return this._post<void>("/entry/logAccess/remove/all", accessLogsToRemove);
    }

    get_datasets(datasetIds: Array<string>): Promise<Array<DatasetFullDatasetVersions>> {
        // TODO: We should not use a post method for a get
        return this._post<Array<DatasetFullDatasetVersions>>("/datasets", {datasetIds: datasetIds})
    }

    get_dataset_version(dataset_version_id: string): Promise<DatasetVersion> {
        return this._fetch<DatasetVersion>("/datasetVersion/" + dataset_version_id)
    }

    get_datasetVersions(datasetVersionIds: Array<string>): Promise<Array<DatasetVersion>> {
        return this._post<Array<DatasetVersion>>("/datasetVersions", {datasetVersionIds: datasetVersionIds})
    }

    get_dataset_version_with_dataset(datasetId: string, datasetVersionId?: string) {
        // If not datasetVersion is passed, return the first datasetVersion
        let dsAndDv: Promise<DatasetAndDatasetVersion>;
        if (isUndefined(datasetVersionId)) {
            // TODO: This should not call the /dataset/{datasetId} api but a specific one to get the dataset and the last datasetVersion
            dsAndDv = this._fetch<DatasetAndDatasetVersion>("/dataset/" + datasetId);
        }
        else {
            dsAndDv = this._fetch<DatasetAndDatasetVersion>("/dataset/" + datasetId + "/" + datasetVersionId);
        }

        return dsAndDv;
    }

    get_dataset_version_last(dataset_id: string): Promise<DatasetVersion> {
        return this._fetch<DatasetVersion>("/dataset/" + dataset_id + "/last");
    }

    get_s3_credentials(): Promise<S3Credentials> {
        return this._fetch<S3Credentials>("/credentials_s3");
    }

    get_upload_session(): Promise<string> {
        return this._fetch<string>("/upload_session");
    }

    update_dataset_name(dataset_id: string, name: string) {
        return this._post<void>("/dataset/" + dataset_id + "/name", {name: name})
    }

    update_dataset_description(dataset_id: string, description: string) {
        return this._post<void>("/dataset/" + dataset_id + "/description", {description: description})
    }

    update_dataset_version_description(dataset_version_id: string, description: string) {
        return this._post<void>("/datasetVersion/" + dataset_version_id + "/description", {description: description})
    }

    create_folder(current_folder_id: string, current_user_id: string, name: string, description: string) {
        return this._post<NamedId>("/folder/create", {
            'creatorId': current_user_id,
            'parentId': current_folder_id,
            'name': name,
            'description': description
        });
    }

    update_folder_name(folder_id: string, name: string) {
        return this._post<void>("/folder/" + folder_id + "/name", {name: name})
    }

    update_folder_description(folder_id: string, description: string) {
        return this._post<void>("/folder/" + folder_id + "/description", {description: description})
    }

    create_datafile(sid: string, S3UploadedFileMetadata: S3UploadedFileMetadata) {
        return this._post<string>("/datafile/" + sid, S3UploadedFileMetadata)
    }

    get_datafile(datasetPermaname: string, datasetVersion: string,
                     datasetVersionId: string, datafileName: string,
                     format: string, force: string): Promise<DatafileUrl> {
        // Returns the url to launch/get status/retrieve the datafile
        // (datasetPermaname with datasetVersion OR datasetVersionId) and datafileName + format [+ force]
        // TODO: Support Permaname+Version. Currently only datasetVersionId
        let url = "/datafile?"
            + "dataset_version_id=" + datasetVersionId
            + "&"
            + "datafile_name=" + datafileName
            + "&"
            + "format=" + format
            + "&"
            + "force=" + force;

        return this._fetch<DatafileUrl>(url);
    }

    get_task_status(taskStatusId: string) {
        return this._fetch<TaskStatus>("/task_status/" + taskStatusId)
    }

    create_dataset(sid: string, datasetName: string, datasetDescription: string, currentFolderId: string) {
        return this._post<string>("/dataset", {
            sessionId: sid,
            datasetName: datasetName,
            datasetDescription: datasetDescription,
            currentFolderId: currentFolderId
        })
    }

    move_to_folder(entryIds: Array<string>, currentFolderId: string, targetFolderId: string) {
        if(isNullOrUndefined(targetFolderId)) {
            targetFolderId = "";
        }

        return this._post<void>("/move", {
            entryIds: entryIds,
            currentFolderId: currentFolderId,
            targetFolderId: targetFolderId
        })
    }

    copy_to_folder(entryIds: Array<string>, folderId: string) {
        return this._post<void>("/copy", {
            entryIds: entryIds,
            folderId: folderId
        })
    }

    create_new_dataset_version(sid: string, dataset_id: string, new_description: string, datafile_ids: Array<string>) {
        return this._post<string>("/datasetVersion", {
            sessionId: sid,
            datasetId: dataset_id,
            newDescription: new_description,
            datafileIds: datafile_ids
        })
    }

    create_or_update_entry_access_log(entry_id: string): Promise<void> {
        return this._post<void>("/entry/" + entry_id + "/logAccess", {});
    }

    get_provenance_graph(graph_id: string): Promise<ProvenanceGraphFull> {
        return this._fetch<ProvenanceGraphFull>("/provenance/" + graph_id);
    }

    // Search
    get_folder_search(current_folder_id: string, search_query: string): Promise<SearchResult> {
        return this._fetch<SearchResult>("/search/" + current_folder_id + "/" + search_query);
    }

    // Deprecation
    // TODO: Promise should return an ack or a failure
    deprecate_dataset_version(dataset_version_id: string, reason: string): Promise<void>{
        return this._post<void>(
            "/datasetVersion/" + dataset_version_id + "/deprecate",
            {deprecationReason: reason});
    }

    de_deprecate_dataset_version(dataset_version_id: string): Promise<void> {
        return this._post<void>(
            "/datasetVersion/" + dataset_version_id + "/de-deprecate", {}
            );
    }

    delete_dataset_version(dataset_version_id: string): Promise<void> {
        return this._post<void>(
            "/datasetVersion/" + dataset_version_id + "/delete", {}
            );
    }

    get_dataset_version_id(any_entry_identifier: string): Promise<string> {
        return this._fetch(
            "/datasetVersion/id/find?entry_submitted_by_user=" + any_entry_identifier
            );
    }
}
