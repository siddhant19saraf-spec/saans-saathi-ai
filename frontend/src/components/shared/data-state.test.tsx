import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { DataState } from "./data-state";

describe("DataState", () => {
  it("announces loading without rendering placeholder values", () => {
    render(<DataState state={{ status: "loading" }}>{() => <p>Loaded content</p>}</DataState>);
    expect(screen.getByText("Loading data")).toBeInTheDocument();
    expect(screen.queryByText("Loaded content")).not.toBeInTheDocument();
    expect(document.querySelector("[aria-busy='true']")).not.toBeNull();
  });

  it("labels an unavailable service and offers retry", async () => {
    const user = userEvent.setup();
    const retry = vi.fn();
    render(
      <DataState
        state={{
          status: "unavailable",
          message: "This data service is not available in this build.",
          code: "NOT_FOUND",
        }}
        retry={retry}
        unavailableTitle="Air quality service not connected"
      >
        {() => <p>Loaded content</p>}
      </DataState>,
    );

    expect(screen.getByText("Air quality service not connected")).toBeInTheDocument();
    expect(
      screen.getByText("This data service is not available in this build."),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /retry/i }));
    expect(retry).toHaveBeenCalledTimes(1);
  });

  it("renders an error alert for genuine failures", () => {
    render(
      <DataState state={{ status: "error", message: "Bad response", code: "UNEXPECTED_ERROR" }}>
        {() => <p>Loaded content</p>}
      </DataState>,
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Something went wrong");
    expect(screen.queryByText("Loaded content")).not.toBeInTheDocument();
  });

  it("renders children only on success", () => {
    render(
      <DataState state={{ status: "success", data: { value: 42 } }}>
        {(data) => <p>Value {data.value}</p>}
      </DataState>,
    );
    expect(screen.getByText("Value 42")).toBeInTheDocument();
  });
});
