import { Dataset } from "src/models/models";

export const getLatestVersionFromDataset = (dataset: Dataset): number =>
  Math.max.apply(
    Math,
    dataset.versions.map((dv) => parseInt(dv.name))
  );

export const getDatasetPermaname = (dataset: Dataset): string =>
  dataset.permanames[dataset.permanames.length - 1];
