import * as React from "react";
import type { CreateDatasetDialogProps, CreateVersionDialogProps } from "./types";
import { UploadDialog } from "./UploadDialog";

export function CreateDatasetDialog(props: CreateDatasetDialogProps) {
  return (
    <UploadDialog
      title="Create new Dataset"
      showNameField={true}
      showChangesField={false}
      {...props}
    />
  );
}

export function CreateVersionDialog(props: CreateVersionDialogProps) {
  return (
    <UploadDialog
      title="Create new Dataset version"
      showNameField={false}
      showChangesField={true}
      {...props}
    />
  );
}
