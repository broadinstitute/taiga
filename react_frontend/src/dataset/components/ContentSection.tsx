import * as React from "react";
import { Link } from "react-router-dom";
import {
  Row,
  Col,
  Table,
  Button,
  Glyphicon,
  OverlayTrigger,
  Tooltip,
} from "react-bootstrap";

import ClipboardButton from "src/common/components/ClipboardButton";

import { FigshareLinkedFiles } from "src/dataset/models/models";
import { DataFileType, DatasetVersion, StatusEnum } from "src/models/models";
import { TaigaApi } from "src/models/api";

import { relativePath } from "src/utilities/route";

interface Props {
  tapi: TaigaApi;
  datasetPermaname: string;
  datasetVersion: DatasetVersion;
  figshareLinkedFiles: FigshareLinkedFiles;
}

const ContentSection = (props: Props) => {
  const { tapi, datasetPermaname, datasetVersion, figshareLinkedFiles } = props;
  const entries = datasetVersion.datafiles
    .sort((datafile_one, datafile_two) =>
      datafile_one.name.localeCompare(datafile_two.name, "en", {
        sensitivity: "base",
      })
    )
    .map((df, index) => {
      let linkToUnderlying = null;
      let gsPath = null;
      if (df.underlying_file_id) {
        const m = df.underlying_file_id.match(/([^.]+)\.([^/]+)\/.+/);

        const permaname = m[1];
        const version = m[2];

        linkToUnderlying = (
          <div>
            (
            <Link to={relativePath(`dataset/${permaname}/${version}`)}>
              {df.underlying_file_id}
            </Link>
            )
          </div>
        );
      }
      if (df.gcs_path) {
        gsPath = <div>({`gs://${df.gcs_path}`})</div>;
      }

      let figshareLinked = null;

      if (figshareLinkedFiles && figshareLinkedFiles.has(df.id)) {
        const figshareFileInfo = figshareLinkedFiles.get(df.id);
        if (figshareFileInfo.readableTaigaId) {
          const m = figshareFileInfo.readableTaigaId.match(
            /([^.]+)\.([^/]+)\/.+/
          );

          const figshareDatasetPermaname = m[1];
          const figshareDatasetVersion = m[2];
          figshareLinked = (
            <OverlayTrigger
              placement="top"
              overlay={
                <Tooltip id="tooltip">
                  {figshareFileInfo.readableTaigaId}
                </Tooltip>
              }
            >
              <Link
                to={relativePath(
                  `dataset/${figshareDatasetPermaname}/${figshareDatasetVersion}`
                )}
              >
                <Glyphicon glyph="ok" />
              </Link>
            </OverlayTrigger>
          );
        } else {
          figshareLinked = <Glyphicon glyph="ok" />;
        }
      }

      return (
        <tr key={index}>
          <td>
            {df.name}
            {linkToUnderlying}
            {gsPath}
          </td>
          <td>{df.short_summary}</td>
          {figshareLinkedFiles && <td>{figshareLinked}</td>}
          <td>
            {!gsPath && (
              <Button
                onClick={() => {
                  tapi
                    .get_datafile(
                      datasetPermaname,
                      datasetVersion.name,
                      datasetVersion.id,
                      df.name,
                      df.type == DataFileType.Raw ? "raw" : "raw_test",
                      "N"
                    )
                    .then((result) => {
                      window.location.href = result.urls[0];
                    });
                }}
              >
                <Glyphicon glyph="download-alt" />
              </Button>
            )}
          </td>
          <td>
            <ClipboardButton
              textToCopy={`${datasetPermaname}.${datasetVersion.name}/${df.name}`}
              tooltipId={df.id}
              disabled={datasetVersion.state == StatusEnum.Deleted}
            />
          </td>
        </tr>
      );
    });
  return (
    <Row componentClass="section">
      <Col md={12}>
        <h2>Contents</h2>
        <Table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Summary</th>
              {figshareLinkedFiles && <th>Uploaded to Figshare</th>}
              <th>Download</th>
              <th>Copy Taiga ID</th>
            </tr>
          </thead>
          <tbody>{entries}</tbody>
        </Table>
      </Col>
    </Row>
  );
};

export default ContentSection;
