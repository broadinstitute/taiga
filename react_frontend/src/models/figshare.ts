import { TaskStatus } from "./models";

interface Author {
  full_name: string;
  id: number;
  is_active: boolean;
}

export interface File {
  computed_md5: string;
  download_url: string;
  id: number;
  is_link_only: boolean;
  name: string;
  size: number;
  supplied_md5: string;
}

export interface ArticleInfo {
  id: number;
  version: number;
  authors: Array<Author>;
  description: string;
  files: Array<File>;
}

export interface FileToUpdate {
  figshare_file_id: number;
  action: "Add" | "Delete";
  datafile_id: string;
  file_name: string;
}

export interface UploadFileStatus {
  datafile_id: string;
  file_name: string;
  failure_reason?: string;
  task_id?: string;
  taskStatus?: TaskStatus;
}

export interface UpdateArticleResponse {
  article_id: number;
  files: Array<UploadFileStatus>;
}

export interface UpdateArticleRemovedFigshareFile {
  figshareFileId: number;
  name: string;
  removeFile: boolean;
}

export interface UpdateArticleAdditionalTaigaDatafile {
  datafileId: string;
  name: string;
  addFile: boolean;
  datafileName: string;
}

export interface UpdateArticleUnchangedFile {
  figshareFileId: number;
  name: string;
  datafileId: string;
  datafileName: string;
}
