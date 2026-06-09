import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SurpriseButton } from "./SurpriseButton";
import { api } from "../api";

vi.mock("../api", () => ({
  api: { sample: vi.fn() },
}));

describe("SurpriseButton", () => {
  it("fetches a random paragraph and passes its text to onPick", async () => {
    vi.mocked(api.sample).mockResolvedValue({
      id: 42,
      text: "Volcanoes form where tectonic plates meet.",
    });
    const onPick = vi.fn();
    const user = userEvent.setup();

    render(<SurpriseButton onPick={onPick} />);
    await user.click(screen.getByRole("button", { name: /surprise me/i }));

    await waitFor(() =>
      expect(onPick).toHaveBeenCalledWith(
        "Volcanoes form where tectonic plates meet.",
      ),
    );
  });
});
