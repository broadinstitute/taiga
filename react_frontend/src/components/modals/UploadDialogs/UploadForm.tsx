import * as React from "react";
import { useRef } from "react";
import { FormControl } from "react-bootstrap";
import UploadController from "./UploadController";
import DataVersionFileList from "./DataVersionFileList";
import type { UploadTableFile } from "./types";
import styles from "./UploadDialogs.scss";

interface UploadFormProps {
  showNameField: boolean;
  showChangesField: boolean;
  controller: UploadController;
  name: string;
  description: string;
  changesDescription: string;
  files: Array<UploadTableFile>;
  onNameChange: (value: string) => void;
  onDescriptionChange: (value: string) => void;
  onChangesDescriptionChange: (value: string) => void;
  isProcessing: boolean;
}

function UploadForm(props: UploadFormProps) {
  const ref = useRef<HTMLDivElement>(null);

  let inputName = (
    <FormControl
      value={props.name}
      onChange={(evt) => {
        props.onNameChange((evt.target as any).value);
      }}
      type="text"
      placeholder="Dataset name"
    />
  );

  let inputDescription = (
    <FormControl
      value={props.description}
      onChange={(evt) => {
        props.onDescriptionChange((evt.target as any).value);
      }}
      componentClass="textarea"
      placeholder="Dataset description"
      rows={10}
    />
  );
  let inputChanges = (
    <FormControl
      value={props.changesDescription}
      onChange={(evt) => {
        props.onChangesDescriptionChange((evt.target as any).value);
      }}
      componentClass="textarea"
      placeholder="Describe what changed…"
      rows={5}
    />
  );

  const handleClickAddButton = () => {
    setTimeout(() => {
        ref.current?.parentElement.scrollTo({
          top: ref.current.scrollHeight,
        behavior: "smooth",
      });
    }, 0);
  }

  return (
    <div ref={ref} className="dataset-metadata">
      {props.showNameField && (
        <div className={styles.labelContainer}>
          <label>
            Dataset name
          </label>
          {inputName}
        </div>
      )}
      <div className={styles.labelContainer}>
        <label>Description</label>
        {inputDescription}
      </div>
      {props.showChangesField && (
        <div className={styles.labelContainer}>
          <label>
            Description of changes
          </label>
          {inputChanges}
        </div>
      )}
      <div className={styles.files}>
        <div className={styles.labelContainer}>
          <label>
            Files {props.files?.length > 0 ? ` (${props.files.length})` : null}
          </label>
        </div>
        <DataVersionFileList
          controller={props.controller}
          files={props.files}
          isProcessing={props.isProcessing}
          onClickAddButton={handleClickAddButton}
        />
      </div>
    </div>
  );
}

export default UploadForm;

