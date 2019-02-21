import {getInitialFileTypeFromMimeType, toLocalDateString} from "../utilities/formats";
import {relativePath} from "../utilities/route";
import {process} from "ts-jest/dist/preprocessor";

export abstract class Entry {
    type: FolderEntriesTypeEnum;
    id: string;
    name: string;
    creation_date: string;
    creator: NamedId;

    constructor(data) {
       for (let key in data) {
        this[key] = data[key];
        }
    }

    abstract getRelativeLink();

    getFullUrl() {
        return window.location.origin + this.getRelativeLink();
    }

    getName() {
        return this.name;
    }
}

export class Folder extends Entry {
    folder_type: TypeFolderEnum;
    parents: Array<NamedId>;
    entries: Array<FolderEntries>;
    description: string;
    acl: Acl;
    can_view: boolean;
    can_edit: boolean;

    constructor(data) {
        super(data);

        this.entries.forEach((entry, index) => {
           this.entries[index] = new FolderEntries(entry);
        });
    }

    getRelativeLink() {
        return relativePath("/folder/" + this.id);
    }
}

export enum TypeFolderEnum {
    Folder = <any> "folder",
    Trash = <any> "trash",
    Home = <any> "home"
}

// TODO: Remove to instead use Entry and DatasetVersion/Dataset(/Folder) extending Entry
export class FolderEntries extends Entry {
    constructor(data) {
        super(data);
    }

    getRelativeLink() {
        if (this.type === FolderEntriesTypeEnum.Dataset) {
            return relativePath("/dataset/" + this.id);
        }
        else if (this.type === FolderEntriesTypeEnum.Folder) {
            return relativePath("/folder/" + this.id);
        }
        else {
            return "Not Implemented yet";
        }
    }
}

export enum FolderEntriesTypeEnum {
    Folder = <any> "folder",
    Dataset = <any> "dataset",
    DatasetVersion = <any> "dataset_version"
}

export class NamedId {
    name: string;
    id: string;
}

export interface User {
    "id": string;
    "name": string;
    "home_folder_id": string;
    "trash_folder_id": string;
    "token": string;
}

export enum StatusEnum {
  Deleted = "deleted",
  Approved = "approved",
  Deprecated = "deprecated"
}



export class DatasetVersion extends Entry {
    dataset_id: string;
    dataset: Dataset;
    state: StatusEnum;
    reason_state: string;
    version: string;
    description?: string;
    datafiles: Array<DatasetVersionDatafiles>;
    folders: Array<NamedId>;
    can_edit: boolean;
    can_view: boolean;

    constructor(data, dataset) {
        super(data);
        this.dataset = dataset;
    }

    getRelativeLink() {
        return relativePath("/dataset/" + this.dataset.permanames[0] + "/" + this.version);
    }

    getName() {
        // TODO: Retrieve the dataset to be able to print dataset name + version
        return "Version " + this.version;
    }
}

export interface DatasetAndDatasetVersion {
    dataset: Dataset;
    datasetVersion: DatasetVersion;
}

export interface DatasetVersionDatafiles {
    id: string;
    name: string;
    url: string;
    type: DataFileType;
    allowed_conversion_type: Array<string>;
    short_summary: string;
    provenance_nodes?: Array<ProvenanceNode>; // Array of urls to provenance graph
}

export interface DatasetVersions {
    "name": string;
    "id": string;
    "status": StatusEnum;
}

export class Dataset extends Entry {
    permanames: Array<string>;
    description: string;
    // TODO: Rename this and rework it, since it is "DatasetVersionNamedId" and not a true DatasetVersion(s)
    versions: Array<DatasetVersions>;
    acl: Acl;
    folders: Array<NamedId>;

    can_edit: boolean;
    can_view: boolean;

    getRelativeLink() {
        return relativePath("/dataset/" + this.permanames[0]);
    }
}

export interface DatasetFullDatasetVersions {
    id: string;
    name: string;
    permanames: Array<string>;
    description: string;
    versions: Array<DatasetVersion>;
    acl: Acl;
    // TODO: Should we stay without the full folders? Cyclic risks?
    folders: Array<NamedId>;
}

interface Method {
    description: string;
    parameters: string;
}

