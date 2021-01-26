import {
  getInitialFileTypeFromMimeType,
  toLocalDateString,
} from "../utilities/formats";
import { relativePath } from "../utilities/route";

export enum EntryTypeEnum {
  Folder = "folder",
  Dataset = "dataset",
  DatasetVersion = "dataset_version",
}
export interface Entry {
  type: EntryTypeEnum;
  id: string;
  name: string;
  creation_date: string;
  creator: NamedId;
}

export enum FolderTypeEnum {
  Folder = "folder",
  Trash = "trash",
  Home = "home",
}
export interface Folder extends Entry {
  type: EntryTypeEnum.Folder;
  folder_type: FolderTypeEnum;
  parents: Array<NamedId>;
  entries: Array<Entry>;
  description: string;
  acl: Acl;
  can_view: boolean;
  can_edit: boolean;
}

export class NamedId {
  name: string;
  id: string;
}

export interface User {
  id: string;
  name: string;
  home_folder_id: string;
  trash_folder_id: string;
  token: string;
  figshare_account_linked: boolean;
}

export interface UserNamedId {
  id: string;
  name: string;
}

export enum StatusEnum {
  Deleted = "deleted",
  Approved = "approved",
  Deprecated = "deprecated",
}

export interface DatasetVersion extends Entry {
  dataset_id: string;
  state: StatusEnum;
  reason_state: string;
  version: string;
  description?: string;
  changes_description?: string;
  datafiles: Array<DatasetVersionDatafiles>;
  folders: Array<NamedId>;
  can_edit: boolean;
  can_view: boolean;
  figshare: {
    is_public: boolean;
    description?: string;
    files?: Array<{
      computed_md5: string;
      download_url: string;
      id: number;
      is_link_only: boolean;
      name: string;
      size: number;
      supplied_md5: string;
      taiga_datafile_id?: string;
      taiga_datafile_readable_id: string;
      underlying_file_id?: string;
    }>;
    id?: number;
    status?: string;
    title?: string;
    url?: string;
    url_private_html?: string;
    url_public_html?: string;
    version?: number;
  };
}

export interface DatasetAndDatasetVersion {
  dataset: Dataset;
  datasetVersion: DatasetVersion;
}

export interface DatasetVersionDatafiles {
  id: string;
  name: string;
  underlying_file_id: string;
  url: string;
  type: DataFileType;
  allowed_conversion_type: Array<string>;
  short_summary: string;
  gcs_path: string;
  original_file_md5?: string;
  original_file_sha256?: string;
}

export interface DatasetVersionSummary {
  name: string;
  id: string;
  status: StatusEnum;
}

