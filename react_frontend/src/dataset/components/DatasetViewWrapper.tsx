import * as React from "react";
import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";

import { Grid } from "react-bootstrap";

import { NotFound } from "src/components/NotFound";

import { TaigaApi } from "src/models/api";
import {
  User,
  Dataset,
  DatasetVersion,
  ActivityLogEntry,
} from "src/models/models";

import { relativePath } from "src/utilities/route";
import {
  getDatasetPermaname,
  getLatestVersionFromDataset,
} from "src/utilities/dataset";
import DatasetView from "./DatasetView";

interface Props {
  tapi: TaigaApi;
  user: User;
}

const redirectToLatestDatasetVersion = (dataset: Dataset) => {
  window.location.replace(
    relativePath(
      `dataset/${getDatasetPermaname(dataset)}/${getLatestVersionFromDataset(
        dataset
      )}`
    )
  );
};

const DatasetViewWrapper = (props: Props) => {
  const [dataset, setDataset] = useState<Dataset>(null);
  const [datasetVersion, setDatasetVersion] = useState<DatasetVersion>(null);
  const [activity, setActivity] = useState<Array<ActivityLogEntry>>(null);
  const [notFound, setNotFound] = useState(false);

  const { user, tapi } = props;
  const { datasetId, datasetVersionId } = useParams<{
    datasetId: string;
    datasetVersionId: string;
  }>();

  useEffect(() => {
    async function fetchData() {
      if (datasetId && datasetVersionId) {
        await tapi
          .get_dataset_version_with_dataset(datasetId, datasetVersionId)
          .then((datasetAndDatasetVersion) => {
            tapi
              .get_activity_log_for_dataset_id(
                datasetAndDatasetVersion.dataset.id
              )
              .then((activityLogEntries) => {
                setDataset(datasetAndDatasetVersion.dataset);
                setDatasetVersion(datasetAndDatasetVersion.datasetVersion);
                setActivity(activityLogEntries);

                if (
                  datasetId !==
                    getDatasetPermaname(datasetAndDatasetVersion.dataset) ||
                  datasetVersionId !==
                    datasetAndDatasetVersion.datasetVersion.name
                ) {
                  window.history.replaceState(
                    null,
                    "",
                    relativePath(
                      `dataset/${getDatasetPermaname(
                        datasetAndDatasetVersion.dataset
                      )}/${datasetAndDatasetVersion.datasetVersion.name}`
                    )
                  );
                }
              });
          })
          .catch(() => setNotFound(true));
      } else if (datasetId && !datasetVersionId) {
        await tapi
          .get_dataset(datasetId)
          .then(redirectToLatestDatasetVersion)
          .catch(() => setNotFound(true));
      } else {
        await tapi.get_dataset_version(datasetVersionId).then((dv) => {
          tapi
            .get_dataset(dv.dataset_id)
            .then(redirectToLatestDatasetVersion)
            .catch(() => setNotFound(true));
        });
      }
    }

    fetchData();
  }, [datasetId, datasetVersionId, tapi]);

  useEffect(() => {
    if (dataset != null && datasetVersion != null) {
      document.title = `${dataset.name} Version ${datasetVersion.name} | Taiga`;
    }
  }, [dataset, datasetVersion]);

  if (notFound) {
    let message = "";
    if (datasetId && datasetVersionId) {
      message = `Dataset "${datasetId}" with version "${datasetVersionId}" `;
    } else if (datasetId) {
      message = `Dataset "${datasetId}" `;
    } else {
      message = `Dataset version "${datasetVersionId}" `;
    }
    message +=
      "does not exist. Please check that this id is correct. We are also available via the feedback button.";
    return <NotFound message={message} />;
  }

  if (!(dataset && datasetVersion && activity)) {
    return <div id="main-content">Loading</div>;
  }

  return (
    <Grid>
      <DatasetView
        key={`dataset/${getDatasetPermaname(dataset)}/${datasetVersion.name}`}
        tapi={tapi}
        user={user}
        dataset={dataset}
        datasetVersion={datasetVersion}
        activityLog={activity}
      />
    </Grid>
  );
};

export default DatasetViewWrapper;
