export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly recovery: "retry" | "reload" = "retry"
  ) {
    super(message);
    this.name = "ApiError";
  }
}
