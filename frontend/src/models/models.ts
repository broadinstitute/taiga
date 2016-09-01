export class Folder {
    'id': string;
    'name': string;
    'type': Folder.TypeEnum;
    'parents': Array<NamedId>;
    'entries': Array<FolderEntries>;
}

export namespace Folder {
    export enum TypeEnum {
        Folder = <any> 'folder',
        Trash = <any> 'trash',
        Home = <any> 'home'
    }
}
export class FolderEntries {
    'type': FolderEntries.TypeEnum;
    'id': string;
    'name': string;
    'creationDate': string;
    'creator': NamedId;
}

export namespace FolderEntries {
    export enum TypeEnum {
        Folder = <any> 'folder',
        Dataset = <any> 'dataset',
        DatasetVersion = <any> 'datasetVersion'
    }
}

export class NamedId {
    'name': string;
    'id': string;
}

export interface User {
    "id": string;
    "name": string;
    "home_folder_id": string;
    "trash_folder_id": string;
}
