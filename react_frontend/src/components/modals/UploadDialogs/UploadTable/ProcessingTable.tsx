import * as React from "react";
import cx from "classnames";
import type { UploadTableFile } from "../types";
import styles from "./UploadTable.scss";

interface ProcessingTableProps {
  files: Array<UploadTableFile>;
}

function ProcessingTable({ files }: ProcessingTableProps) {
  const rows = files.map((file, i) => {
    let progressBar = file.progressMessage as React.ReactNode;

    if (file.progress != null) {
      if (file.progressMessage?.startsWith("Error")) {
        progressBar = <code>{file.progressMessage}</code>;
      } else {
        progressBar = (
          <div className="progress">
            <div className="progress-bar" style={{ width: file.progress + "%" }}>
              {file.progressMessage}
            </div>
          </div>
        );
      }
    }

    return (
      <tr key={"r" + i}>
        <td>{file.name}</td>
        <td>{progressBar}</td>
      </tr>
    );
  });

  return (
    <>
      <div className={styles.opaqueHeaderBackground} />
      <table className={cx("table", styles.table)}>
        <thead>
          <tr>
            <th className={styles.thName}>Name</th>
            <th className={styles.thProgress}>Progress</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </>
  );
}

export default ProcessingTable;
