// Native Markdown headings and the server's section list share positional IDs.
export function lessonAnchors() {
  return (tree: {
    children: {
      type: string;
      depth?: number;
      data?: Record<string, unknown>;
    }[];
  }) => {
    let index = 0;
    for (const node of tree.children) {
      if (node.type === "heading" && node.depth === 2) {
        index++;
        node.data = {
          ...node.data,
          hProperties: { id: `lesson-section-${index}` },
        };
      }
    }
  };
}
