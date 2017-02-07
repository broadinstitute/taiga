
export class Folder {
    id: string;
    name: string;
    type: Folder.TypeEnum;
    parents: Array<NamedId>;
    entries: Array<FolderEntries>;
    description: string;
    creator: NamedId;
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

export interface DatasetAndDatasetVersion {
    "dataset": Dataset;
    "datasetVersion": DatasetVersion;
}

export interface DatasetVersionDatafiles {
    "name": string;
    "url": string;
    "type": DataFileType;
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
    "folders": Array<NamedId>;
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

export interface S3UploadedData {
    Location: string;
    ETag: string;
    Bucket: string;
    Key: string;
}

export class S3UploadedFileMetadata {
    location: string;
    eTag: string;
    bucket: string;
    key: string;
    filename: string;
    filetype: string;

    constructor(uploadS3Data: S3UploadedData, filename: string, filetype: InitialFileType) {
        this.location = uploadS3Data.Location;
        this.eTag = uploadS3Data.ETag;
        this.bucket = uploadS3Data.Bucket;
        this.key = uploadS3Data.Key;

        this.filename = filename;
        this.filetype = filetype.toString();
    }
}

// Upload
export class FileUploadStatus {
    file: File;

    // These exist because of special needs for react-bootstrap-table. See https://github.com/AllenFang/react-bootstrap-table/issues/50
    fileName: string;
    mimeType: string;
    fileType: InitialFileType;
    fileSize: number;

    s3Key: string;

    progress: number;
    conversionProgress: string;

    constructor(file: File, s3Prefix: string) {
        this.file = file;

        this.fileName = this.file.name;
        this.mimeType = this.file.type;
        this.fileSize = this.file.size

        this.progress = 0;
        this.conversionProgress = '';

        this.s3Key = s3Prefix + this.fileName;
    }

    recreateS3Key(prefix: string) {
        this.s3Key = prefix + this.fileName;
    }
}

export class TaskStatus {
    id: string;
    state: string;
    message: string;
    current: string;
    total: string;
    s3Key: string;
}

// IMPORTANT: Need to sync with backend for each changes
export enum InitialFileType {
    NumericMatrixCSV = <any> 'NumericMatrixCSV',
    NumericMatrixTSV = <any> 'NumericMatrixTSV',
    Table = <any> 'Table',
    GCT = <any> 'GCT',
    Raw = <any> 'Raw'
}

export enum DataFileType {
    Raw = <any> 'Raw',
    HDF5 = <any> 'HDF5',
    Columnar = <any> 'Columnar'
}
