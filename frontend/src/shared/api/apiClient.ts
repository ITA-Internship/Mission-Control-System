const SAFE_METHODS = new Set([
  "GET",
  "HEAD",
  "OPTIONS",
  "TRACE",
]);

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? ""
).replace(/\/+$/, "");

const CSRF_COOKIE_NAME =
  import.meta.env.VITE_CSRF_COOKIE_NAME ??
  "csrftoken";

const CSRF_HEADER_NAME =
  import.meta.env.VITE_CSRF_HEADER_NAME ??
  "X-CSRFToken";

export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(status: number, body: unknown) {
    super(`API request failed with status ${status}.`);

    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

export class NetworkError extends Error {
  constructor() {
    super("The API could not be reached.");
    this.name = "NetworkError";
  }
}

export function isAbortError(
  error: unknown,
): boolean {
  return (
    error instanceof Error &&
    error.name === "AbortError"
  );
}

interface ApiRequestOptions
  extends Omit<RequestInit, "body"> {
  json?: unknown;
  formData?: FormData;
}

function getCookie(
  name: string,
): string | undefined {
  if (typeof document === "undefined") {
    return undefined;
  }

  const prefix = `${encodeURIComponent(name)}=`;

  const cookie = document.cookie
    .split("; ")
    .find((item) => item.startsWith(prefix));

  if (!cookie) {
    return undefined;
  }

  const value = cookie.slice(prefix.length);

  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

function buildApiUrl(path: string): string {
  const normalizedPath = path.startsWith("/")
    ? path
    : `/${path}`;

  return `${API_BASE_URL}${normalizedPath}`;
}

async function parseResponseBody(
  response: Response,
): Promise<unknown> {
  const text = await response.text();

  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

export async function apiRequest<T>(
  path: string,
  {
    json,
    formData,
    headers: initialHeaders,
    ...options
  }: ApiRequestOptions = {},
): Promise<T> {
  const method = (
    options.method ?? "GET"
  ).toUpperCase();

  const headers = new Headers(initialHeaders);

  headers.set("Accept", "application/json");

  let body: BodyInit | undefined;

  if (
    json !== undefined &&
    formData !== undefined
  ) {
    throw new Error(
      "apiRequest does not support both json and formData in the same request.",
    );
  }

  if (json !== undefined) {
    headers.set(
      "Content-Type",
      "application/json",
    );

    body = JSON.stringify(json);
  }

  if (formData !== undefined) {
    headers.delete("Content-Type");
    body = formData;
  }

  if (!SAFE_METHODS.has(method)) {
    const csrfToken = getCookie(
      CSRF_COOKIE_NAME,
    );

    if (csrfToken) {
      headers.set(
        CSRF_HEADER_NAME,
        csrfToken,
      );
    }
  }

  let response: Response;

  try {
    response = await fetch(buildApiUrl(path), {
      ...options,
      method,
      headers,
      body,
      credentials: "include",
    });
  } catch (error) {
    if (isAbortError(error)) {
      throw error;
    }

    throw new NetworkError();
  }

  const responseBody =
    await parseResponseBody(response);

  if (!response.ok) {
    throw new ApiError(
      response.status,
      responseBody,
    );
  }

  return responseBody as T;
}
