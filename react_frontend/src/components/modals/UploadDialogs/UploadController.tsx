import update from "immutability-helper";
import * as filesize from "filesize";
import { InitialFileType } from "../../../models/models";
import { UploadFileType } from "../../UploadTracker";
import type { UploadTableFile } from "./types"

export class UploadController {
  files: Readonly<Array<UploadTableFile>>;
  listener: (x: any) => void;

  constructor(files: Readonly<Array<UploadTableFile>>, listener: (x: any) => void) {
    this.files = files;
    this.listener = listener;
  }

  getDefaultName(path: string) {
    let lastSlash = path.lastIndexOf("/");
    if (lastSlash >= 0) {
      path = path.substring(lastSlash + 1);
    }

    let lastDot = path.lastIndexOf(".");
    if (lastDot >= 0) {
      path = path.substring(0, lastDot);
    }

    return path;
  }

  addGCS(gcsPath: string) {
    let name = this.getDefaultName(gcsPath);
    this.addFile({
      name: name,
      computeNameFromTaigaId: false,
      fileType: UploadFileType.GCSPath,
      size: "unknown",
      gcsPath: gcsPath,
    });
  }

  addUpload(file: File) {
    let name = this.getDefaultName(file.name);
    this.addFile({
      name: name,
      computeNameFromTaigaId: false,
      fileType: UploadFileType.Upload,
      size: filesize(file.size),
      uploadFile: file,
      uploadFormat: InitialFileType.Raw,
      encoding: "UTF-8",
    });
  }

  addTaiga(existingTaigaId: string, size: string) {
    let name = this.getDefaultName(existingTaigaId);
    this.addFile({
      name: name,
      computeNameFromTaigaId: true,
      fileType: UploadFileType.TaigaPath,
      size: size,
      existingTaigaId: existingTaigaId,
    });
  }

  addFile(file: UploadTableFile) {
    this.files = update(this.files, { $push: [file] });
    this.listener(this.files);
  }

  changeUploadFormat(index: number, format: string) {
    this.files = update(this.files, {
      [index]: { uploadFormat: { $set: format } },
    });
    this.listener(this.files);
  }

  onDelete(index: number) {
    this.files = update(this.files, { $splice: [[index, 1]] });
    this.listener(this.files);
  }

  onTaigaIdChange(index: number, newValue: string) {
    let changes = { existingTaigaId: { $set: newValue } } as any;
    if (this.files[index].computeNameFromTaigaId) {
      changes.name = { $set: this.getDefaultName(newValue) };
    }
    this.files = update(this.files, { [index]: changes });
    this.listener(this.files);
  }

  onGCSPathChange(index: number, newValue: string) {
    let changes = { gcsPath: { $set: newValue } } as any;
    if (this.files[index].computeNameFromTaigaId) {
      changes.name = { $set: this.getDefaultName(newValue) };
    }
    this.files = update(this.files, { [index]: changes });
    this.listener(this.files);
  }

  onNameChange(index: number, newName: string) {
    this.files = update(this.files, {
      [index]: {
        name: { $set: newName },
        computeNameFromTaigaId: { $set: false },
      },
    });
    this.listener(this.files);
  }

  onEncodingChange(index: number, newEncoding: string) {
    this.files = update(this.files, {
      [index]: { encoding: { $set: newEncoding } },
    });
    this.listener(this.files);
  }
}

export default UploadController;
