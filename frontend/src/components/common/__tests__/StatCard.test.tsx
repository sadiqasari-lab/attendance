import { describe, it, expect } from "vitest";
import { render, screen } from "@/test/test-utils";
import { StatCard } from "../StatCard";

describe("StatCard", () => {
  it("renders title and value", () => {
    render(
      <StatCard title="Total Employees" value={42} icon={<span>icon</span>} />
    );
    expect(screen.getByText("Total Employees")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
  });

  it("renders the icon", () => {
    render(
      <StatCard
        title="Active"
        value={10}
        icon={<span data-testid="test-icon">I</span>}
      />
    );
    expect(screen.getByTestId("test-icon")).toBeInTheDocument();
  });

  it("shows change text when provided", () => {
    render(
      <StatCard
        title="Revenue"
        value="$1,000"
        icon={<span>$</span>}
        change="+12% from last month"
      />
    );
    expect(screen.getByText("+12% from last month")).toBeInTheDocument();
  });

  it("does not render change text when not provided", () => {
    const { container } = render(
      <StatCard title="Count" value={5} icon={<span>C</span>} />
    );
    const changeElements = container.querySelectorAll(".text-xs");
    expect(changeElements).toHaveLength(0);
  });

  it("applies custom className", () => {
    const { container } = render(
      <StatCard
        title="Test"
        value={1}
        icon={<span>T</span>}
        className="my-custom-class"
      />
    );
    expect(container.firstChild).toHaveClass("my-custom-class");
  });
});
