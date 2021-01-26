import * as React from "react";
import { Row, Col, Button } from "react-bootstrap";
import { Link } from "react-router-dom";
import { saveAs } from "file-saver";

import { FigshareLinkedFiles } from "src/dataset/models/models";
import { DatasetVersion } from "../../models/models";
import { relativePath } from "../../utilities/route";
import { TaigaApi } from "../../models/api";
import UpdateFigshare from "../../components/modals/UpdateFigshare";
import UploadToFigshare from "../../components/modals/UploadToFigshare";

type Props = {
  tapi: TaigaApi;
  datasetName: string;
  datasetVersion: DatasetVersion;
  handleFigshareUploadComplete: () => Promise<any>;
  userFigshareAccountLinked: boolean;
  figshareLinkedFiles: FigshareLinkedFiles;
};

type State = {
  showUploadToFigshare: boolean;
  showUpdateFigshare: boolean;
};

export default class FigshareSection extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);

    this.state = {
      showUploadToFigshare: false,
      showUpdateFigshare: false,
    };
  }

  showUploadToFigshare = () => {
    this.setState({ showUploadToFigshare: true });
  };

  showUpdateFigshare = () => {
    this.setState({ showUpdateFigshare: true });
  };

  handleCloseUploadToFigshare = (uploadComplete: boolean) => {
    if (uploadComplete) {
      this.props.handleFigshareUploadComplete().then(() => {
        this.setState({
          showUploadToFigshare: false,
        });
      });
    } else {
      this.setState({
        showUploadToFigshare: false,
      });
    }
  };

  handleCloseUpdateFigshare = (uploadComplete: boolean) => {
    if (uploadComplete) {
      this.props.handleFigshareUploadComplete().then(() => {
        this.setState({
          showUpdateFigshare: false,
        });
      });
    } else {
      this.setState({
        showUpdateFigshare: false,
      });
    }
  };

  renderFigshareLinkedContent() {
    if (
      !this.props.datasetVersion.figshare.is_public &&
      !this.props.datasetVersion.figshare.url_private_html
    ) {
      return (
        <p>This dataset version is linked to a private article on Figshare.</p>
      );
    }

    const articleLink = (
      <p>
        This dataset version is linked to a{" "}
        <a
          href={
            this.props.datasetVersion.figshare.is_public
              ? this.props.datasetVersion.figshare.url_public_html
              : this.props.datasetVersion.figshare.url_private_html
          }
          target="_blank"
          rel="noopener"
        >
          {this.props.datasetVersion.figshare.is_public ? "public" : "private"}{" "}
          Figshare article
        </a>
        .
      </p>
    );
    return (
      <React.Fragment>
        {articleLink}
        <span>
          <Button
            bsStyle="link"
            onClick={() => {
              const map: { [taigaId: string]: string } = {};
              this.props.figshareLinkedFiles.forEach((value) => {
                map[value.currentTaigaId] = value.downloadLink;
              });
              const blob = new Blob([JSON.stringify(map, null, 2)], {
                type: "application/json;charset=utf-8",
              });
              saveAs(blob, "taiga_figshare_map.json");
            }}
          >
            Download Figshare link mapping for taigapy{" "}
            <i className="fa fa-download" aria-hidden="true"></i>
          </Button>
        </span>
      </React.Fragment>
    );
  }

  renderFigshareNotLinkedContent() {
    const { userFigshareAccountLinked } = this.props;
    return (
      <React.Fragment>
        <p>This dataset version is not linked with any Figshare article.</p>
        {!userFigshareAccountLinked && (
          <p>
            Link your Figshare account to upload this dataset version to
            Figshare through the sidebar of the{" "}
            <Link to={relativePath("token")}>My Token</Link> page.
          </p>
        )}
        <Button
          onClick={this.showUploadToFigshare}
          disabled={!userFigshareAccountLinked}
        >
          Upload to Figshare as new article
        </Button>
        <Button
          onClick={this.showUpdateFigshare}
          disabled={!userFigshareAccountLinked}
        >
          Upload to Figshare as a new version of an existing article
        </Button>
      </React.Fragment>
    );
  }

  render() {
    const { userFigshareAccountLinked } = this.props;

    return (
      <Row componentClass="section">
        <Col md={12}>
          <h2>Link with Figshare</h2>
          {this.props.datasetVersion && (
            <React.Fragment>
              {this.props.datasetVersion.figshare
                ? this.renderFigshareLinkedContent()
                : this.renderFigshareNotLinkedContent()}
              <UploadToFigshare
                tapi={this.props.tapi}
                handleClose={this.handleCloseUploadToFigshare}
                show={this.state.showUploadToFigshare}
                userFigshareLinked={userFigshareAccountLinked}
                datasetName={this.props.datasetName}
                datasetVersion={this.props.datasetVersion}
              />
              <UpdateFigshare
                tapi={this.props.tapi}
                handleClose={this.handleCloseUpdateFigshare}
                show={this.state.showUpdateFigshare}
                datasetVersion={this.props.datasetVersion}
              />
            </React.Fragment>
          )}
        </Col>
      </Row>
    );
  }
}
