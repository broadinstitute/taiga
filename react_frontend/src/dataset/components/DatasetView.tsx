import * as React from "react";
import update, { Query } from "immutability-helper";

import DatasetMetadataSection from "src/dataset/components/DatasetMetadataSection";
import ActivityLogSection from "src/dataset/components/ActivityLogSection";
import CodeSampleSection from "src/dataset/components/CodeSampleSection";
import ContentSection from "src/dataset/components/ContentSection";
import FigshareSection from "src/dataset/components/FigshareSection";

import {
  Dataset,
  DatasetVersion,
  ActivityLogEntry,
  User,
} from "src/models/models";
import TaigaApi from "src/models/api";

import { getDatasetPermaname } from "src/utilities/dataset";
import { getFigshareLinkedFiles } from "src/utilities/figshare";

import "src/dataset/styles/dataset.css";

interface Props {
  tapi: TaigaApi;
  user: User;
  dataset: Dataset;
  datasetVersion: DatasetVersion;
  activityLog: Array<ActivityLogEntry>;
}

const DatasetView = (props: Props) => {
  const { tapi, user, dataset, datasetVersion, activityLog } = props;
  const [workingDataset, setWorkingDataset] = React.useState(dataset);
  const [workingDatasetVersion, setWorkingDatasetVersion] = React.useState(
    datasetVersion
  );

  const datasetPermaname = getDatasetPermaname(workingDataset);
  const figshareLinkedFiles = React.useMemo(
    () => getFigshareLinkedFiles(datasetPermaname, datasetVersion),
    [datasetPermaname, datasetVersion]
  );

  return (
    <div className="dataset-view">
      <DatasetMetadataSection
        tapi={tapi}
        user={user}
        dataset={workingDataset}
        datasetVersion={workingDatasetVersion}
        updateDataset={(key: keyof Dataset, value: any) =>
          setWorkingDataset(update(workingDataset, { [key]: { $set: value } }))
        }
        updateDatasetVersion={(updates: Query<DatasetVersion>) => {
          setWorkingDatasetVersion(update(workingDatasetVersion, updates));
        }}
      />
      <ContentSection
        tapi={tapi}
        datasetPermaname={datasetPermaname}
        datasetVersion={workingDatasetVersion}
        figshareLinkedFiles={figshareLinkedFiles}
      />
      <CodeSampleSection
        datasetPermaname={datasetPermaname}
        datasetVersion={workingDatasetVersion}
      />
      <FigshareSection
        tapi={tapi}
        userFigshareAccountLinked={user.figshare_account_linked}
        datasetName={workingDataset.name}
        datasetVersion={workingDatasetVersion}
        figshareLinkedFiles={figshareLinkedFiles}
        handleFigshareUploadComplete={null}
      />
      <ActivityLogSection activityLog={activityLog} />
    </div>
  );
};

export default DatasetView;
