/// <reference types="@types/jest" />

import {
    InitialFileType
} from "../models/models";

import { TaigaApi } from "../models/api";
import { file } from "@babel/types";
import { UploadTracker, UploadFileType, UploadStatus, pollFunction } from "../components/UploadTracker";

let tapi = new TaigaApi("http://localhost:8080/taiga/api", "test-token");

// let test: any;
// let expect: any;

xtest('pollFuncLoop', () => {
    let counter = [0];
    return pollFunction(1000, () => {
        console.log("counter=" + counter[0]);
        counter[0] += 1;
        if (counter[0] > 6) {
            return Promise.resolve(false);
        } else {
            return Promise.resolve(true);
        }
    }).then(() => {
        expect(counter[0]).toBe(4);
    })
}, 60 * 1000);

test('end-to-end test of uploading with the tracker', () => {
    let uploadFile = "blob";

    let t = new UploadTracker(tapi);
    let uploadFiles = [
        { name: "taiga", fileType: UploadFileType.TaigaPath, existingTaigaId: "sample-1.1/data" },
        { name: "upload", fileType: UploadFileType.Upload, uploadFile: uploadFile, uploadFormat: InitialFileType.Raw },
    ] as Array<UploadFile>;
    let params = { folderId: "public", description: "test upload description", name: "test name" };
    let lastStatus = [null, null] as Array<UploadStatus>;
    let callback = (status: Array<UploadStatus>) => {
        console.log("update:", status);
        expect(status.length).toEqual(2);
        status.forEach((x, i) => {
            lastStatus[i] = x;
        });
    };

    return t.upload(uploadFiles, params, callback).then(() => {
        console.log("after t.upload");
        expect(lastStatus[0].progress).toEqual(100);
        expect(lastStatus[0].progressMessage).toEqual("Added existing file");
        expect(lastStatus[1].progress).toEqual(100);
        expect(lastStatus[1].progressMessage).toEqual("Conversion done");
    });
    // .catch((err) => {
    //     console.error(err);
    //     throw "Bad";
    // });
}, 60 * 1000);


