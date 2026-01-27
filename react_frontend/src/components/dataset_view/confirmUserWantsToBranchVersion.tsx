import * as React from "react";
import { Dataset, DatasetVersion } from "../../models/models";
import { relativePath } from "../../utilities/route";
import getConfirmation from "../../utilities/getConfirmation";
import styles from "./confirm.scss";

function confirmUserWantsToBranchVersion(
  dataset: Dataset,
  datasetVersion: DatasetVersion
) {
  const thisVersion = Number(datasetVersion.version);
  const newerVersions = dataset.versions.slice(thisVersion);
  const permaname = dataset.permanames.slice(-1)[0];

  return getConfirmation({
    title: "Are you sure?",
    message: (
      <div>
        <p>
          This is not the latest version. If you create a new version based on
          this one,
          <br />
          it could be missing important files that were added later.
        </p>
        <p>
          {newerVersions.length === 1
            ? "This newer verision already exists:"
            : "These newer versions already exist:"}
        </p>
        <VersionList permaname={permaname} newerVersions={newerVersions} />
      </div>
    ),
    noText: "Cancel",
    yesText: "Use this version anyway",
    yesButtonBsStyle: "warning",
  });
}

const Icon = ({ className }: { className: string }) => (
  <>
    <i className={`glyphicon ${className}`} />{" "}
  </>
);

function VersionList({
  newerVersions,
  permaname,
}: {
  newerVersions: Dataset["versions"];
  permaname: string;
}) {
  return (
    <div className={styles.tableContainer}>
      <table>
        <thead>
          <tr>
            <th>Version</th>
            <th />
            <th>Link</th>
          </tr>
        </thead>
        <tbody>
          {newerVersions.map(version => (
            <tr key={version.id}>
              <td>{version.name}</td>
              <td>
                {version.state === "deprecated" && (
                  <span className={styles.deprecated}>
                    <Icon className="glyphicon-warning-sign" />
                    Deprecated
                  </span>
                )}
                {version.state === "deleted" && (
                  <span className={styles.deleted}>
                    <Icon className="glyphicon-exclamation-sign" />
                    Deleted
                  </span>
                )}
              </td>
              <td>
                <a
                  target="_blank"
                  href={relativePath(`/dataset/${permaname}/${version.name}`)}
                >
                  View <Icon className="glyphicon-new-window" />
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default confirmUserWantsToBranchVersion;
