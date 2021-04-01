import { isUndefined, isNullOrUndefined } from "util";

import HTMLResponseError from "src/common/models/HTMLReponseError";
import {
  User,
  Folder,
  Dataset,
  DatasetVersion,
  S3Credentials,
  TaskStatus,
  DatasetAndDatasetVersion,
  UploadedFileMetadata,
  NamedId,
  DatasetFullDatasetVersions,
  AccessLog,
  DatafileUrl,
  SearchResult,
  ActivityLogEntry,
  Group,
} from "./models";
import {
  ArticleInfo as FigshareArticleInfo,
  FileToUpdate as FigshareFileToUpdate,
  UpdateArticleResponse as FigshareUpdateArticleResponse,
} from "./figshare";

// import { getUserToken } from '../utilities/route';
// import { Token } from "../components/Token";

const checkResponse = (response: Response): Promise<Response> => {
  if (response.status >= 200 && response.status < 300) {
    return Promise.resolve(response);
  }

  if (response.status === 400) {
    return response.json().then((errorDetail) => {
      return Promise.reject<Response>(new Error(errorDetail.detail));
    });
  }
  return Promise.reject<Response>(new HTMLResponseError(response));
};

export default class TaigaApi {
  baseUrl: string;

  authHeaders: any;

  loading: boolean;

  userToken: string;

  constructor(baseUrl: string, userToken: string) {
    this.baseUrl = baseUrl;
    this.userToken = userToken;

    this.authHeaders = {
      auth: `Bearer ${this.userToken}`,
    };
    this.loading = false;
  }

  _fetch<T>(url: string): Promise<T> {
    return fetch(this.baseUrl + url, {
      headers: {
        Authorization: this.authHeaders.auth,
      },
    })
      .then((response: Response) => checkResponse(response))
      .then<T>((response: Response) => {
        return response.json();
      });
  }

