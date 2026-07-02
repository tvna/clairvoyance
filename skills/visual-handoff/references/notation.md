# Notation guide

Pick the notation from the information's structure, not from habit. If no row
matches, the content probably has no structure a plane can exploit — decline to
diagram it (see the evidence reference, Larkin & Simon).

## Structure to notation

| Information structure | Question the eye answers | Mermaid notation |
|---|---|---|
| Flow / decision path | "What happens next, and where does it branch?" | `flowchart TD` (or `LR` for pipelines) |
| Interaction over time | "Who calls whom, in what order?" | `sequenceDiagram` |
| State and transitions | "What states exist and what moves between them?" | `stateDiagram-v2` |
| Dependency / impact | "What depends on what; what breaks if this changes?" | `flowchart` with edges, or `graph` |
| Hierarchy / composition | "What contains or owns what?" | `classDiagram` or nested `flowchart subgraph` |
| Timeline / schedule | "What overlaps and what blocks what?" | `gantt` |
| Entity relationships | "How are the records related?" | `erDiagram` |
| Proportion / comparison | "Which share dominates?" | `pie`, `xychart-beta` — or a plain table when exact values matter |

## Reproducibility rules

- **Mermaid first.** GitHub, GitLab, and most Markdown renderers render fenced
  ` ```mermaid ` blocks natively, so the handoff renders wherever it lands.
- **PlantUML or Graphviz DOT** only when Mermaid cannot express the structure
  (rich UML component/deployment diagrams, large auto-laid-out graphs). Still
  ship the text source in a fenced block; add a rendered image only as a
  supplement, never as the only artifact.
- **Source lives in the artifact.** The fenced source is the diagram of record:
  deterministic to re-render, diffable in review, editable by the next session.
- **No hand-drawn or generated raster images** for structural content — they
  cannot be reproduced from text and drift silently from the state they show.

## Construction checklist (Mayer's principles, applied)

- One message per diagram. Two messages means two diagrams — or one and prose.
- Include only nodes and edges the message needs (coherence). If a node does
  not change the reading, delete it.
- Label marks in place (spatial contiguity): name edges and nodes directly; do
  not push meaning into a legend the eye must round-trip to.
- Signal the point: mark the anomaly, bottleneck, or decision node — Mermaid
  `style`/`classDef` highlight, or a `%% note` — so the eye lands where the
  decision lives.
- Keep node text short; the surrounding **Reading** line carries the sentence.
- Direction follows reading order: time and causality flow top-down or
  left-right, consistently within one handoff.