// interface ProvSource {
//     dataset_version_id: string;
//     name: string;
//     method_parameter: string;
//     dataset_version_name?: string;
// }
//
// export interface Provenance {
//     method: Method;
//     inputs: Array<ProvSource>;
// }

export interface ProvenanceGraphFull {
    graph_id: string;
    name: string;
    permaname: string;
    created_timestamp: string;
    created_by_user_id: string;
    provenance_nodes: Array<ProvenanceNodeFull>;
}

export interface ProvenanceNodeFull {
    node_id: string;
    from_edges: Array<ProvenanceEdgeFull>;
    to_edges: Array<ProvenanceEdgeFull>;
    label: string;
    type: ProvenanceNodeType;
    datafile_id: string;
    url: string;
}

export interface ProvenanceEdgeFull {
    edge_id: string;
    from_node_id: string;
    to_node_id: string;
    label: string;
}

export enum ProvenanceNodeType {
    Dataset = <any> 'Dataset',
    Process = <any> 'Process',
    External = <any> 'External'
}

export interface ProvenanceGraph {
    graph_id: string;
    name: string;
    permaname: string;
}

export interface ProvenanceNode {
    node_id: string;
    graph: ProvenanceGraph;
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

export function dropExtension(filename: string): string {
    var i = filename.lastIndexOf(".")
    if (i > 0) {
        filename = filename.substring(0, i);
    }
    return filename;
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

        // since filename often includes an extension describing how the data is encoded, drop it because it
        // is no longer relevant once that data is in Taiga.
        this.fileName = dropExtension(this.file.name);
        this.fileType = getInitialFileTypeFromMimeType(this.file.type);
        this.fileSize = this.file.size;

        this.progress = 0;
        this.conversionProgress = "";

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

// Bootstrap Table object
// Class to manage the items in the bootstrap table of FolderView
export class BootstrapTableFolderEntry {
    id: string;
    name: string;
    url: string;
    creation_date: Date;
    creator_name: string;

    type: FolderEntriesTypeEnum;

    processFolderEntryUrl(entry: FolderEntries, latestDatasetVersion?: DatasetVersion,
                          full_datasetVersion?: DatasetVersion) {
        let processedUrl = null;
        if (entry.type === FolderEntriesTypeEnum.Folder) {
            processedUrl = relativePath("folder/" + entry.id);
        }
        else if (entry.type === FolderEntriesTypeEnum.DatasetVersion) {
            processedUrl = relativePath("dataset/" + full_datasetVersion.id + "/" + entry.id);
        }
        else if (entry.type === FolderEntriesTypeEnum.Dataset) {
            processedUrl = relativePath("dataset/" + entry.id + "/" + latestDatasetVersion.id);
        }

        return processedUrl;
    }

    processCreationDate(entry: FolderEntries, latestDatasetVersion?: DatasetVersion) {
        let processedCreationDate: Date = new Date();

        if (entry.type === FolderEntriesTypeEnum.Dataset) {

            processedCreationDate.setTime(Date.parse(latestDatasetVersion.creation_date));
            // processedCreationDate = toLocalDateString(latestDatasetVersion.creation_date);
        }
        else {
            processedCreationDate.setTime(Date.parse(entry.creation_date));
            // processedCreationDate = toLocalDateString(entry.creation_date);
        }

        return processedCreationDate;
    }

    constructor(entry: FolderEntries, latestDatasetVersion?: DatasetVersion, fullDatasetVersion?: DatasetVersion) {
        this.id = entry.id;
        this.name = entry.name;

        this.url = this.processFolderEntryUrl(entry, latestDatasetVersion, fullDatasetVersion);

        this.creation_date = this.processCreationDate(entry, latestDatasetVersion);

        // TODO: Think about what to do with an entry without a user
        if (entry.creator && entry.creator.name) {
            this.creator_name = entry.creator.name;
        }
        else {
            this.creator_name = undefined;
        }

        this.type = entry.type;
    }
}

export class BootstrapTableSearchEntry {
    id: string;
    name: string;
    url: string;
    creation_date: Date;
    creator_name: string;

    type: FolderEntriesTypeEnum;

    processBreadCrumbName(searchEntry: SearchEntry) {
        let breadcrumbedName = "";

        // Fetch per order the names while current_order != length of the breadcrumb list
        let current_order = 0;
        while (current_order !== searchEntry.breadcrumbs.length) {
            breadcrumbedName += searchEntry.breadcrumbs.find((breadcrumb: OrderedNamedId) => {
                return breadcrumb.order === current_order + 1;
            }).folder.name + " > ";
            current_order += 1;
        }

        // Now we add the name of the entry
        breadcrumbedName += searchEntry.entry.name;

        return breadcrumbedName;
    }

    processFolderEntryUrl(searchEntry: SearchEntry) {
        let processedUrl = null;
        if (searchEntry.entry.type === FolderEntriesTypeEnum.Folder) {
            processedUrl = relativePath("folder/" + searchEntry.entry.id);
        }
        else if (searchEntry.entry.type === FolderEntriesTypeEnum.Dataset) {
            processedUrl = relativePath("dataset/" + searchEntry.entry.id);
        }

        return processedUrl;
    }

    processCreationDate(searchEntry: SearchEntry) {
        let processedCreationDate: Date = new Date();

        processedCreationDate.setTime(Date.parse(searchEntry.entry.creation_date));
        // processedCreationDate = toLocalDateString(entry.creation_date);

        return processedCreationDate;
    }

    constructor(searchEntry: SearchEntry) {
        this.id = searchEntry.entry.id;
        this.name = this.processBreadCrumbName(searchEntry);

        this.url = this.processFolderEntryUrl(searchEntry);

        this.creation_date = this.processCreationDate(searchEntry);

        // TODO: Think about what to do with an entry without a user
        if (searchEntry.entry.creator && searchEntry.entry.creator.name) {
            this.creator_name = searchEntry.entry.creator.name;
        }
        else {
            this.creator_name = undefined;
        }

        this.type = searchEntry.entry.type;
    }
}

// IMPORTANT: Need to sync with backend for each changes
export enum InitialFileType {
    NumericMatrixCSV = <any> "NumericMatrixCSV",
    NumericMatrixTSV = <any> "NumericMatrixTSV",
    TableCSV = <any> "TableCSV",
    TableTSV = <any> "TableTSV",
    GCT = <any> "GCT",
    Raw = <any> "Raw"
}

export enum DataFileType {
    Raw = <any> "Raw",
    HDF5 = <any> "HDF5",
    Columnar = <any> "Columnar"
}

export interface DatafileUrl {
    dataset_name: string;
    dataset_version: string;
    dataset_id: string;
    dataset_version_id: string;
    datafile_name: string;
    status: string;
    urls: Array<string>;
}

export enum ConversionStatusEnum {
    Pending = <any> "Conversion pending",
    Downloading = <any> "Downloading from S3",
    Running = <any> "Running conversion",
    Uploading = <any> "Uploading converted file to S3",
    Completed = <any> "Completed successfully"
}

export class AccessLog {
    user_id: string;
    user_name: string;

    // Used for presentation BootstrapTable
    entry_id: string;
    entry_name: string;
    type: FolderEntriesTypeEnum;

    url: string;

    last_access: string;

    processAccessLogEntryUrl(serverAccessLog: any) {
        let processedUrl = null;
        // TODO: Fix this toLowerCase workaround to compare types
        if (serverAccessLog.entry.type.toLowerCase() === FolderEntriesTypeEnum.Folder) {
            processedUrl = relativePath("folder/" + serverAccessLog.entry.id);
        }
        else {
            processedUrl = relativePath("dataset/" + serverAccessLog.entry.id);
        }

        return processedUrl;
    }

    constructor(obj: any) {
        this.user_id = obj.user_id;
        this.user_name = obj.user_name;
        this.entry_id = obj.entry.id;
        this.entry_name = obj.entry.name;
        this.type = obj.type;
        this.url = this.processAccessLogEntryUrl(obj);
        this.last_access = obj.last_access;
    }
}

// Search
export class SearchResult {
    current_folder: NamedId; // Id and name of the folder where search was originated from
    name: string; // Name of the search
    entries: Array<SearchEntry>;
}

export class SearchEntry {
    entry: Entry;
    breadcrumbs: Array<OrderedNamedId>; // Array of folders
}

export class OrderedNamedId {
    folder: NamedId;
    order: Number; // Order in which the breadcrumb should appear
}

