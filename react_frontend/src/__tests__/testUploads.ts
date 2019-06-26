import {
    InitialFileType
} from "../models/models";

import { TaigaApi } from "../models/api";
import { file } from "@babel/types";
import { UploadTracker, UploadFileType, UploadFile, UploadStatus } from "../components/UploadTracker";

let tapi = new TaigaApi("http://localhost:8080/taiga/api", "test-token");

test('end-to-end test of uploading with the tracker', () => {
    let t = new UploadTracker(tapi);
    let uploadFiles = [
        { name: "taiga", fileType: UploadFileType.TaigaPath, existingTaigaId: "sample-1.1/data" },
        //        { name: "upload", fileType: UploadFileType.Upload, uploadFile: file, uploadFormat: InitialFileType.Raw },
    ] as Array<UploadFile>;
    let params = { folderId: "public", description: "test upload description", name: "test name" };
    let callback = (status: Array<UploadStatus>) => {
        console.log("update:", status);
    };

    return t.upload(uploadFiles, params, callback);
    // .catch((err) => {
    //     console.error(err);
    //     throw "Bad";
    // });
});


