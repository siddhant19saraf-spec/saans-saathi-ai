import { render } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";

import { MOTION_STORAGE_KEY } from "@/lib/motion";

import { MotionPreference } from "./motion-preference";

describe("MotionPreference", () => {
  beforeEach(() => {
    window.localStorage.clear();
    delete document.documentElement.dataset.reduceMotion;
  });

  it("applies the stored preference on mount", () => {
    window.localStorage.setItem(MOTION_STORAGE_KEY, "true");
    render(<MotionPreference />);
    expect(document.documentElement.dataset.reduceMotion).toBe("true");
  });

  it("reacts to storage events for the motion key only", () => {
    render(<MotionPreference />);

    window.localStorage.setItem(MOTION_STORAGE_KEY, "true");
    window.dispatchEvent(
      new StorageEvent("storage", { key: MOTION_STORAGE_KEY, newValue: "true" }),
    );
    expect(document.documentElement.dataset.reduceMotion).toBe("true");

    window.localStorage.setItem(MOTION_STORAGE_KEY, "false");
    window.dispatchEvent(
      new StorageEvent("storage", { key: MOTION_STORAGE_KEY, newValue: "false" }),
    );
    expect(document.documentElement.dataset.reduceMotion).toBe("false");

    window.dispatchEvent(new StorageEvent("storage", { key: "unrelated", newValue: "true" }));
    expect(document.documentElement.dataset.reduceMotion).toBe("false");
  });

  it("reacts to the in-app motion preference event", () => {
    render(<MotionPreference />);

    window.dispatchEvent(new CustomEvent("saans:motion-preference", { detail: true }));
    expect(document.documentElement.dataset.reduceMotion).toBe("true");

    window.dispatchEvent(new CustomEvent("saans:motion-preference", { detail: false }));
    expect(document.documentElement.dataset.reduceMotion).toBe("false");
  });

  it("removes its listeners on unmount", () => {
    const { unmount } = render(<MotionPreference />);
    unmount();

    document.documentElement.dataset.reduceMotion = "unchanged";
    window.dispatchEvent(new CustomEvent("saans:motion-preference", { detail: true }));
    expect(document.documentElement.dataset.reduceMotion).toBe("unchanged");
  });

  it("renders no markup", () => {
    const { container } = render(<MotionPreference />);
    expect(container).toBeEmptyDOMElement();
  });
});
