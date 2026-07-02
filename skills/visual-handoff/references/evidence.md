# Evidence base

The skill's rules are constraints derived from primary learning research, not
preferences of the skill author. Each source below is the primary publication;
the "constraint" line is what it forces on this skill's behaviour.

## VARK is a catalyst for reflection, not a diagnosis

Fleming, N. D., & Mills, C. (1992). *Not Another Inventory, Rather a Catalyst
for Reflection.* To Improve the Academy, 11, 137–155.
<https://onlinelibrary.wiley.com/doi/abs/10.1002/j.2334-4822.1992.tb00213.x>

The VARK modal-preference questionnaire was designed for learners to identify
their own sensory preferences and adjust their own behaviour — not for an
instructor (or an agent) to classify them and adapt silently.

**Constraint:** the skill fires only on the person's own explicit request. The
person owns the preference; the agent never assumes it.

## Style assessment has no adequate evidence base

Pashler, H., McDaniel, M., Rohrer, D., & Bjork, R. (2008). *Learning Styles:
Concepts and Evidence.* Psychological Science in the Public Interest, 9(3),
105–119. <https://journals.sagepub.com/doi/10.1111/j.1539-6053.2009.01038.x>

The review found that the "meshing hypothesis" — instruction is best delivered
in the format matching a learner's style — is essentially untested by the
required crossover-interaction designs, and concluded: "at present, there is no
adequate evidence base to justify incorporating learning-styles assessments
into general educational practice."

**Constraint:** never classify a person as a "visual learner", never store or
carry a style label across sessions, and never auto-adapt output on an inferred
style. An explicit in-the-moment request is honored as a preference, which
needs no meshing evidence.

## Words plus pictures beat words alone — for everyone

Mayer, R. E. (2001; 3rd ed. 2021). *Multimedia Learning.* Cambridge University
Press. <https://doi.org/10.1017/9781316941355> (multimedia, coherence,
signaling, and spatial-contiguity principles, grounded in Paivio's dual-coding
theory).

The multimedia principle — people learn better from words and pictures than
from words alone — holds across learners, so offering a diagram on request
needs no style theory at all. The construction principles bind how the diagram
is built: exclude extraneous material (coherence), highlight the essential
(signaling), and place labels next to the marks they describe (spatial
contiguity).

**Constraint:** the diagram complements the prose handoff instead of replacing
it, carries one message, is stripped of decoration, and is labeled in place
with the anomaly or decision point signaled.

## A diagram is only *sometimes* worth ten thousand words

Larkin, J. H., & Simon, H. A. (1987). *Why a Diagram is (Sometimes) Worth Ten
Thousand Words.* Cognitive Science, 11(1), 65–100.
<https://onlinelibrary.wiley.com/doi/10.1111/j.1551-6708.1987.tb00863.x>

Diagrammatic and sentential representations can be informationally equivalent
yet computationally different: a diagram wins when grouping information by
location lets perceptual inference replace expensive search. When the content
has no such 2D structure, the diagram adds cost, not insight.

**Constraint:** match notation to the information's structure, and decline to
diagram content that a plane cannot exploit — say why, and keep prose or a
table.

## Why text-sourced diagrams

Reproducibility is an engineering constraint layered on the above: a diagram
whose source is text (Mermaid, PlantUML, Graphviz DOT) renders
deterministically from the artifact itself, diffs in review, and re-renders
after edits — an image pasted without source does none of these. This is the
same source-of-truth discipline the repository applies to code.
