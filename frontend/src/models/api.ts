//import * as Fetch from 'whatwg-fetch';

import { User, Folder } from './models';

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
}

