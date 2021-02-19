import * as React from "react";
import { Table, ProgressBar } from "react-bootstrap";

import { UploadFileStatus } from "../../models/figshare";

interface Props {
  datafileIdToName: Map<string, string>;
  uploadResults: ReadonlyArray<UploadFileStatus>;
}
export default class FigshareUploadTable extends React.Component<Props> {
  render() {
    return (
      <Table responsive striped bsClass="table figshare-upload-files-table">
        <thead>
          <tr>
            <th>Datafile</th>
            <th>Upload status</th>
          </tr>
        </thead>
        <tbody>
          {this.props.uploadResults.map((file, i) => {
            let progressIndicator = null;

            const state = file.taskStatus ? file.taskStatus.state : null;
            if (file.failure_reason) {
              progressIndicator = (
                <ProgressBar
                  now={0}
                  label={`Failed to upload: ${file.failure_reason}`}
                  bsStyle="danger"
                />
              );
            } else if (state == "PROGRESS") {
              progressIndicator = (
                <ProgressBar
                  now={file.taskStatus.current * 100}
                  label="Uploading"
                />
              );
            } else if (state == "SUCCESS") {
              progressIndicator = <ProgressBar now={100} label="Uploaded" />;
            } else if (state == "FAILURE") {
              progressIndicator = (
                <ProgressBar
                  now={file.taskStatus.current * 100}
                  label="Failed to upload"
                  bsStyle="danger"
                />
              );
            }

            return (
              <tr key={file.datafile_id}>
                <td>{this.props.datafileIdToName.get(file.datafile_id)}</td>
                <td>{progressIndicator}</td>
              </tr>
            );
          })}
        </tbody>
      </Table>
    );
  }
}
