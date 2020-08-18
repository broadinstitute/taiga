import * as React from "react";
import { Button } from "react-bootstrap";
import { Link } from "react-router-dom";
import { saveAs } from "file-saver";

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
  figshareLinkedFiles: Map<
    string,
    {
      downloadLink: string;
      currentTaigaId: string;
      readableTaigaId?: string;
    }
  >;
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
            {this.props.datasetVersion.figshare
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
