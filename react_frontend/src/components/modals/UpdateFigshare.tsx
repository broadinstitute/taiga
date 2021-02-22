import * as React from "react";

import { Modal } from "react-bootstrap";
import ArticleIdStep from "./UpdateFigshareArticleIdStep";
import UpdateArticleStep from "./UpdateFigshareUpdateArticleStep";
import PollResultsStep from "./UpdateFigsharePollResultsStep";

import { DatasetVersion } from "../../models/models";
import TaigaApi from "../../models/api";
import {
  ArticleInfo,
  UpdateArticleResponse,
  UploadFileStatus,
} from "../../models/figshare";

import "../../styles/modals/uploadtofigshare.css";

type Props = {
  tapi: TaigaApi;
  handleClose: (uploadComplete: boolean, figsharePrivateUrl: string) => void;
  show: boolean;
  datasetVersion: DatasetVersion;
};

interface State {
  figshareArticleInfo: ArticleInfo;
  uploadResults: ReadonlyArray<UploadFileStatus>;
  uploadComplete: boolean;
}
export default class UpdateFigshare extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);

    this.state = {
      figshareArticleInfo: null,
      uploadResults: null,
      uploadComplete: false,
    };
  }

  componentDidUpdate(prevProps: Props) {
    if (
      prevProps.show != this.props.show ||
      prevProps.datasetVersion != this.props.datasetVersion
    ) {
      this.setState({
        figshareArticleInfo: null,
        uploadResults: null,
        uploadComplete: false,
      });
    }
  }

  handleFetchFigshareArticleSuccess = (figshareArticleInfo: ArticleInfo) => {
    this.setState({ figshareArticleInfo });
  };

  handleUpdateArticleResponse = (
    updateArticleResponse: UpdateArticleResponse
  ) => {
    this.setState({
      uploadResults: updateArticleResponse.files.map((r) => {
        if (!r.task_id && !r.failure_reason) {
          return {
            ...r,
            taskStatus: {
              id: null,
              state: "SUCCESS",
              message: null,
              current: 1,
              total: 1,
              s3Key: null,
            },
          };
        }
        return r;
      }),
    });
  };

  handleClose = () => {
    const { uploadComplete } = this.state;
    const figsharePrivateUrl = uploadComplete
      ? `https://figshare.com/account/articles/${this.state.figshareArticleInfo.id}`
      : null;

    this.setState(
      {
        figshareArticleInfo: null,
        uploadResults: null,
        uploadComplete: false,
      },
      () => this.props.handleClose(uploadComplete, figsharePrivateUrl)
    );
  };

  render() {
    const { figshareArticleInfo, uploadResults, uploadComplete } = this.state;
    const figsharePrivateUrl = uploadComplete
      ? `https://figshare.com/account/articles/${figshareArticleInfo.id}`
      : null;

    return (
      <Modal
        show={this.props.show}
        onHide={this.handleClose}
        dialogClassName="upload-to-figshare-modal"
      >
        <Modal.Header closeButton>
          <Modal.Title>Update Figshare Article</Modal.Title>
        </Modal.Header>
        {!figshareArticleInfo ? (
          <ArticleIdStep
            tapi={this.props.tapi}
            handleFetchFigshareArticleSuccess={
              this.handleFetchFigshareArticleSuccess
            }
          />
        ) : !uploadResults ? (
          <UpdateArticleStep
            tapi={this.props.tapi}
            datasetVersion={this.props.datasetVersion}
            figshareArticleInfo={figshareArticleInfo}
            onUpdateArticle={this.handleUpdateArticleResponse}
          />
        ) : !uploadComplete ? (
          <PollResultsStep
            tapi={this.props.tapi}
            initialUploadResults={uploadResults}
            datafiles={this.props.datasetVersion.datafiles}
            onUploadComplete={() => this.setState({ uploadComplete: true })}
          />
        ) : (
          <Modal.Body>
            <p>
              Files have finished uploading. Your Figshare article version is
              not yet published. Go to the Figshare website to publish it.
            </p>
          </Modal.Body>
        )}
      </Modal>
    );
  }
}
