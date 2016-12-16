// import * as fetch from 'whatwg-fetch';

// import * as AWS from "aws-sdk";

import 'whatwg-fetch';

import { User, Folder, Dataset, DatasetVersion, S3Credentials } from './models';

export class TaigaApi {
    baseUrl : string;

    constructor(baseUrl : string) {
        this.baseUrl = baseUrl;
    }

    _fetch<T>(url : string) : Promise<any> {
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

    _post<T>(url: string, args : any) : Promise<any> {
        return window.fetch(this.baseUrl + url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify(args)})
            .then(function(response: Response) : Promise<Response> {
                if (response.status >= 200 && response.status < 300) {  
                    return Promise.resolve(response)  
                } else {  
                    return Promise.reject<Response>(new Error(response.statusText))  
                }  
            })
            .then( (response : Response) => response.json() )
    }

    _post_upload<T>(url: string, file: any) : Promise<any> {
        debugger;
        //let s3 = new AWS.S3();
/*
        let params = {
            Bucket: '',
            Key: '',
            Body: ''
        };
        return s3.putObject(params).promise()
            .then(function(response: Response) : Promise<Response> {
                if (response.status >= 200 && response.status < 300) {
                    return Promise.resolve(response)
                } else {
                    return Promise.reject<Response>(new Error(response.statusText))
                }
            })
            .then( (response : Response) => response.json() )
            */
            return window.fetch(this.baseUrl + url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify(file)})
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

    get_s3_credentials() {
        return this._fetch<S3Credentials>("/credentials_s3")
    }

    update_dataset_name(dataset_id : string, name: string) {
        return this._post<void>("/dataset/"+dataset_id+"/name", {name: name})
    }

    update_dataset_description(dataset_id : string, description: string) {
        return this._post<void>("/dataset/"+dataset_id+"/description", {description: description})
    }

    update_folder_name(folder_id: string, name: string) {
        return this._post<void>("/folder/"+folder_id+"/name", {name: name})
    }

    update_folder_description(folder_id : string, description: string) {
        return this._post<void>("/folder/"+folder_id+"/description", {description: description})
    }
}

