import * as React from "react";
import cx from "classnames";
import {
  FormControl,
  Glyphicon,
  Popover,
  OverlayTrigger,
} from "react-bootstrap";
import { InitialFileType } from "../../../../models/models";
import { UploadFileType } from "../../../UploadTracker";
import UploadController from "../UploadController"
import type { UploadTableFile } from "../types"
import styles from "./UploadTable.scss";

interface InputTableProps {
  files: Array<UploadTableFile>;
  controller: UploadController;
}

const CHARACTER_ENCODING_OPTIONS = ["ASCII", "ISO 8859-1", "UTF-8"];

function InputTable({ files, controller }: InputTableProps) {
  const requestEncoding = files.some((file) => !!file.uploadFile);

  return (
    <>
      {/*
        This <div> is just for a subtle visual thing. The table's header has a
        transparent background so you can see the scroll container's inner
        shadow through it. But when you scroll down and the table's header
        becomes sticky, we want it to now look opaque so you can't see the rows
        scroll behind it. This little <div> magically slides into place to
        accomplish that.
      */}
      <div className={styles.opaqueHeaderBackground} />
      <table className={cx('table', styles.table)}>
        <thead>
          <tr>
            <th className={styles.thName}>Name</th>
            <th  className={styles.thSource}>Source</th>
            {requestEncoding && (
              <th className={styles.thRequestEncode}>
                <span style={{ marginInlineEnd: 4 }}>Encoding</span>
                <OverlayTrigger
                  trigger={["hover", "focus"]}
                  placement="top"
                  overlay={
                    <Popover id="character-encoding">
                      Character encoding of the uploaded file (usually UTF-8).
                    </Popover>
                  }
                >
                  <Glyphicon glyph="glyphicon glyphicon-info-sign" />
                </OverlayTrigger>
              </th>
            )}
            <th className={styles.thDelete}>Delete</th>
          </tr>
        </thead>
        <tbody>
          {files.map((file, i) => (
            <InputFormRow
              key={i}
              file={file}
              index={i}
              controller={controller}
              requestEncoding={requestEncoding}
            />
          ))}
        </tbody>
      </table>
    </>
  );
}

interface InputFormRowProps {
  file: UploadTableFile;
  index: number;
  controller: UploadController;
  requestEncoding: boolean;
}

function InputFormRow({ file, index, controller, requestEncoding }: InputFormRowProps) {
  let source: React.ReactNode;
  let encodingInput: React.ReactNode = null;

  if (file.fileType === UploadFileType.GCSPath) {
    source = (
      <input
        className="form-control"
        placeholder="GCS Object Path"
        type="text"
        value={file.gcsPath}
        onChange={(e) => controller.onGCSPathChange(index, e.target.value)}
      />
    );
  } else if (file.fileType === UploadFileType.TaigaPath) {
    source = (
      <input
        className="form-control"
        placeholder="Taiga ID"
        type="text"
        value={file.existingTaigaId}
        onChange={(e) => controller.onTaigaIdChange(index, e.target.value)}
      />
    );
  } else if (file.fileType === UploadFileType.Upload) {
    source = (
      <select
        className="form-control"
        value={file.uploadFormat}
        onChange={(e) => controller.changeUploadFormat(index, e.target.value)}
      >
        <option value={InitialFileType.TableCSV}>{InitialFileType.TableCSV}</option>
        <option value={InitialFileType.NumericMatrixCSV}>{InitialFileType.NumericMatrixCSV}</option>
        <option value={InitialFileType.Raw}>{InitialFileType.Raw}</option>
      </select>
    );

    if (requestEncoding && file.uploadFile) {
      encodingInput = (
        <FormControl
          componentClass="select"
          defaultValue={file.encoding}
          onChange={(e) =>
            controller.onEncodingChange(index, (e.target as HTMLSelectElement).value)
          }
        >
          {CHARACTER_ENCODING_OPTIONS.map((encoding) => (
            <option key={encoding} value={encoding}>
              {encoding}
            </option>
          ))}
        </FormControl>
      );
    }
  } else {
    throw new Error("unknown filetype");
  }

  return (
    <tr>
      <td>
        <input
          type="text"
          value={file.name}
          onChange={(e) => controller.onNameChange(index, e.target.value)}
          className="form-control"
          placeholder="Name"
          required
        />
      </td>
      <td>{source}</td>
      {requestEncoding && <td>{encodingInput}</td>}
      <td>
        <button
          type="button"
          className="btn btn-default"
          aria-label="Delete"
          onClick={() => controller.onDelete(index)}
        >
          <span className="glyphicon glyphicon-trash" aria-hidden="true" />
        </button>
      </td>
    </tr>
  );
}

export default InputTable;
