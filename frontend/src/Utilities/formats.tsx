import { InitialFileType } from "../models/models";

export function toLocalDateString(stringDate: string) {
    let date = new Date(stringDate);
    return date.toLocaleDateString();
}

export function getInitialFileTypeFromMimeType(mimeTypeOrEnum: string|InitialFileType) : InitialFileType {
    // Manage the case of receiving the Enum
    let formattedType: InitialFileType = InitialFileType.Raw;
    if(mimeTypeOrEnum in InitialFileType){
        formattedType = mimeTypeOrEnum as InitialFileType;
    }
    else {
        if (mimeTypeOrEnum == 'text/csv') {
            formattedType = InitialFileType.NumericMatrixCSV;
        }
        else if(mimeTypeOrEnum == 'text/tab-separated-values') {
            formattedType = InitialFileType.NumericMatrixTSV;
        }
        else {
            formattedType = InitialFileType.Raw;
        }
    }
    console.log("In getInitial: "+ mimeTypeOrEnum);
    console.log("Returning: " + mimeTypeOrEnum);
    return formattedType;
}

