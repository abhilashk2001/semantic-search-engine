import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { BenchmarkChart } from "./BenchmarkChart";

vi.mock("../api", () => ({
  api: { benchmark: vi.fn().mockResolvedValue({ recall_at_k: 0.99 }) },
}));

describe("BenchmarkChart", () => {
  it("renders the heading and live-recall button from static results", () => {
    render(<BenchmarkChart />);
    expect(screen.getByText("RECALL vs LATENCY")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /run live recall check/i }),
    ).toBeInTheDocument();
    // Static dataset metadata is rendered (10,000 vectors).
    expect(screen.getByText(/10,000 vectors/)).toBeInTheDocument();
  });
});
