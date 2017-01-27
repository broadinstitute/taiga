export class Folder {
    'id': string;
    'name': string;
    'type': Folder.TypeEnum;
    'parents': Array<NamedId>;
    'entries': Array<FolderEntries>;
    description: string;
    acl: Acl;
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
    'creation_date': string;
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
    provenance?: Provenance;
}

export interface DatasetVersionDatafiles {
    "name": string;
    "url": string;
    "mimeType": string;
    "description": string;
    "content_summary": string;
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
    acl: Acl;
}

interface Method {
    description: string;
    parameters: string;
}

interface ProvSource {
    dataset_version_id : string;
    name : string;
    method_parameter : string;
    dataset_version_name? : string;
}

export interface Provenance {
    method: Method;
    inputs: Array<ProvSource>;
}

interface Grant {
    type: string;
    id: string;
    name: string;
    permission: string;
}

interface Acl {
    default_permissions: string;
    grants: Array<Grant>;
}

export interface S3Credentials {
    accessKeyId: string;
    expiration: string;
    secretAccessKey: string;
    sessionToken: string;
    bucket: string;
    prefix: string;
}

// Upload
export class FileUploadStatus {
    file: File;

    // These exist because of special needs for react-bootstrap-table. See https://github.com/AllenFang/react-bootstrap-table/issues/50
    fileName: string;
    fileType: string;
    fileSize: number;

    progress: number;
    conversionProgress: string;

    constructor(file: File) {
        this.file = file;

        this.fileName = this.file.name;
        this.fileType = this.file.type;
        this.fileSize = this.file.size

        this.progress = 0;
        this.conversionProgress = '';
    }
}

export class TaskStatus {
    id: string;
    state: string;
    message: string;
    current: string;
    total: string;
    fileName: string;
}
