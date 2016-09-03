//import * as Fetch from 'whatwg-fetch';

import { User, Folder, Dataset, DatasetVersion } from './models';

export class TaigaApi {
    baseUrl : string;

    constructor(baseUrl : string) {
        this.baseUrl = baseUrl;
    }

    _fetch<T>(url : string) : Promise<T> {
        return window.fetch(this.baseUrl + url)
            .then(function(response: Response) : Promise<Response> {
                if (response.status >= 200 && response.status < 300) {  
                    return Promise.resolve(response)  
                } else {  
                    return Promise.reject<Response>(new Error(response.statusText))  
                }  
            })
            .then( (response : Response) => response.json() )
    }

    get_user() : Promise<User> {
        return this._fetch<User>("/user")
    }

    get_folder(folderId : string) : Promise<Folder> {
        return this._fetch<Folder>("/folder/"+folderId)
    }

    get_dataset(dataset_id : string) : Promise<Dataset> {
        return this._fetch<Dataset>("/dataset/"+dataset_id)
    }
    
    get_dataset_version(dataset_version_id: string) : Promise<DatasetVersion> {
        return this._fetch<DatasetVersion>("/datasetVersion/"+dataset_version_id)
    }
}

