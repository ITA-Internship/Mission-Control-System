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

const CSRF_BOOTSTRAP_PATH =
  "/api/accounts/login/";

export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(status: number, body: unknown) {
    super(
      `API request failed with status ${status}.`,
    );

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

export interface DownloadedFile {
  blob: Blob;
  filename?: string;
}

export type QueryValue =
  | string
  | number
  | boolean
  | null
  | undefined;

function getCookie(
  name: string,
): string | undefined {
  if (typeof document === "undefined") {
    return undefined;
  }

  const prefix =
    `${encodeURIComponent(name)}=`;

  const cookie = document.cookie
    .split("; ")
    .find((item) =>
      item.startsWith(prefix),
    );

  if (!cookie) {
    return undefined;
  }

  const value = cookie.slice(
    prefix.length,
  );

  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

function buildApiUrl(path: string): string {
  const normalizedPath =
    path.startsWith("/")
      ? path
      : `/${path}`;

  return `${API_BASE_URL}${normalizedPath}`;
}

/**
 * Append the defined entries of `params`
 * to `path` as a query string.
 *
 * Empty strings, null and undefined are
 * dropped so unset filters do not reach
 * the API.
 */
export function withQuery(
  path: string,
  params: Record<string, QueryValue>,
): string {
  const search = new URLSearchParams();

  for (
    const [key, value] of Object.entries(
      params,
    )
  ) {
    if (
      value === null ||
      value === undefined ||
      value === ""
    ) {
      continue;
    }

    search.set(key, String(value));
  }

  const query = search.toString();

  return query
    ? `${path}?${query}`
    : path;
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

function getResponseField(
  body: unknown,
  field: string,
): string | undefined {
  if (
    typeof body !== "object" ||
    body === null ||
    Array.isArray(body)
  ) {
    return undefined;
  }

  const value = (
    body as Record<string, unknown>
  )[field];

  return typeof value === "string"
    ? value
    : undefined;
}

function isCsrfApiError(
  error: unknown,
): error is ApiError {
  if (
    !(error instanceof ApiError) ||
    error.status !== 403
  ) {
    return false;
  }

  const code = getResponseField(
    error.body,
    "code",
  )?.toLowerCase();

  if (
    code === "csrf_failed" ||
    code === "csrf_failure"
  ) {
    return true;
  }

  const detail = (
    typeof error.body === "string"
      ? error.body
      : getResponseField(
          error.body,
          "detail",
        )
  )?.toLowerCase();

  return Boolean(
    detail?.includes("csrf"),
  );
}

function parseFilename(
  disposition: string | null,
): string | undefined {
  if (!disposition) {
    return undefined;
  }

  const encoded =
    /filename\*=UTF-8''([^;]+)/i.exec(
      disposition,
    );

  if (encoded) {
    try {
      return decodeURIComponent(
        encoded[1],
      );
    } catch {
      return encoded[1];
    }
  }

  const plain =
    /filename="?([^";]+)"?/i.exec(
      disposition,
    );

  return plain
    ? plain[1]
    : undefined;
}

function buildRequestHeaders(
  method: string,
  initialHeaders:
    | HeadersInit
    | undefined,
  accept: string,
  hasJsonBody: boolean,
): Headers {
  const headers =
    new Headers(initialHeaders);

  headers.set("Accept", accept);

  if (hasJsonBody) {
    headers.set(
      "Content-Type",
      "application/json",
    );
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

  return headers;
}

async function sendRequest(
  path: string,
  method: string,
  headers: Headers,
  body: BodyInit | undefined,
  options: Omit<
    RequestInit,
    "body"
  >,
): Promise<Response> {
  try {
    return await fetch(
      buildApiUrl(path),
      {
        ...options,
        method,
        headers,
        body,
        credentials: "include",
      },
    );
  } catch (error) {
    if (isAbortError(error)) {
      throw error;
    }

    throw new NetworkError();
  }
}

async function apiRequestOnce<T>(
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

  if (
    json !== undefined &&
    formData !== undefined
  ) {
    throw new Error(
      "apiRequest does not support both json and formData in the same request.",
    );
  }

  const headers =
    buildRequestHeaders(
      method,
      initialHeaders,
      "application/json",
      json !== undefined,
    );

  let body: BodyInit | undefined;

  if (json !== undefined) {
    body = JSON.stringify(json);
  }

  if (formData !== undefined) {
    /*
     * Let the browser set the multipart
     * boundary automatically.
     */
    headers.delete("Content-Type");
    body = formData;
  }

  const response =
    await sendRequest(
      path,
      method,
      headers,
      body,
      options,
    );

  const responseBody =
    await parseResponseBody(
      response,
    );

  if (!response.ok) {
    throw new ApiError(
      response.status,
      responseBody,
    );
  }

  return responseBody as T;
}

async function refreshCsrfState(
  signal?: AbortSignal | null,
): Promise<void> {
  await apiRequestOnce<unknown>(
    CSRF_BOOTSTRAP_PATH,
    {
      method: "GET",
      cache: "no-store",
      signal,
    },
  );
}

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const method = (
    options.method ?? "GET"
  ).toUpperCase();

  try {
    return await apiRequestOnce<T>(
      path,
      options,
    );
  } catch (error) {
    /*
     * Safe requests do not require CSRF.
     * Non-CSRF 403 responses must not be
     * retried as they may be genuine
     * authorization failures.
     */
    if (
      SAFE_METHODS.has(method) ||
      !isCsrfApiError(error)
    ) {
      throw error;
    }

    /*
     * Bootstrap a fresh CSRF cookie and
     * repeat the original request exactly
     * once.
     */
    await refreshCsrfState(
      options.signal,
    );

    return apiRequestOnce<T>(
      path,
      options,
    );
  }
}

/**
 * Fetch a binary payload, such as a CSV
 * export or protected media, together
 * with the filename advertised by the API.
 */
export async function apiDownload(
  path: string,
  {
    headers: initialHeaders,
    ...options
  }: Omit<
    ApiRequestOptions,
    "json" | "formData"
  > = {},
): Promise<DownloadedFile> {
  const method = (
    options.method ?? "GET"
  ).toUpperCase();

  const headers =
    buildRequestHeaders(
      method,
      initialHeaders,
      "*/*",
      false,
    );

  const response =
    await sendRequest(
      path,
      method,
      headers,
      undefined,
      options,
    );

  if (!response.ok) {
    const responseBody =
      await parseResponseBody(
        response,
      );

    throw new ApiError(
      response.status,
      responseBody,
    );
  }

  return {
    blob: await response.blob(),
    filename: parseFilename(
      response.headers.get(
        "Content-Disposition",
      ),
    ),
  };
}