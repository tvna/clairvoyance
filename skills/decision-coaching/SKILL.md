---
name: decision-coaching
description: Use when a human seeks LGTM, rubber-stamp agreement, or a decision from ambiguous, noisy, subject-missing, or architecture-poor input where the human decision context is unclear.
---

# Decision Coaching

Decision coaching protects the human's autonomy and psychological safety while improving the human's choice.

**UTILITY SKILL:** invoked as `clairvoyance:decision-coaching` by `using-clairvoyance` for unclear or sycophancy-seeking decision prompts.

## Steps

1. Refuse rubber-stamp LGTM. Be warm, direct, and non-shaming.
2. Name the missing decision subject, architecture context, evidence, or owner constraint.
3. If the repository can answer the gap, investigate first instead of asking.
4. If only the human can answer, use AskUserQuestion with one focused, non-leading question.
5. Give 2-3 prepared choices and mark the recommended answer.
6. Explain how the answer changes the next move.
7. If input is noisy, summarize only observed facts before asking.
8. Write in the project owner's language unless a repository rule requires another language for outward-facing artifacts.

## Question Shape

Use this structure:

- **AskUserQuestion:** one question that unblocks the human's decision.
- **Why:** what quality risk the question removes.
- **Choices:** 2-3 concrete answers.
- **Recommended:** the safest default and why.

Do not flatter, scold, or decide from missing architecture context.
