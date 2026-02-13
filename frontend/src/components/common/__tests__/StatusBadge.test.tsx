import { describe, it, expect } from "vitest";
import { render, screen } from "@/test/test-utils";
import { StatusBadge } from "../StatusBadge";
import type { AttendanceStatus } from "@/types";

describe("StatusBadge", () => {
  const statuses: AttendanceStatus[] = [
    "PRESENT",
    "ABSENT",
    "LATE",
    "EARLY_DEPARTURE",
    "HALF_DAY",
    "ON_LEAVE",
  ];

  it.each(statuses)("renders badge for status %s", (status) => {
    render(<StatusBadge status={status} />);
    // The badge should render some text (the translated status label)
    const badge = screen.getByText(/./);
    expect(badge).toBeInTheDocument();
    expect(badge.tagName).toBe("SPAN");
    expect(badge.className).toContain("badge");
  });

  it("renders 'Present' text for PRESENT status", () => {
    render(<StatusBadge status="PRESENT" />);
    expect(screen.getByText("Present")).toBeInTheDocument();
  });

  it("renders 'Absent' text for ABSENT status", () => {
    render(<StatusBadge status="ABSENT" />);
    expect(screen.getByText("Absent")).toBeInTheDocument();
  });

  it("renders 'Late' text for LATE status", () => {
    render(<StatusBadge status="LATE" />);
    expect(screen.getByText("Late")).toBeInTheDocument();
  });
});
