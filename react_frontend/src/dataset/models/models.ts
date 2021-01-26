export type FigshareLinkedFiles = Map<
  // datafile ID
  string,
  {
    downloadLink: string;
    currentTaigaId: string;
    readableTaigaId?: string;
  }
>;
