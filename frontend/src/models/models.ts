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
        DatasetVersion = <any> 'dataset_version'
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

export type StatusEnum = "deleted" | "valid" | "deprecated";

export interface DatasetVersion {
    "id": string;
    "dataset_id": string;
    "status": StatusEnum;
    "name": string;
    "version": string;
    "description"?: string;
    "creation_date": string;
    "creator": NamedId;
    "datafiles": Array<DatasetVersionDatafiles>;
    folders: Array<NamedId>;
}

export interface DatasetVersionDatafiles {
    "name"?: string;
    "url"?: string;
    "mimeType"?: string;
    "description"?: string;
}

export interface DatasetVersions {
    "name": string;
    "id": string;
    "status": StatusEnum;
}

export interface Dataset {
    "id": string;
    "name": string;
    "permanames": Array<string>;
    "description": string;
    "versions": Array<DatasetVersions>;
}

