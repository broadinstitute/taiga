import * as React from "react";
import { Col, Row } from "react-bootstrap";
import { BootstrapTable, TableHeaderColumn } from "react-bootstrap-table";

import {
  ActivityLogEntry,
  CreationActivityLogEntry,
  NameUpdateActivity,
  DescriptionUpdateActivity,
  VersionAdditionActivity,
  LogStartActivity,
  ActivityTypeEnum,
} from "src/models/models";

interface Props {
  activityLog: Array<ActivityLogEntry>;
}

const activityLogDateFormatter = (
  cell: string,
  row: ActivityLogEntry
): string => {
  return new Date(cell).toLocaleString();
};
const descriptionDetailsFormatter = (
  description: string | null,
  title = "Description"
): React.ReactNode => {
  if (!description) {
    return null;
  }
  return (
    <details>
      <summary>{title}</summary>
      <span className="activity-log-description">{description}</span>
    </details>
  );
};

const activityLogTypeFormatter = (
  cell: ActivityTypeEnum,
  row: ActivityLogEntry
) => {
  if (cell == ActivityTypeEnum.created) {
    return (
      <div>
        <div>
          Created dataset{" "}
          <strong>{(row as CreationActivityLogEntry).dataset_name}</strong>
        </div>
        {descriptionDetailsFormatter(
          (row as CreationActivityLogEntry).dataset_description
        )}
      </div>
    );
  } else if (cell == ActivityTypeEnum.changed_name) {
    return (
      <span>
        Changed name to{" "}
        <strong>{(row as NameUpdateActivity).dataset_name}</strong>
      </span>
    );
  } else if (cell == ActivityTypeEnum.changed_description) {
    const changeDescriptionAction = !!(row as DescriptionUpdateActivity)
      .dataset_description
      ? "Changed"
      : "Deleted";
    return (
      <div>
        <div>
          {`${changeDescriptionAction} description for version `}
          <strong>{(row as DescriptionUpdateActivity).dataset_version}</strong>
        </div>
        {descriptionDetailsFormatter(
          (row as DescriptionUpdateActivity).dataset_description
        )}
      </div>
    );
  } else if (cell == ActivityTypeEnum.added_version) {
    return (
      <div>
        <div>
          Added dataset version{" "}
          <strong>{(row as VersionAdditionActivity).dataset_version}</strong>
        </div>
        {descriptionDetailsFormatter(row.comments, "Changelog")}
        {descriptionDetailsFormatter(
          (row as VersionAdditionActivity).dataset_description
        )}
      </div>
    );
  } else if (cell == ActivityTypeEnum.started_log) {
    return (
      <div>
        <div>
          Logs started for{" "}
          <strong>{(row as LogStartActivity).dataset_name}</strong> version{" "}
          <strong>{(row as LogStartActivity).dataset_version}</strong>
        </div>
        {descriptionDetailsFormatter(
          (row as LogStartActivity).dataset_description
        )}
      </div>
    );
  }
  return cell;
};
const ActivityLogSection = (props: Props) => {
  const { activityLog } = props;
  const options = {
    noDataText: "No activity logged yet",
    defaultSortName: "timestamp",
    defaultSortOrder: "desc",
  };
  return (
    <Row componentClass="section">
      <Col md={12}>
        <h2>Activity Log</h2>
        <BootstrapTable data={activityLog} options={options} pagination striped>
          <TableHeaderColumn dataField="id" isKey hidden>
            ID
          </TableHeaderColumn>
          <TableHeaderColumn
            dataField="timestamp"
            dataFormat={activityLogDateFormatter}
            dataSort
            width="200"
          >
            Date
          </TableHeaderColumn>
          <TableHeaderColumn dataField="user_name" dataSort width="150">
            Editor
          </TableHeaderColumn>
          <TableHeaderColumn
            dataField="type"
            dataFormat={activityLogTypeFormatter}
          >
            Type
          </TableHeaderColumn>
        </BootstrapTable>
      </Col>
    </Row>
  );
};

export default ActivityLogSection;
