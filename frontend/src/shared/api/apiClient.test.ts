import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

import {
  ApiError,
  apiRequest,
} from "./apiClient";

function jsonResponse(
  body: unknown,
  status = 200,
): Response {
  return new Response(
    JSON.stringify(body),
    {
      status,
      headers: {
        "Content-Type":
          "application/json",
      },
    },
  );
}

function setCsrfCookie(
  value: string,
): void {
  document.cookie =
    `csrftoken=${encodeURIComponent(value)}; path=/`;
}

function clearCsrfCookie(): void {
  document.cookie =
    "csrftoken=; Max-Age=0; path=/";
}

describe("apiRequest CSRF retry", () => {
  it("refreshes CSRF state and retries an unsafe request once", async () => {
    setCsrfCookie("stale-token");

    const fetchMock = vi.mocked(
      globalThis.fetch,
    );

    // Initial unsafe request fails.
    fetchMock.mockResolvedValueOnce(
      jsonResponse(
        {
          detail:
            "CSRF verification failed. Request aborted.",
        },
        403,
      ),
    );

    // CSRF bootstrap refreshes the cookie.
    fetchMock.mockImplementationOnce(
      async () => {
        setCsrfCookie("fresh-token");

        return jsonResponse({
          detail: "CSRF cookie set.",
        });
      },
    );

    // Retried unsafe request succeeds.
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        saved: true,
      }),
    );

    await expect(
      apiRequest<{
        saved: boolean;
      }>("/api/test-resource/", {
        method: "POST",
        json: {
          name: "demo",
        },
      }),
    ).resolves.toEqual({
      saved: true,
    });

    expect(
      fetchMock,
    ).toHaveBeenCalledTimes(3);

    expect(
      String(
        fetchMock.mock.calls[0]?.[0],
      ),
    ).toContain(
      "/api/test-resource/",
    );

    expect(
      String(
        fetchMock.mock.calls[1]?.[0],
      ),
    ).toContain(
      "/api/accounts/login/",
    );

    expect(
      String(
        fetchMock.mock.calls[2]?.[0],
      ),
    ).toContain(
      "/api/test-resource/",
    );

    const firstRequestHeaders =
      new Headers(
        fetchMock.mock.calls[0]?.[1]
          ?.headers,
      );

    const retryRequestHeaders =
      new Headers(
        fetchMock.mock.calls[2]?.[1]
          ?.headers,
      );

    expect(
      firstRequestHeaders.get(
        "X-CSRFToken",
      ),
    ).toBe("stale-token");

    expect(
      retryRequestHeaders.get(
        "X-CSRFToken",
      ),
    ).toBe("fresh-token");

    expect(
      fetchMock.mock.calls[1]?.[1]
        ?.method,
    ).toBe("GET");
  });

  it("does not retry more than once", async () => {
    setCsrfCookie("stale-token");

    const fetchMock = vi.mocked(
      globalThis.fetch,
    );

    fetchMock.mockResolvedValueOnce(
      jsonResponse(
        {
          detail:
            "CSRF verification failed.",
        },
        403,
      ),
    );

    fetchMock.mockImplementationOnce(
      async () => {
        setCsrfCookie("fresh-token");

        return jsonResponse({
          detail: "CSRF cookie set.",
        });
      },
    );

    fetchMock.mockResolvedValueOnce(
      jsonResponse(
        {
          detail:
            "CSRF verification failed again.",
        },
        403,
      ),
    );

    await expect(
      apiRequest(
        "/api/test-resource/",
        {
          method: "POST",
          json: {
            name: "demo",
          },
        },
      ),
    ).rejects.toMatchObject({
      status: 403,
    });

    expect(
      fetchMock,
    ).toHaveBeenCalledTimes(3);
  });

  it("does not retry a genuine authorization failure", async () => {
    const fetchMock = vi.mocked(
      globalThis.fetch,
    );

    fetchMock.mockResolvedValueOnce(
      jsonResponse(
        {
          detail:
            "You do not have permission to perform this action.",
        },
        403,
      ),
    );

    await expect(
      apiRequest(
        "/api/test-resource/",
        {
          method: "POST",
          json: {
            name: "demo",
          },
        },
      ),
    ).rejects.toBeInstanceOf(
      ApiError,
    );

    expect(
      fetchMock,
    ).toHaveBeenCalledTimes(1);
  });

  it("does not retry safe requests", async () => {
    const fetchMock = vi.mocked(
      globalThis.fetch,
    );

    fetchMock.mockResolvedValueOnce(
      jsonResponse(
        {
          detail:
            "CSRF verification failed.",
        },
        403,
      ),
    );

    await expect(
      apiRequest(
        "/api/test-resource/",
        {
          method: "GET",
        },
      ),
    ).rejects.toBeInstanceOf(
      ApiError,
    );

    expect(
      fetchMock,
    ).toHaveBeenCalledTimes(1);
  });
});

beforeEach(() => {
  clearCsrfCookie();

  vi.stubGlobal(
    "fetch",
    vi.fn(),
  );
});

afterEach(() => {
  clearCsrfCookie();

  vi.unstubAllGlobals();
});
