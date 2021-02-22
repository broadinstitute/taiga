import * as React from "react";
import update from "immutability-helper";

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
        datasetVersion={datasetVersion}
        updateDataset={(key: keyof Dataset, value: any) =>
          setWorkingDataset(update(workingDataset, { [key]: { $set: value } }))
        }
      />
      <ContentSection
        tapi={tapi}
        datasetPermaname={datasetPermaname}
        datasetVersion={datasetVersion}
        figshareLinkedFiles={figshareLinkedFiles}
      />
      <CodeSampleSection
        datasetPermaname={datasetPermaname}
        datasetVersion={datasetVersion}
      />
      <FigshareSection
        tapi={tapi}
        userFigshareAccountLinked={user.figshare_account_linked}
        datasetName={workingDataset.name}
        datasetVersion={datasetVersion}
        figshareLinkedFiles={figshareLinkedFiles}
        handleFigshareUploadComplete={null}
      />
      <ActivityLogSection activityLog={activityLog} />
    </div>
  );
};

export default DatasetView;
