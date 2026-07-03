---
name: visual-handoff
description: Renders a handoff's state as reproducible text-sourced diagrams (Mermaid flowcharts, sequence or state UML, dependency graphs). Use when the person explicitly asks for visualization of a handoff, plan, or system state; never self-invoked.
---

# Visual Handoff

Visual handoff converts the state a handoff must make inspectable into a diagram, so a human can detect anomalies without reading through prose. It serves contributors who prefer the visual modality (the V in VARK) — but only when they ask. The design constraints come from primary learning research; see [the evidence base](references/evidence.md).

**UTILITY SKILL:** invoked as `clairvoyance:visual-handoff` by `using-clairvoyance` only when the person explicitly requests visualization (a diagram, chart, UML, graph, or "show me visually"). It augments whichever handoff skill is routed; it never replaces one.

## Opt-in contract

- **Never push a diagram.** Preference is self-identified by the person in the moment (Fleming & Mills 1992); an unrequested diagram is decoration, not a handoff.
- **Never diagnose or store a "learning style".** There is no adequate evidence base for style assessment (Pashler et al. 2008). Honor the explicit request; infer nothing about the person, and persist no style label across sessions.
- **Complement, never replace.** Words plus pictures beat pictures alone as much as words alone (Mayer's multimedia principle). The routed skill's prose headings stay; the diagram is added evidence.

## Steps

1. Confirm the request is explicit. No request, no diagram — continue the routed handoff unchanged.
2. Identify the information structure — flow, interaction, state, dependency, hierarchy, timeline, or proportion — and pick the matching notation from [the notation guide](references/notation.md).
3. If the content has no structure a plane can exploit (no grouping-by-location for the eye to use), say so and keep prose or a table — a diagram is only *sometimes* worth ten thousand words (Larkin & Simon 1987).
4. Build the smallest diagram that carries one message: drop extraneous nodes and decoration, label marks in place, and highlight the anomaly or decision point the human must see (Mayer's coherence, contiguity, and signaling principles).
5. Emit it as a fenced text-to-diagram source block — Mermaid first (GitHub renders it natively); PlantUML or Graphviz DOT only when Mermaid cannot express the structure. Never hand over a rendered image without its source: the text source is what makes the visual reproducible, diffable, and re-renderable.
6. Insert it as a **Diagram** section inside the routed skill's output, next to the evidence it visualizes, and state in one line what the diagram shows and where to look.

## Output

The routed handoff's headings, plus:

- **Diagram:** a fenced ` ```mermaid ` (or PlantUML/DOT) source block — one message per diagram, anomaly or decision point signaled.
- **Reading:** one or two lines naming what the diagram shows and where the eye should land.

## References

Load only what the task needs:

- [Evidence base](references/evidence.md) — the primary sources behind the opt-in, no-diagnosis, and complement rules.
- [Notation guide](references/notation.md) — structure-to-notation table, Mermaid conventions, reproducibility rules.
- [Worked example](references/example.md) — a full visual handoff.