export interface Dataset {
  can_edit: boolean;
  can_view: boolean;
  description: string;
  folders: Array<NamedId>;
  id: string;
  name: string;
  permanames: Array<string>;
  subscription_id: string;
  versions: Array<DatasetVersionSummary>;
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

export interface S3UploadedLocation {
  format: string;
  bucket: string;
  key: string;
  encoding: string;
}

export interface UploadedFileMetadata {
  filename: string;
  filetype: string;
  s3Upload?: S3UploadedLocation;
  existingTaigaId?: string;
}

export function dropExtension(filename: string): string {
  var i = filename.lastIndexOf(".");
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
  current: number;
  total: number;
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

  type: EntryTypeEnum;

  processFolderEntryUrl(
    entry: Entry,
    latestDatasetVersion?: DatasetVersion,
    full_datasetVersion?: DatasetVersion
  ) {
    let processedUrl = null;
    if (entry.type === EntryTypeEnum.Folder) {
      processedUrl = relativePath("folder/" + entry.id);
    } else if (entry.type === EntryTypeEnum.DatasetVersion) {
      processedUrl = relativePath(
        "dataset/" + full_datasetVersion.id + "/" + entry.id
      );
    } else if (entry.type === EntryTypeEnum.Dataset) {
      processedUrl = relativePath(
        "dataset/" + entry.id + "/" + latestDatasetVersion.id
      );
    }

    return processedUrl;
  }

  processCreationDate(entry: Entry, latestDatasetVersion?: DatasetVersion) {
    let processedCreationDate: Date = new Date();

    if (entry.type === EntryTypeEnum.Dataset) {
      processedCreationDate.setTime(
        Date.parse(latestDatasetVersion.creation_date)
      );
      // processedCreationDate = toLocalDateString(latestDatasetVersion.creation_date);
    } else {
      processedCreationDate.setTime(Date.parse(entry.creation_date));
      // processedCreationDate = toLocalDateString(entry.creation_date);
    }

    return processedCreationDate;
  }

  constructor(
    entry: Entry,
    latestDatasetVersion?: DatasetVersion,
    fullDatasetVersion?: DatasetVersion
  ) {
    this.id = entry.id;
    this.name = entry.name;

    this.url = this.processFolderEntryUrl(
      entry,
      latestDatasetVersion,
      fullDatasetVersion
    );

    this.creation_date = this.processCreationDate(entry, latestDatasetVersion);

    // TODO: Think about what to do with an entry without a user
    if (entry.creator && entry.creator.name) {
      this.creator_name = entry.creator.name;
    } else {
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

  type: EntryTypeEnum;

  processBreadCrumbName(searchEntry: SearchEntry) {
    let breadcrumbedName = "";

    // Fetch per order the names while current_order != length of the breadcrumb list
    let current_order = 0;
    while (current_order !== searchEntry.breadcrumbs.length) {
      breadcrumbedName +=
        searchEntry.breadcrumbs.find((breadcrumb: OrderedNamedId) => {
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
    if (searchEntry.entry.type === EntryTypeEnum.Folder) {
      processedUrl = relativePath("folder/" + searchEntry.entry.id);
    } else if (searchEntry.entry.type === EntryTypeEnum.Dataset) {
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
    } else {
      this.creator_name = undefined;
    }

    this.type = searchEntry.entry.type;
  }
}

// IMPORTANT: Need to sync with backend for each changes
export enum InitialFileType {
  NumericMatrixCSV = "NumericMatrixCSV",
  TableCSV = "TableCSV",
  GCT = "GCT",
  Raw = "Raw",
}

export enum DataFileType {
  Raw = "Raw",
  HDF5 = "HDF5",
  Columnar = "Columnar",
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
  Pending = <any>"Conversion pending",
  Downloading = <any>"Downloading from S3",
  Running = <any>"Running conversion",
  Uploading = <any>"Uploading converted file to S3",
  Completed = <any>"Completed successfully",
}

export class AccessLog {
  user_id: string;
  user_name: string;

  // Used for presentation BootstrapTable
  entry_id: string;
  entry_name: string;
  type: EntryTypeEnum;

  url: string;

  last_access: string;

  processAccessLogEntryUrl(serverAccessLog: any) {
    let processedUrl = null;
    // TODO: Fix this toLowerCase workaround to compare types
    if (serverAccessLog.entry.type.toLowerCase() === EntryTypeEnum.Folder) {
      processedUrl = relativePath("folder/" + serverAccessLog.entry.id);
    } else {
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

export enum ActivityTypeEnum {
  created = "created",
  changed_name = "changed_name",
  changed_description = "changed_description",
  added_version = "added_version",
  started_log = "started_log",
}

export class ActivityLogEntry {
  id: string;
  user_name: string;
  timestamp: string;
  type: ActivityTypeEnum;
  comments: string | null;
}

export interface CreationActivityLogEntry extends ActivityLogEntry {
  type: ActivityTypeEnum.created;
  dataset_name: string;
  dataset_description: string | null;
}

export interface NameUpdateActivity extends ActivityLogEntry {
  type: ActivityTypeEnum.changed_name;
  dataset_name: string;
}

export interface DescriptionUpdateActivity extends ActivityLogEntry {
  type: ActivityTypeEnum.changed_description;
  dataset_description: string;
  dataset_version: number;
}

export interface VersionAdditionActivity extends ActivityLogEntry {
  type: ActivityTypeEnum.added_version;
  dataset_description: string | null;
  dataset_version: number;
}

export interface LogStartActivity extends ActivityLogEntry {
  type: ActivityTypeEnum.started_log;
  dataset_name: string;
  dataset_description: string | null;
  dataset_version: number;
}

export interface Group {
  id: number;
  name: string;
  users: Array<UserNamedId>;
  num_users: number;
}
