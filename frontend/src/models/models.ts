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

export interface SignedS3Post {
    // Example:
    // {'url': 'https://broadtaiga2prototype.s3.amazonaws.com/',
    //  'fields': {'AWSAccessKeyId': 'AKIAIRDC67MDYNGUJ6PQ',
    //      'policy': 'eyJleHBpcmF0aW9uIjogIjIwMTYtMTItMTBUMDA6NDQ6MDdaIiwgImNvbmRpdGlvbnMiOiBbeyJidWNrZXQiOiAiYnJvYWR0YWlnYTJwcm90b3R5cGUifSwgeyJrZXkiOiAiZjY2ODA3NDdhOWQ3NDRmZjgwNjIxYzA3ZDAyYTljNWEifV19',
    //      'signature': 'ifqmpadPwJY0IneKbIzxcfF42Wg=',
    //      'key': 'f6680747a9d744ff80621c07d02a9c5a'}
    // }

    url: string;
    fields: SignedS3PostFields;
}

export interface S3Credentials {
    accessKeyId: string;
    expiration: string;
    secretAccessKey: string;
    sessionToken: string;
}

interface SignedS3PostFields {
    AWSAccessKeyId: string;
    policy: string;
    signature: string;
    key: string
}
