export function toLocalDateString(stringDate: string) {
    let date = new Date(stringDate);
    return date.toLocaleDateString();
}