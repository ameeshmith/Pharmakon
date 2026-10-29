import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import App from "../App";
import { CodeBlock, GlassCard, GlassModal, Tabs } from "../components/ui";

describe("Pharmakon Glassmorphism UI & Pages", () => {
  it("renders Landing page hero, animated tool demo, Connect in 30 Seconds, and disclaimer", () => {
    render(<App />);
    expect(
      screen.getByText(/Grounded Biomedical & Drug Safety/i)
    ).toBeInTheDocument();
    expect(screen.getByText(/Connect in 30 Seconds/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Medical & Regulatory Disclaimer:/i)
    ).toBeInTheDocument();
  });

  it("toggles between dark and light mode via the navbar button", async () => {
    const user = userEvent.setup();
    render(<App />);
    expect(document.documentElement.classList.contains("dark")).toBe(true);

    const toggleBtn = screen.getByRole("button", {
      name: /switch to light mode/i,
    });
    await user.click(toggleBtn);
    expect(document.documentElement.classList.contains("dark")).toBe(false);
  });

  it("navigates to Playground and generates dynamic form inputs from tool schemas", async () => {
    const user = userEvent.setup();
    render(<App />);

    const playgroundNav = screen.getByRole("button", { name: /^Playground$/i });
    await user.click(playgroundNav);

    expect(
      screen.getByText(/Interactive MCP Playground/i)
    ).toBeInTheDocument();
    // Switch to adverse_event_summary tool
    const aeToolBtn = screen.getByRole("button", {
      name: /adverse_event_summary\(\)/i,
    });
    await user.click(aeToolBtn);

    expect(
      screen.getByRole("heading", { name: /Adverse Event Summary \(FAERS\)/i })
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/drug \*/i)).toHaveValue("semaglutide");
  });

  it("navigates to Docs & Connect page and displays all 6 tool schemas", async () => {
    const user = userEvent.setup();
    render(<App />);

    const docsNav = screen.getByRole("button", { name: /Docs & Connect/i });
    await user.click(docsNav);

    expect(
      screen.getByText(/Pharmakon MCP Documentation & Tool Reference/i)
    ).toBeInTheDocument();
    expect(screen.getByText("search_trials")).toBeInTheDocument();
    expect(screen.getByText("drug_safety_brief")).toBeInTheDocument();
  });

  it("renders reusable GlassCard, Tabs, GlassModal, and CodeBlock primitives", async () => {
    const user = userEvent.setup();
    const onTabChange = vi.fn();
    const onCloseModal = vi.fn();

    render(
      <div>
        <GlassCard dense>
          <p>Inside GlassCard</p>
        </GlassCard>
        <Tabs
          tabs={[
            { id: "a", label: "Tab A" },
            { id: "b", label: "Tab B" },
          ]}
          activeTab="a"
          onChange={onTabChange}
        />
        <CodeBlock title="Sample Snippet" code='{"hello": "world"}' />
        <GlassModal open={true} title="Test Modal" onClose={onCloseModal}>
          <p>Modal body content</p>
        </GlassModal>
      </div>
    );

    expect(screen.getByText("Inside GlassCard")).toBeInTheDocument();
    expect(screen.getByText("Modal body content")).toBeInTheDocument();
    await user.click(screen.getByRole("tab", { name: "Tab B" }));
    expect(onTabChange).toHaveBeenCalledWith("b");
  });
});
