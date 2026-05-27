# LLM prompt templates

Three sister prompts for the `RFNTILE` trigger. Each is calibrated for a
different tile-count regime — pick the one that matches the pass you're
about to run, not the prompt that sounds the most descriptive.

| Template | When to use | Per-tile content |
|---|---|---|
| [`full_build_upscale_prompt.md`](full_build_upscale_prompt.md) | Source ≲ 2K–3K, **few tiles** (under ~6) | Each tile holds most of the subject |
| [`texture_upscale_prompt.md`](texture_upscale_prompt.md) | Higher-res source, **many tiles**, each a surface crop | Recognisable material regions per tile |
| [`subject_less_upscale_prompt.md`](subject_less_upscale_prompt.md) | Very-high-res / dense-repeat / large empty regions | Many tiles are context-free crops |

## The decision rule

The right tier depends on **how much of the subject any one tile holds**,
which falls out of the upscaled result size and the picked tile dimensions:

- **Result ≲ 4 K with 1024–1536 px tiles** → grid is 1×1 to 3×2-ish, each
  tile contains most of the subject → **full build**. Name materials, fragile
  elements, lighting; the per-element guards have something to bind to.
- **Result 4 K–8 K with same tile size** → 4×3 to 6×4 grid, most tiles
  contain one or two surfaces → **texture tier**. List surface families;
  drop the per-element guards.
- **Result 8 K+ or dense-repeat / empty-region images** → many tiles will
  be context-free crops or pure background → **subject-less generic**.
  Drop named subjects entirely; rely on the anti-hallucination clause.

Heuristic: more ambitious prompts (named subjects, per-element guards) are
*helpful* when tiles can see the subject. They become *liabilities* when
tiles can't — naming "the cat" while sampling a tile of pure sky can
hallucinate cat fragments into the sky.

If you're in doubt between two tiers, prefer the **less specific** one. A
texture survey on a few-tile pass leaves some detail on the table but
won't drift; a full build on a many-tile pass can.

## Trigger

All three templates open with the same fixed `RFNTILE.` trigger phrase. Do
not reword it — that's the LoRA's training signal. The rest of each prompt
varies in structure (block-based vs single-paragraph) and in what slots
need filling per image.
