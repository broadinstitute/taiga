/// <reference types="@types/jest" />

import {
    InitialFileType
} from "../models/models";

import { TaigaApi } from "../models/api";
import { file } from "@babel/types";
import { UploadTracker, UploadFileType, UploadStatus, pollFunction, UploadFile } from "../components/UploadTracker";

let tapi = new TaigaApi("http://localhost:8080/taiga/api", "test-token");

// let test: any;
// let expect: any;

test('pollFuncLoop', () => {
    let counter = [0];
    return pollFunction(10, () => {
        console.log("counter=" + counter[0]);
        counter[0] += 1;
        if (counter[0] > 3) {
            return Promise.resolve(false);
        } else {
            return Promise.resolve(true);
        }
    }).then(() => {
        expect(counter[0]).toBe(4);
    })
}, 60 * 1000);

test('bad taiga id upload', () => {
    let t = new UploadTracker(tapi);
    let uploadFiles = [
        { name: "taiga", fileType: UploadFileType.TaigaPath, existingTaigaId: "invalid" },
    ] as Array<UploadFile>;
    let params = { folderId: "public", description: "test upload description", name: "test name" };
    let lastStatus = [null] as Array<UploadStatus>;
    let callback = (status: Array<UploadStatus>) => {
        console.log("update:", status);
        expect(status.length).toEqual(1);
        status.forEach((x, i) => {
            lastStatus[i] = x;
        });
    };

    let reachedBad = [false];

    return t.upload(uploadFiles, params, callback).then(() => {
        reachedBad[0] = true;
    }).catch((reason) => {
        console.log("after t.upload");
        expect(lastStatus[0].progress).toEqual(0);
        expect(lastStatus[0].progressMessage).toEqual("Error: The following was not formatted like a valid taiga ID: invalid");
    }).then(() => {
        expect(reachedBad[0]).toBe(false);
    });
    // .catch((err) => {
    //     console.error(err);
    //     throw "Bad";
    // });

})

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


