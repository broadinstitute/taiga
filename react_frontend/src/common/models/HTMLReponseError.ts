export default class HTMLResponseError extends Error {
  status: number;

  constructor(response: Response) {
    // Pass remaining arguments (including vendor specific ones) to parent constructor
    super(response.statusText);

    this.name = "HTMLResponseError";
    this.status = response.status;
  }
}
