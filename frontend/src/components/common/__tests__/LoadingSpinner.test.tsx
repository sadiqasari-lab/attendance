import { describe, it, expect } from "vitest";
import { render } from "@/test/test-utils";
import { LoadingSpinner } from "../LoadingSpinner";

describe("LoadingSpinner", () => {
  it("renders the spinner element", () => {
    const { container } = render(<LoadingSpinner />);
    const spinner = container.querySelector(".animate-spin");
    expect(spinner).toBeInTheDocument();
  });

  it("applies custom className", () => {
    const { container } = render(<LoadingSpinner className="mt-8" />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.className).toContain("mt-8");
  });

  it("centers the spinner by default", () => {
    const { container } = render(<LoadingSpinner />);
    const wrapper = container.firstChild as HTMLElement;
    expect(wrapper.className).toContain("flex");
    expect(wrapper.className).toContain("items-center");
    expect(wrapper.className).toContain("justify-center");
  });
});
