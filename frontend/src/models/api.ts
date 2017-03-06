import 'whatwg-fetch';

import {
    User, Folder, Dataset, DatasetVersion, S3Credentials,
    TaskStatus, DatasetAndDatasetVersion, S3UploadedFileMetadata, NamedId
} from './models';

import { currentUserToken } from '../utilities/route';
import {isUndefined} from "util";
import {Token} from "../components/Token";
import {isNullOrUndefined} from "util";

export class TaigaApi {
    baseUrl: string;
    authHeaders: any;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
        // TODO: Don't pass the name and email as clear strings. We could use a hash function shared between api_app and ui_app to encode/decode
        this.authHeaders = {
            "auth": "Bearer "+currentUserToken
        }
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
            .then<T>((response: Response) => response.json())
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
            .then<T>((response: Response) => response.json())
    }

    get_user(): Promise<User> {
        return this._fetch<User>("/user")
    }

    get_folder(folderId: string): Promise<Folder> {
        return this._fetch<Folder>("/folder/" + folderId)
    }

    get_dataset(dataset_id: string): Promise<Dataset> {
        return this._fetch<Dataset>("/dataset/" + dataset_id)
    }

    get_dataset_version(dataset_version_id: string): Promise<DatasetVersion> {
        return this._fetch<DatasetVersion>("/datasetVersion/" + dataset_version_id)
    }

    get_dataset_version_with_dataset(datasetId: string, datasetVersionId?: string) {
        // If not datasetVersion is passed, return the first datasetVersion
        let dsAndDv;
        if (isUndefined(datasetVersionId)) {
            dsAndDv = this._fetch<DatasetAndDatasetVersion>("/dataset/" + datasetId);
        }
        else {
            dsAndDv = this._fetch<DatasetAndDatasetVersion>("/dataset/" + datasetId + "/" + datasetVersionId);
        }

        return dsAndDv;
    }

    get_dataset_version_first(dataset_id: string): Promise<DatasetVersion> {
        return this._fetch<DatasetVersion>("/dataset/" + dataset_id + "/first")
    }

    get_dataset_version_last(dataset_id: string): Promise<DatasetVersion> {
        return this._fetch<DatasetVersion>("/dataset/" + dataset_id + "/last")
    }

    get_s3_credentials(): Promise<S3Credentials> {
        return this._fetch<S3Credentials>("/credentials_s3")
    }

    get_upload_session(): Promise<string> {
        return this._fetch<string>("/upload_session")
    }

    update_dataset_name(dataset_id: string, name: string) {
        return this._post<void>("/dataset/" + dataset_id + "/name", {name: name})
    }

    update_dataset_description(dataset_id: string, description: string) {
        return this._post<void>("/dataset/" + dataset_id + "/description", {description: description})
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
}

