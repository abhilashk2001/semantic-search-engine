import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "./App";
import { api } from "./api";

vi.mock("./api", () => ({
  api: {
    baseUrl: "http://test",
    search: vi.fn(),
    sample: vi.fn(),
    stats: vi.fn(),
    benchmark: vi.fn(),
    health: vi.fn(),
  },
}));

const mockedSearch = vi.mocked(api.search);
const mockedStats = vi.mocked(api.stats);

beforeEach(() => {
  mockedStats.mockResolvedValue({
    node_count: 10000,
    layer_distribution: { "0": 10000, "1": 600 },
    build_time_ms: 23659,
    config: { M: 16, ef_construction: 200, metric: "cosine", dim: 384 },
  });
  mockedSearch.mockResolvedValue({
    results: [{ id: 7, text: "Volcanoes form at tectonic boundaries.", score: 0.71 }],
    latency_ms: 1.3,
    k: 10,
    ef_search: 50,
  });
});

afterEach(() => vi.clearAllMocks());

describe("App", () => {
  it("renders index stats from the API", async () => {
    render(<App />);
    // dim (384) and metric are unique to the stats panel.
    expect(await screen.findByText("384")).toBeInTheDocument();
    expect(screen.getByText("cosine")).toBeInTheDocument();
  });

  it("searches when the user types and renders results", async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.type(screen.getByLabelText("Search query"), "volcanoes");

    expect(
      await screen.findByText("Volcanoes form at tectonic boundaries."),
    ).toBeInTheDocument();
    await waitFor(() =>
      expect(mockedSearch).toHaveBeenCalledWith({
        query: "volcanoes",
        k: 10,
        ef_search: 50,
      }),
    );
    expect(screen.getByText(/found in 1.30 ms/)).toBeInTheDocument();
  });

  it("re-runs search when the ef_search slider changes", async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.type(screen.getByLabelText("Search query"), "stars");
    await screen.findByText("Volcanoes form at tectonic boundaries.");
    mockedSearch.mockClear();

    // jsdom doesn't drive range-slider keyboard input; set the value directly.
    fireEvent.change(screen.getByLabelText("ef_search"), {
      target: { value: "51" },
    });

    await waitFor(() =>
      expect(mockedSearch).toHaveBeenCalledWith(
        expect.objectContaining({ query: "stars", ef_search: 51 }),
      ),
    );
  });
});
