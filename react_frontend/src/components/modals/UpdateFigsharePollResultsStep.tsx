import * as React from "react";
import { Modal, Button } from "react-bootstrap";
import update from "immutability-helper";

import FigshareUploadStatusTable from "./FigshareUploadStatusTable";

import { TaskStatus, DatasetVersionDatafiles } from "../../models/models";
import TaigaApi from "../../models/api";
import { UploadFileStatus } from "../../models/figshare";

import { relativePath } from "../../utilities/route";

interface Props {
  tapi: TaigaApi;
  datafiles: ReadonlyArray<DatasetVersionDatafiles>;
  initialUploadResults: ReadonlyArray<UploadFileStatus>;
  onUploadComplete: () => void;
}

interface State {
  uploadResults: ReadonlyArray<UploadFileStatus>;
}

export default class UpdateFigsharePollResultsStep extends React.Component<
  Props,
  State
> {
  datafileIdToName: Map<string, string>;

  constructor(props: Props) {
    super(props);

    if (this.isUploadComplete(props.initialUploadResults)) {
      props.onUploadComplete();
    }

    this.state = {
      uploadResults: props.initialUploadResults,
    };

    this.datafileIdToName = new Map(
      props.datafiles.map((datafile) => [datafile.id, datafile.name])
    );

    props.initialUploadResults.forEach((file, i) => {
      if (file.task_id) {
        this.pollUploadToFigshareFile(i, file.task_id);
      }
    });
  }

  pollUploadToFigshareFile(i: number, taskId: string) {
    this.props.tapi.get_task_status(taskId).then((newStatus: TaskStatus) => {
      this.setState(
        {
          uploadResults: update(this.state.uploadResults, {
            [i]: { taskStatus: { $set: newStatus } },
          }),
        },
        () => {
          if (newStatus.state != "SUCCESS" && newStatus.state != "FAILURE") {
            setTimeout(() => this.pollUploadToFigshareFile(i, taskId), 1000);
          } else if (this.isUploadComplete(this.state.uploadResults)) {
            this.props.onUploadComplete();
          }
        }
      );
    });
  }

  isUploadComplete(uploadResults: ReadonlyArray<UploadFileStatus>) {
    return uploadResults.every(
      (file) =>
        !!file.failure_reason ||
        (file.taskStatus &&
          (file.taskStatus.state == "SUCCESS" ||
            file.taskStatus.state == "FAILURE"))
    );
  }

  render() {
    return (
      <Modal.Body
        // @ts-expect-error
        bsClass="modal-body figshare-modal-body"
      >
        <FigshareUploadStatusTable
          datafileIdToName={this.datafileIdToName}
          uploadResults={this.state.uploadResults}
        />
      </Modal.Body>
    );
  }
}
