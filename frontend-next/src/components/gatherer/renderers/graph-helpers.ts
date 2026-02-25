/**
 * Convert the iKy backend "gather" array format to ForceGraph nodes/links.
 *
 * Backend gather item shape:
 *   { "name-node": string, title: string, subtitle: string|number,
 *     icon?: string, link: string, picture?: string, help?: string }
 *
 * Hub nodes have `link === title` (self-referencing).
 * Non-hub nodes are connected to the hub whose title matches their `link`.
 */

export interface GraphNode {
  id: string;
  label: string;
  img?: string;
  group?: string;
}

export interface GraphLink {
  source: string;
  target: string;
}

export interface GatherItem {
  "name-node": string;
  title: string;
  subtitle: string | number;
  icon?: string;
  link: string;
  picture?: string;
  help?: string;
}

export function gatherToGraph(gather: GatherItem[]): {
  nodes: GraphNode[];
  links: GraphLink[];
} {
  if (!gather || gather.length === 0) {
    return { nodes: [], links: [] };
  }

  const nodes: GraphNode[] = [];
  const links: GraphLink[] = [];

  for (const item of gather) {
    const isHub = item.link === item.title;

    const node: GraphNode = {
      id: item["name-node"],
      label: isHub ? item.title : `${item.title}: ${item.subtitle}`,
      group: isHub ? "primary" : item.link,
    };

    if (item.picture) {
      node.img = item.picture;
    }

    nodes.push(node);

    // Non-hub nodes link back to their hub
    if (!isHub) {
      // Find the hub node whose title matches this item's link
      const hub = gather.find(
        (h) => h.title === item.link && h.link === h.title,
      );
      if (hub) {
        links.push({
          source: hub["name-node"],
          target: item["name-node"],
        });
      }
    }
  }

  return { nodes, links };
}
