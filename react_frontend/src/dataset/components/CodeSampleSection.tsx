import * as React from "react";

import { Col, Row } from "react-bootstrap";

import { DatasetVersion, DatasetVersionDatafiles } from "src/models/models";

interface Props {
  datasetPermaname: string;
  datasetVersion: DatasetVersion;
}
const onlyRawAvailable = (df: DatasetVersionDatafiles): boolean => {
  const onlyRawAvailable =
    df.allowed_conversion_type.length == 1 &&
    df.allowed_conversion_type[0] == "raw";
  return onlyRawAvailable;
};

const CodeSampleSection = (props: Props) => {
  const { datasetPermaname, datasetVersion } = props;
  const s3AndVirtualDatafiles = datasetVersion.datafiles.filter(
    (df) => !df.gcs_path
  );
  let rBlock = "library(taigr);\n";

  let rBlockLinks = s3AndVirtualDatafiles.map((df) => {
    let r_name = df.name.replace(/[^A-Za-z0-9]+/g, ".");
    if (onlyRawAvailable(df)) {
      return `${r_name} <- download.raw.from.taiga(data.name='${datasetPermaname}', data.version=${datasetVersion.version}, data.file='${df.name}')`;
    } else {
      return `${r_name} <- load.from.taiga(data.name='${datasetPermaname}', data.version=${datasetVersion.version}, data.file='${df.name}')`;
    }
  });
  rBlock += rBlockLinks.join("\n");

  let pythonBlock = "from taigapy import TaigaClient\n";
  pythonBlock += "tc = TaigaClient()\n";

  let pythonBlockLines = s3AndVirtualDatafiles.map((df) => {
    let python_name = df.name.replace(/[^A-Za-z0-9]+/g, "_");

    if (onlyRawAvailable(df)) {
      return `${python_name} = tc.download_to_cache(name='${datasetPermaname}', version=${datasetVersion.version}, file='${df.name}')  # download_to_cache for raw`;
    } else {
      return `${python_name} = tc.get(name='${datasetPermaname}', version=${datasetVersion.version}, file='${df.name}')`;
    }
  });
  pythonBlock += pythonBlockLines.join("\n");

  return (
    <>
      <Row componentClass="section">
        <Col md={12}>
          <h2>
            Direct access from R (
            <a href="https://github.com/broadinstitute/taigr">
              TaigR Documentation
            </a>
            )
          </h2>
          <pre>{rBlock}</pre>
        </Col>
      </Row>
      <Row componentClass="section">
        <Col md={12}>
          <h2>
            Direct access from Python (
            <a href="https://github.com/broadinstitute/taigapy">
              Taigapy Documentation
            </a>
            )
          </h2>
          <pre>{pythonBlock}</pre>
        </Col>
      </Row>
    </>
  );
};

export default CodeSampleSection;
