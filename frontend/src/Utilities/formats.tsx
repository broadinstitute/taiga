import { SupportedTypeEnum } from "../models/models";

export function toLocalDateString(stringDate: string) {
    let date = new Date(stringDate);
    return date.toLocaleDateString();
}

export function getFormatType(mimeTypeOrEnum: string|SupportedTypeEnum): SupportedTypeEnum {
    // Manage the case of receiving the Enum
    let formattedType: SupportedTypeEnum = SupportedTypeEnum.Raw;
    if(mimeTypeOrEnum in SupportedTypeEnum){
        formattedType = mimeTypeOrEnum as SupportedTypeEnum;
    }
    // Else we convert the type
    else {
        if (mimeTypeOrEnum == 'text/csv' || mimeTypeOrEnum == 'text/tab-separated-values') {
            formattedType = SupportedTypeEnum.Columnar;
        }
    }
    return formattedType;
}