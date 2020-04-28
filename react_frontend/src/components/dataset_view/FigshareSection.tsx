import * as React from "react";
import { Button } from "react-bootstrap";
import { Link } from "react-router-dom";

import { DatasetVersion } from "../../models/models";
import { relativePath } from "../../utilities/route";
import { TaigaApi } from "../../models/api";
import UpdateFigshare from "../modals/UpdateFigshare";
import UploadToFigshare from "../modals/UploadToFigshare";

type Props = {
  tapi: TaigaApi;
  datasetVersion: DatasetVersion;
  handleFigshareUploadComplete: () => Promise<any>;
  userFigshareAccountId: number;
};

type State = {
  figshareUrl: string;
  figshareUrlPublic: boolean;
  showUploadToFigshare: boolean;
  showUpdateFigshare: boolean;
};

export default class FigshareSection extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);

    this.state = {
      figshareUrl: null,
      figshareUrlPublic: false,
      showUploadToFigshare: false,
      showUpdateFigshare: false,
    };

    this.showUploadToFigshare = this.showUploadToFigshare.bind(this);
    this.handleCloseUploadToFigshare = this.handleCloseUploadToFigshare.bind(
      this
    );
    this.showUpdateFigshare = this.showUpdateFigshare.bind(this);
    this.handleCloseUpdateFigshare = this.handleCloseUpdateFigshare.bind(this);
  }

  componentDidMount() {
    if (this.props.datasetVersion.figshare_linked) {
      this.getFigshareUrl();
    } else {
      this.setState({ figshareUrl: null });
    }
  }

  componentDidUpdate(prevProps: Props) {
    if (prevProps.datasetVersion.id != this.props.datasetVersion.id) {
      if (this.props.datasetVersion.figshare_linked) {
        this.getFigshareUrl();
      } else {
        this.setState({ figshareUrl: null });
      }
    }
  }

  getFigshareUrl() {
    this.props.tapi
      .get_figshare_article_url(this.props.datasetVersion.id)
      .then((v) =>
        this.setState({
          figshareUrl: v.figshare_url,
          figshareUrlPublic: v.public,
        })
      );
  }

  showUploadToFigshare() {
    this.setState({ showUploadToFigshare: true });
  }

  showUpdateFigshare() {
    this.setState({ showUpdateFigshare: true });
  }

  handleCloseUploadToFigshare(
    uploadComplete: boolean,
    figsharePrivateUrl: string
  ) {
    if (uploadComplete) {
      this.props.handleFigshareUploadComplete().then(() => {
        this.setState({
          showUploadToFigshare: false,
          figshareUrl: figsharePrivateUrl,
          figshareUrlPublic: false,
        });
      });
    } else {
      this.setState({
        showUploadToFigshare: false,
        figshareUrl: figsharePrivateUrl,
      });
    }
  }

  handleCloseUpdateFigshare(
    uploadComplete: boolean,
    figsharePrivateUrl: string
  ) {
    if (uploadComplete) {
      this.props.handleFigshareUploadComplete().then(() => {
        this.setState({
          showUpdateFigshare: false,
          figshareUrl: figsharePrivateUrl,
          figshareUrlPublic: false,
        });
      });
    } else {
      this.setState({
        showUpdateFigshare: false,
        figshareUrl: figsharePrivateUrl,
      });
    }
  }

  renderFigshareLinkedContent() {
    if (!this.state.figshareUrl && !this.state.figshareUrlPublic) {
      return (
        <p>This dataset version is linked to a private article on Figshare.</p>
      );
    }

    const articleLink = (
      <p>
        This dataset version is linked to a{" "}
        <a href={this.state.figshareUrl} target="_blank" rel="noopener">
          {this.state.figshareUrlPublic ? "public" : "private"} Figshare article
        </a>
        .
      </p>
    );
    return (
      <React.Fragment>
        {articleLink}
        <span>
          <a
            href={`${this.props.tapi.baseUrl}/figshare/download_mapping/${this.props.datasetVersion.id}`}
          >
            Download Figshare link mapping for taigapy{" "}
            <i className="fa fa-download" aria-hidden="true"></i>
          </a>
        </span>
      </React.Fragment>
    );
  }

  renderFigshareNotLinkedContent() {
    const { userFigshareAccountId } = this.props;
    return (
      <React.Fragment>
        <p>This dataset version is not linked with any Figshare article.</p>
        {userFigshareAccountId === null && (
          <p>
            Link your Figshare account to upload this dataset version to
            Figshare through the sidebar of the{" "}
            <Link to={relativePath("token")}>My Token</Link> page.
          </p>
        )}
        <Button
          onClick={this.showUploadToFigshare}
          disabled={userFigshareAccountId === null}
        >
          Upload to Figshare as new article
        </Button>
        <Button
          onClick={this.showUpdateFigshare}
          disabled={userFigshareAccountId === null}
        >
          Upload to Figshare as a new version of an existing article
        </Button>
      </React.Fragment>
    );
  }

  render() {
    return (
      <section>
        <h2>Link with Figshare</h2>
        {this.props.datasetVersion && (
          <React.Fragment>
            {this.props.datasetVersion.figshare_linked
              ? this.renderFigshareLinkedContent()
              : this.renderFigshareNotLinkedContent()}
            <UploadToFigshare
              tapi={this.props.tapi}
              handleClose={this.handleCloseUploadToFigshare}
              show={this.state.showUploadToFigshare}
              userFigshareLinked={this.props.userFigshareAccountId !== null}
              datasetVersion={this.props.datasetVersion}
            />
            <UpdateFigshare
              tapi={this.props.tapi}
              handleClose={this.handleCloseUpdateFigshare}
              show={this.state.showUpdateFigshare}
              userFigshareAccountId={this.props.userFigshareAccountId}
              datasetVersion={this.props.datasetVersion}
            />
          </React.Fragment>
        )}
      </section>
    );
  }
}
