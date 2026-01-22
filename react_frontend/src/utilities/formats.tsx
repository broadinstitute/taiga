import { InitialFileType } from "../models/models";

export function toLocalDateString(stringDate: string) {
  const _date = new Date(stringDate);
  const options: Intl.DateTimeFormatOptions = {
    month: "2-digit",
    day: "2-digit",
    year: "2-digit",
  };
  return _date.toLocaleDateString("en-US", options);
}

export function getInitialFileTypeFromMimeType(
  mimeTypeOrEnum: string | InitialFileType
): InitialFileType {
  // Manage the case of receiving the Enum

  // Options values should also be changed in formats.tsx
  // TODO: Use the same text to print to the user between selection of option and print result in formats.tsx
  let formattedType: InitialFileType = InitialFileType.Raw;
  if (mimeTypeOrEnum in InitialFileType) {
    formattedType = mimeTypeOrEnum as InitialFileType;
  } else {
    if (mimeTypeOrEnum == "text/csv") {
      formattedType = InitialFileType.NumericMatrixCSV;
    } else {
      formattedType = InitialFileType.Raw;
    }
  }
  return formattedType;
}

export function lastAccessFormatter(cell: any, row: any) {
  const _date = new Date(cell);
  const options: Intl.DateTimeFormatOptions = {
    month: "2-digit",
    day: "2-digit",
    year: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  };
  return _date.toLocaleString("en-US", options);
}
