import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "./api";

describe("api client", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("POSTs the right payload to /search and returns parsed JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        results: [{ id: 1, text: "hi", score: 0.9 }],
        latency_ms: 2.1,
        k: 5,
        ef_search: 50,
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const resp = await api.search({ query: "music", k: 5, ef_search: 50 });

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/search$/);
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ query: "music", k: 5, ef_search: 50 });
    expect(resp.results[0].text).toBe("hi");
  });

  it("throws with the server detail on error responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        statusText: "Bad Request",
        json: async () => ({ detail: "Vector has dimension 3, expected 384." }),
      }),
    );
    await expect(api.search({ vector: [0, 0, 0] })).rejects.toThrow(/dimension 3/);
  });
});
