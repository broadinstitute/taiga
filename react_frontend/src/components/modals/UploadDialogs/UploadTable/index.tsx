import * as React from "react";
import UploadController from "../UploadController";
import type { UploadTableFile } from "../types";
import ProcessingTable from "./ProcessingTable";
import InputTable from "./InputTable";

interface UploadTableProps {
  isProcessing: boolean;
  files: Array<UploadTableFile>;
  controller: UploadController;
}

function UploadTable({ isProcessing, files, controller }: UploadTableProps) {
  if (isProcessing) {
    return <ProcessingTable files={files} />;
  }

  return <InputTable files={files} controller={controller} />;
}

export default UploadTable;
