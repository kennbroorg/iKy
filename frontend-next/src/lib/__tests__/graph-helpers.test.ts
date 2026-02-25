import { describe, expect, it } from "vitest";

import {
  gatherToGraph,
  type GatherItem,
} from "@/components/gatherer/renderers/graph-helpers";

describe("gatherToGraph", () => {
  it("converts a 3-node gather with one hub into nodes and links", () => {
    const gather: GatherItem[] = [
      {
        "name-node": "github-hub",
        title: "GitHub",
        subtitle: "",
        link: "GitHub",
        icon: "fab fa-github",
      },
      {
        "name-node": "github-repos",
        title: "Repos",
        subtitle: 42,
        link: "GitHub",
        icon: "fas fa-code",
      },
      {
        "name-node": "github-followers",
        title: "Followers",
        subtitle: 100,
        link: "GitHub",
        icon: "fas fa-users",
      },
    ];

    const result = gatherToGraph(gather);

    expect(result.nodes).toHaveLength(3);
    expect(result.links).toHaveLength(2);

    // Hub node
    const hub = result.nodes.find((n) => n.id === "github-hub");
    expect(hub).toBeDefined();
    expect(hub!.label).toBe("GitHub");
    expect(hub!.group).toBe("primary");

    // Non-hub nodes
    const repos = result.nodes.find((n) => n.id === "github-repos");
    expect(repos).toBeDefined();
    expect(repos!.label).toBe("Repos: 42");
    expect(repos!.group).toBe("GitHub");

    const followers = result.nodes.find((n) => n.id === "github-followers");
    expect(followers).toBeDefined();
    expect(followers!.label).toBe("Followers: 100");
    expect(followers!.group).toBe("GitHub");

    // Links point from hub to leaf nodes
    expect(result.links).toContainEqual({
      source: "github-hub",
      target: "github-repos",
    });
    expect(result.links).toContainEqual({
      source: "github-hub",
      target: "github-followers",
    });
  });

  it("maps picture field to img on nodes", () => {
    const gather: GatherItem[] = [
      {
        "name-node": "user-hub",
        title: "User",
        subtitle: "",
        link: "User",
        picture: "https://example.com/avatar.jpg",
      },
      {
        "name-node": "user-detail",
        title: "Detail",
        subtitle: "value",
        link: "User",
        picture: "https://example.com/detail.png",
      },
    ];

    const result = gatherToGraph(gather);

    const hub = result.nodes.find((n) => n.id === "user-hub");
    expect(hub!.img).toBe("https://example.com/avatar.jpg");

    const detail = result.nodes.find((n) => n.id === "user-detail");
    expect(detail!.img).toBe("https://example.com/detail.png");
  });

  it("returns empty arrays for empty input", () => {
    expect(gatherToGraph([])).toEqual({ nodes: [], links: [] });
  });

  it("returns empty arrays for undefined-like input", () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    expect(gatherToGraph(undefined as any)).toEqual({ nodes: [], links: [] });
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    expect(gatherToGraph(null as any)).toEqual({ nodes: [], links: [] });
  });

  it("does not add img when picture is absent", () => {
    const gather: GatherItem[] = [
      {
        "name-node": "solo-hub",
        title: "Solo",
        subtitle: "",
        link: "Solo",
      },
    ];

    const result = gatherToGraph(gather);
    expect(result.nodes[0].img).toBeUndefined();
  });
});
