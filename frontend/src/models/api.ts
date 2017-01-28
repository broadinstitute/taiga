import 'whatwg-fetch';

import { User, Folder, Dataset, DatasetVersion, S3Credentials,
    TaskStatus, DatasetAndDatasetVersion } from './models';

export class TaigaApi {
    baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    _fetch<T>(url: string): Promise<T> {
        return window.fetch(this.baseUrl + url)
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
                "Accept": "application/json"
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

    get_dataset_version_with_dataset(datasetId: string, datasetVersionId: string) {
        let dsAndDv = this._fetch<DatasetAndDatasetVersion>("/dataset/" + datasetId + "/" + datasetVersionId)

        return dsAndDv;
    }

    get_dataset_version_first(dataset_id: string): Promise<DatasetVersion> {
        return this._fetch<DatasetVersion>("/dataset/" + dataset_id + "/first")
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

    update_folder_name(folder_id: string, name: string) {
        return this._post<void>("/folder/" + folder_id + "/name", {name: name})
    }

    update_folder_description(folder_id: string, description: string) {
        return this._post<void>("/folder/" + folder_id + "/description", {description: description})
    }

    create_datafile(location: string, eTag: string, bucket: string, key: string, filetype: string, sid: string) {
        return this._post<string>("/datafile/" + sid, {
            location: location, eTag: eTag,
            bucket: bucket, key: key,
            filetype: filetype
        })
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
}