  _post<T>(url: string, args: any): Promise<T> {
    return fetch(this.baseUrl + url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        Authorization: this.authHeaders.auth,
      },
      body: JSON.stringify(args),
    })
      .then((response: Response) => checkResponse(response))
      .then<T>((response: Response) => {
        return response.json();
      });
  }

  _put<T>(url: string, args: any): Promise<T> {
    return fetch(this.baseUrl + url, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        Authorization: this.authHeaders.auth,
      },
      body: JSON.stringify(args),
    })
      .then((response: Response) => checkResponse(response))
      .then<T>((response: Response) => {
        return response.json();
      });
  }

  _delete<T>(url: string): Promise<T> {
    return fetch(this.baseUrl + url, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        Authorization: this.authHeaders.auth,
      },
    })
      .then((response: Response) => checkResponse(response))
      .then<T>((response: Response) => {
        return response.json();
      });
  }

  get_user(): Promise<User> {
    return this._fetch<User>("/user");
  }

  get_all_users(): Promise<Array<User>> {
    return this._fetch<Array<User>>("/user/all");
  }

  // TODO: Replace with FolderFullDatasetVersions
  get_folder(folderId: string): Promise<Folder> {
    return this._fetch<Folder>(`/folder/${folderId}`);
  }

  get_dataset(dataset_id: string): Promise<Dataset> {
    return this._fetch<Dataset>(`/dataset/${dataset_id}`);
  }

  get_user_entry_access_log(): Promise<Array<AccessLog>> {
    // TODO: Change this api to get a better meaning. We want all the entries for a specific user
    return this._fetch<Array<AccessLog>>("/entry/logAccess");
  }

  get_entry_access_log(entry_id: string): Promise<Array<AccessLog>> {
    // We fetch all the AccessLog for a specific entry
    return this._fetch<Array<AccessLog>>(`/entry/${entry_id}/logAccess`);
  }

  remove_entry_access_log(accessLogsToRemove: Array<AccessLog>) {
    return this._post<void>("/entry/logAccess/remove/all", accessLogsToRemove);
  }

  get_datasets(
    datasetIds: Array<string>
  ): Promise<Array<DatasetFullDatasetVersions>> {
    // TODO: We should not use a post method for a get
    return this._post<Array<DatasetFullDatasetVersions>>("/datasets", {
      datasetIds,
    });
  }

  get_dataset_version(dataset_version_id: string): Promise<DatasetVersion> {
    return this._fetch<DatasetVersion>(`/datasetVersion/${dataset_version_id}`);
  }

  get_datasetVersions(
    datasetVersionIds: Array<string>
  ): Promise<Array<DatasetVersion>> {
    return this._post<Array<DatasetVersion>>("/datasetVersions", {
      datasetVersionIds,
    });
  }

  get_dataset_version_with_dataset(
    datasetId: string,
    datasetVersionId?: string
  ) {
    // If not datasetVersion is passed, return the first datasetVersion
    let dsAndDv: Promise<DatasetAndDatasetVersion>;
    if (isUndefined(datasetVersionId)) {
      // TODO: This should not call the /dataset/{datasetId} api but a specific one to get the dataset and the last datasetVersion
      dsAndDv = this._fetch<DatasetAndDatasetVersion>(`/dataset/${datasetId}`);
    } else {
      dsAndDv = this._fetch<DatasetAndDatasetVersion>(
        `/dataset/${datasetId}/${datasetVersionId}`
      );
    }

    return dsAndDv;
  }

  get_dataset_version_last(dataset_id: string): Promise<DatasetVersion> {
    return this._fetch<DatasetVersion>(`/dataset/${dataset_id}/last`);
  }

  get_s3_credentials(): Promise<S3Credentials> {
    return this._fetch<S3Credentials>("/credentials_s3");
  }

  get_upload_session(): Promise<string> {
    return this._fetch<string>("/upload_session");
  }

  update_dataset_name(dataset_id: string, name: string) {
    return this._post<void>(`/dataset/${dataset_id}/name`, { name });
  }

  update_dataset_version_description(
    dataset_version_id: string,
    description: string
  ) {
    return this._post<void>(
      `/datasetVersion/${dataset_version_id}/description`,
      { description }
    );
  }

  update_dataset_version_changes_description(
    dataset_version_id: string,
    changes_description: string
  ) {
    return this._post<void>(
      `/datasetVersion/${dataset_version_id}/changes_description`,
      { changes_description }
    );
  }

  create_folder(
    current_folder_id: string,
    current_user_id: string,
    name: string,
    description: string
  ) {
    return this._post<NamedId>("/folder/create", {
      creatorId: current_user_id,
      parentId: current_folder_id,
      name,
      description,
    });
  }

  update_folder_name(folder_id: string, name: string) {
    return this._post<void>(`/folder/${folder_id}/name`, { name });
  }

  update_folder_description(folder_id: string, description: string) {
    return this._post<void>(`/folder/${folder_id}/description`, {
      description,
    });
  }

  create_datafile(sid: string, S3UploadedFileMetadata: UploadedFileMetadata) {
    return this._post<string>(`/datafile/${sid}`, S3UploadedFileMetadata);
  }

  get_datafile(
    datasetPermaname: string,
    datasetVersion: string,
    datasetVersionId: string,
    datafileName: string,
    format: string,
    force: string
  ): Promise<DatafileUrl> {
    // Returns the url to launch/get status/retrieve the datafile
    // (datasetPermaname with datasetVersion OR datasetVersionId) and datafileName + format [+ force]
    // TODO: Support Permaname+Version. Currently only datasetVersionId
    const url =
      `${"/datafile?" + "dataset_version_id="}${datasetVersionId}&` +
      `datafile_name=${encodeURIComponent(datafileName)}&` +
      `format=${format}&` +
      `force=${force}`;

    return this._fetch<DatafileUrl>(url);
  }

  get_task_status(taskStatusId: string) {
    return this._fetch<TaskStatus>(`/task_status/${taskStatusId}`);
  }

  create_dataset(
    sid: string,
    datasetName: string,
    datasetDescription: string,
    currentFolderId: string
  ) {
    return this._post<string>("/dataset", {
      sessionId: sid,
      datasetName,
      datasetDescription,
      currentFolderId,
    });
  }

  move_to_folder(
    entryIds: Array<string>,
    currentFolderId: string,
    targetFolderId: string
  ) {
    if (isNullOrUndefined(targetFolderId)) {
      targetFolderId = "";
    }

    return this._post<void>("/move", {
      entryIds,
      currentFolderId,
      targetFolderId,
    });
  }

  copy_to_folder(entryIds: Array<string>, folderId: string) {
    return this._post<void>("/copy", {
      entryIds,
      folderId,
    });
  }

  create_new_dataset_version(
    sid: string,
    dataset_id: string,
    new_description: string,
    changes_description: string
  ) {
    return this._post<string>("/datasetVersion", {
      sessionId: sid,
      datasetId: dataset_id,
      newDescription: new_description,
      changesDescription: changes_description,
    });
  }

  create_or_update_entry_access_log(entry_id: string): Promise<void> {
    return this._post<void>(`/entry/${entry_id}/logAccess`, {});
  }

  // Search
  get_folder_search(
    current_folder_id: string,
    search_query: string
  ): Promise<SearchResult> {
    return this._fetch<SearchResult>(
      `/search/${current_folder_id}/${search_query}`
    );
  }

  // Deprecation
  // TODO: Promise should return an ack or a failure
  deprecate_dataset_version(
    dataset_version_id: string,
    reason: string
  ): Promise<void> {
    return this._post<void>(`/datasetVersion/${dataset_version_id}/deprecate`, {
      deprecationReason: reason,
    });
  }

  de_deprecate_dataset_version(dataset_version_id: string): Promise<void> {
    return this._post<void>(
      `/datasetVersion/${dataset_version_id}/de-deprecate`,
      {}
    );
  }

  delete_dataset_version(dataset_version_id: string): Promise<void> {
    return this._post<void>(`/datasetVersion/${dataset_version_id}/delete`, {});
  }

  get_dataset_version_id(any_entry_identifier: string): Promise<string> {
    return this._fetch(
      `/datasetVersion/id/find?entry_submitted_by_user=${any_entry_identifier}`
    );
  }

  get_activity_log_for_dataset_id(
    dataset_id: string
  ): Promise<Array<ActivityLogEntry>> {
    return this._fetch(`/dataset/${dataset_id}/activityLog`);
  }

  get_all_groups_for_current_user(): Promise<
    Array<Pick<Group, Exclude<keyof Group, "users">>>
  > {
    return this._fetch("/group/allJoined");
  }

  get_group(groupId: string): Promise<Group> {
    return this._fetch(`/group/${groupId}`);
  }

  add_group_user_associations(
    groupId: string,
    userIds: Array<string>
  ): Promise<Group> {
    return this._post<Group>(`/group/${groupId}/add`, {
      userIds,
    });
  }

  remove_group_user_associations(
    groupId: string,
    userIds: Array<string>
  ): Promise<Group> {
    return this._post<Group>(`/group/${groupId}/remove`, { userIds });
  }

  authorize_figshare(token: string): Promise<{}> {
    return this._put("/figshare/token", token);
  }

  get_figshare_article(article_id: number): Promise<FigshareArticleInfo> {
    return this._fetch(`/figshare/article_for_user/${article_id}`);
  }

  get_figshare_article_creation_parameters(): Promise<{
    categories: Array<{
      parent_id: number;
      id: number;
      title: string;
    }>;
    licenses: Array<{
      value: number;
      name: string;
      url: string;
    }>;
  }> {
    return this._fetch("/figshare/article_creation_parameters");
  }

  upload_dataset_version_to_figshare(
    dataset_version_id: string,
    article_name: string,
    article_description: string,
    files_to_upload: Array<{ datafile_id: string; file_name: string }>,
    license: number,
    categories: Array<number>,
    keywords: Array<string>,
    references: Array<string>
  ): Promise<{
    article_id: number;
    files: Array<{
      datafile_id: string;
      file_name: string;
      failure_reason?: string;
      task_id?: string;
    }>;
  }> {
    return this._post("/figshare/link", {
      dataset_version_id,
      article_name,
      article_description,
      files_to_upload,
      license,
      categories,
      keywords,
      references,
    });
  }

  update_figshare_article(
    article_id: number,
    description: string,
    current_article_version: number,
    dataset_version_id: string,
    files_to_update: Array<FigshareFileToUpdate>
  ): Promise<FigshareUpdateArticleResponse> {
    return this._post("/figshare/update_article", {
      article_id,
      description,
      current_article_version,
      dataset_version_id,
      files_to_update,
    });
  }

  add_subscription(dataset_id: string): Promise<string> {
    return this._put(`/subscription`, dataset_id);
  }

  delete_subscription(subscriptionId: string): Promise<boolean> {
    return this._delete(`/subscription/${subscriptionId}`);
  }
}
