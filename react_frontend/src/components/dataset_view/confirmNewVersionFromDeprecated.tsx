import * as React from "react";
import { DatasetVersion } from "../../models/models";
import getConfirmation from "../../utilities/getConfirmation";

function confirmNewVersionFromDeprecated(datasetVersion: DatasetVersion) {
  const { state } = datasetVersion;

  return getConfirmation({
    title: "Are you sure?",
    message: (
      <div>
        <p>
          This version is {state === "deprecated" ? "deprecated" : "deleted"}.
          Are you sure you want to create a new version based on it?
        </p>
      </div>
    ),
    noText: "Cancel",
    yesText: "Create new version",
    yesButtonBsStyle: "warning",
  });
}

export default confirmNewVersionFromDeprecated;
