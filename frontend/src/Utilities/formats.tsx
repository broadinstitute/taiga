import { InitialFileType } from "../models/models";

export function toLocalDateString(stringDate: string) {
    let date = new Date(stringDate);
    return date.toLocaleDateString();
}

export function getInitialFileTypeFromMimeType(mimeType : string) : InitialFileType {
    if (mimeType == 'text/csv') {
        return InitialFileType.NumericMatrixCSV;
    } else if(mimeType == 'text/tab-separated-values') {
        return InitialFileType.NumericMatrixTSV;
    } else {
        return InitialFileType.Raw;
    }
}

