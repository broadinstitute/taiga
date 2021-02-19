import { FigshareLinkedFiles } from "src/dataset/models/models";
import { sortByName } from "./common";

import {
  DatasetVersionDatafiles as Datafile,
  DataFileType,
  DatasetVersion,
} from "../models/models";
import {
  File,
  UpdateArticleRemovedFigshareFile,
  UpdateArticleAdditionalTaigaDatafile,
  UpdateArticleUnchangedFile,
} from "../models/figshare";

export const getDefaultFilesToUpdate = (
  figshareFiles: Array<File>,
  datafiles: Array<Datafile>
): {
  removedFigshareFiles: Array<UpdateArticleRemovedFigshareFile>;
  additionalTaigaDatafiles: Array<UpdateArticleAdditionalTaigaDatafile>;
  unchangedFiles: Array<UpdateArticleUnchangedFile>;
} => {
  const getDefaultDatafileName = (datafile: Datafile) =>
    datafile.type == DataFileType.Raw ? datafile.name : `${datafile.name}.csv`;

  const removedFigshareFiles: Array<UpdateArticleRemovedFigshareFile> = [];
  const additionalTaigaDatafiles: Array<UpdateArticleAdditionalTaigaDatafile> = [];
  const unchangedFiles: Array<UpdateArticleUnchangedFile> = [];
  const matchedDatafiles = new Set<string>();

  figshareFiles.forEach((figshareFile) => {
    const matchingDataFileByMD5 = datafiles.find(
      (datafile) =>
        !matchedDatafiles.has(datafile.id) &&
        (datafile.original_file_md5 == figshareFile.supplied_md5 ||
          datafile.original_file_md5 == figshareFile.computed_md5)
    );
    if (matchingDataFileByMD5) {
      unchangedFiles.push({
        figshareFileId: figshareFile.id,
        datafileId: matchingDataFileByMD5.id,
        name: figshareFile.name,
        datafileName: matchingDataFileByMD5.name,
      });
      matchedDatafiles.add(matchingDataFileByMD5.id);
      return;
    }

    // Exclude file extension from figshareFile.name
    const figshareFileName = figshareFile.name.includes(".")
      ? figshareFile.name.substr(0, figshareFile.name.lastIndexOf("."))
      : figshareFile.name;

    const matchingDataFileByName = datafiles.find(
      (datafile) =>
        !matchedDatafiles.has(datafile.id) && datafile.name == figshareFileName
    );
    if (matchingDataFileByName) {
      removedFigshareFiles.push({
        figshareFileId: figshareFile.id,
        name: figshareFile.name,
        removeFile: true,
      });
      additionalTaigaDatafiles.push({
        datafileId: matchingDataFileByName.id,
        name: figshareFile.name,
        addFile: true,
        datafileName: matchingDataFileByName.name,
      });
      matchedDatafiles.add(matchingDataFileByName.id);
      return;
    }

    removedFigshareFiles.push({
      figshareFileId: figshareFile.id,
      name: figshareFile.name,
      removeFile: false,
    });
  });

  datafiles.forEach((datafile) => {
    if (matchedDatafiles.has(datafile.id)) {
      return;
    }
    additionalTaigaDatafiles.push({
      name: getDefaultDatafileName(datafile),
      datafileId: datafile.id,
      addFile: false,
      datafileName: datafile.name,
    });
  });

  removedFigshareFiles.sort(sortByName);
  additionalTaigaDatafiles.sort(sortByName);
  unchangedFiles.sort(sortByName);
  return {
    removedFigshareFiles,
    additionalTaigaDatafiles,
    unchangedFiles,
  };
};

export const getFigshareLinkedFiles = (
  datasetPermaname: string,
  datasetVersion: DatasetVersion
): FigshareLinkedFiles => {
  if (
    !datasetVersion.figshare ||
    !datasetVersion.figshare.files ||
    datasetVersion.figshare.files.length == 0
  ) {
    return null;
  }

  const figshareLinkedFiles: FigshareLinkedFiles = new Map();

  datasetVersion.datafiles.forEach((datafile) => {
    const file = datasetVersion.figshare.files.find(
      (file) =>
        file.taiga_datafile_id == datafile.id ||
        file.underlying_file_id == datafile.underlying_file_id
    );

    if (file) {
      const currentTaigaId = `${datasetPermaname}.${datasetVersion.version}/${datafile.name}`;
      if (file.taiga_datafile_id == datafile.id) {
        figshareLinkedFiles.set(datafile.id, {
          downloadLink: file.download_url,
          currentTaigaId,
        });
      } else {
        figshareLinkedFiles.set(datafile.id, {
          downloadLink: file.download_url,
          currentTaigaId,
          readableTaigaId: file.taiga_datafile_readable_id,
        });
      }
    }
  });

  return figshareLinkedFiles;
};
