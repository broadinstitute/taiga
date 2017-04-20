import {InitialFileType} from "../models/models";

export function toLocalDateString(stringDate: string) {
    let _date = new Date(stringDate);
    var options = {
        month: "2-digit", day: "2-digit", year: "2-digit"
    };
    return _date.toLocaleDateString("en-us", options);
}

export function getInitialFileTypeFromMimeType(mimeTypeOrEnum: string|InitialFileType): InitialFileType {
    // Manage the case of receiving the Enum

    // Options values should also be changed in formats.tsx
    // TODO: Use the same text to print to the user between selection of option and print result in formats.tsx
    let formattedType: InitialFileType = InitialFileType.Raw;
    if (mimeTypeOrEnum in InitialFileType) {
        formattedType = mimeTypeOrEnum as InitialFileType;
    }
    else {
        if (mimeTypeOrEnum == 'text/csv') {
            formattedType = InitialFileType.NumericMatrixCSV;
        }
        else if (mimeTypeOrEnum == 'text/tab-separated-values') {
            formattedType = InitialFileType.NumericMatrixTSV;
        }
        else {
            formattedType = InitialFileType.Raw;
        }
    }
    console.log("In getInitial: " + mimeTypeOrEnum);
    console.log("Returning: " + mimeTypeOrEnum);
    return formattedType;
}

