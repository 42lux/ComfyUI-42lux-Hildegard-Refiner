# Texture-tier upscale prompt — Flux2 Klein

A single-paragraph, surface-level prompt for the RFNTILE upscaler. It refines
whatever textures a tile contains without naming a focal subject or per-element
guards. This is the working default for high-resolution, many-tile passes.

---

## When to use it

The choice between the three tiers tracks **tile resolution and tile count**,
not image complexity:

- **Texture tier (this document)** — high-resolution images cut into **many
  tiles** where each tile still contains recognisable material regions. A
  flat texture survey fits a tile that's a clean crop of one or two surfaces.
- **Full per-image build** — lower-resolution images with **few tiles**. Each
  tile holds most of the subject, so focal-subject framing and per-element
  guards have something to bind to. See `full_build_upscale_prompt.md`.
- **Subject-less generic** — very high-res passes where most tiles are
  context-free, dense-repeated subjects (flocks, crowds, sticker fields), or
  images with large empty/negative-space regions. Naming any subject risks
  hallucinating it into tiles that don't contain it. See
  `subject_less_upscale_prompt.md`.

Edge notes:

- When a few-tile pass contains a genuinely hard material in one tile —
  fine lace, dense ornament, layered translucent plastic, a patterned
  garment — prefer the **full build** for that pass.
- When a high-res pass will produce many context-free tiles (very small
  tiles, dense repeated subjects, or large empty regions), prefer the
  **subject-less generic** prompt.

---

## The prompt

The trigger phrase is fixed and immutable — it begins every prompt verbatim.
The texture survey in the middle is the only part that changes per image.

> RFNTILE. refine and add detail to this upscaled tile. Restore the image quality and resolve it to a sharp, high-resolution result. Remove compression artifacts, banding, and noise, and clarify soft or blurred areas into crisp, clean edges and definition. Enrich existing textures and surfaces with fine, intricate, physically accurate detail — {TEXTURE SURVEY} — recovering realistic, lifelike micro-detail only where detail is present in the source, matching the existing grain, focus, and material properties of each surface. Keep in-focus subjects crisp and sharp, and keep softly blurred or out-of-focus areas soft, holding their existing depth of field. Preserve the original lighting, colour, contrast, and composition exactly as shown, leaving evenly-toned areas clean and untouched. Produce a clean, photorealistic result faithful to the source.

Everything except `{TEXTURE SURVEY}` is fixed. Do not reword the trigger, the
clean-up clause, the depth-of-field clause, the negative-space clause, or the
closing line.

---

## Building the texture survey

`{TEXTURE SURVEY}` is a comma-separated list of every significant texture in the
frame. It is a list of nouns with short descriptors — never guards, never
sub-clauses. The moment an entry grows a guard ("...keeping it faithful and...")
it has drifted into the full build.

Four rules for the list:

1. **Survey the whole frame, not just the subject.** In a many-tile pass the
   subject may occupy only a minority of tiles. Name the environment textures
   too — ground, walls, foliage, sky, background objects — weighted by how much
   tile area each covers. A tile landing on background needs a matching anchor
   in the prompt.
2. **Describe the observed surface, not a default.** Especially skin: it is
   matte in normal portrait lighting, but genuinely glossy under macro, sweat,
   oil, or strong directional light. Write "natural matte skin with pore-level
   texture" or "skin with pore-level texture and its natural sheen" to match
   what the image actually shows. The same applies to any surface — name its
   real finish.
3. **Name material families, not one generic texture.** Glossy paint, matte
   velvet, coarse linen, polished metal, rough stone each behave differently;
   the "matching material properties" clause only works if the surfaces are
   named distinctly.
4. **Separate distinct fine-detail systems.** If two fine textures meet — hair
   against feathers, fur against fabric — name them separately so the model
   holds the boundary instead of blending them.

---

## Texture descriptors

Reusable phrasings for common surfaces. Pick what is in the frame.

| Surface | Descriptor |
|---------|-----------|
| Skin (normal light) | natural matte skin with pore-level texture |
| Skin (macro/sweat/oil/strong light) | skin with pore-level texture and its natural sheen |
| Lips | the soft sheen of the lips |
| Eyes | detailed eyes with iris fibres |
| Eyelashes / brows | fine individual eyelashes and eyebrow hairs |
| Hair | fine individual hair strands with flyaways |
| Curly hair | dense curly hair with fine individual coils |
| Animal fur | fine individual fur with natural directional flow |
| Feathers | soft layered feathers with their barbs and downy texture |
| Polished metal | polished reflective metal with specular highlights and reflections |
| Gold / filigree | engraved gold filework with its set stones |
| Glossy paint | glossy paint with specular highlights and reflections |
| Glass | clear glass with refraction and highlights |
| Glossy plastic | glossy translucent plastic with creases, folds, and highlights |
| Matte plastic / rubber | even matte moulded surface |
| Silk / satin | glossy patterned fabric with its print and folds |
| Velvet | soft matte velvet with directional nap |
| Knit / linen / coarse fabric | coarse woven fabric texture |
| Lace | fine openwork lace pattern with mesh ground |
| Beadwork / sequins | dense beaded surface, each bead a point of light |
| Stone / rock | rough textured stone surface |
| Wood | wood-grain texture |
| Foliage / ground | leaves, bark, gravel, soil, each its own texture |
| Water surface | rippled water with reflections |
| Flame / glow | bright flame with its glow |
| Printed graphics / stickers | printed artwork and lettering (see Limitations) |

---

## The fixed clauses — what they do

- **"enrich existing textures... only where detail is present"** — refine what
  is there; do not invent detail in surfaces that have none.
- **"matching the existing grain, focus, and material properties"** — refine
  each surface in character; do not apply one uniform sharpening pass.
- **depth-of-field clause** — keep intentionally soft/blurred areas soft; do
  not sharpen an out-of-focus background and flatten the depth.
- **negative-space clause** — leave large dark or evenly-toned empty regions
  clean and smooth; do not hallucinate grain, ripples, or murk into the void.
  Essential for images with large empty backgrounds.
- **scope lock** ("preserve the original lighting, colour, contrast, and
  composition") — change resolution and detail only, never content or look.

---

## Writing rules

1. **Positive framing.** Describe the desired surface, never the failure to
   avoid. The texture survey is all positive description by nature; keep it so.
2. **No transformation verbs.** Restore, resolve, recover, enrich, clarify,
   preserve — never "improve", "enhance the colour", "make it better", "fix".
3. **List, not prose.** The survey stays a comma-separated list of nouns with
   short descriptors. No guards, no clauses — that is the line between this and
   the full build.
4. **Observed surface over default.** Match the skin (and every surface) to
   what the image shows, not to a fixed assumption.

---

## Known limitations

No prompt clears these — the texture tier included:

- **Dense small repeated elements** (crowds, sticker fields, fine ornament) —
  the model cannot resolve many tiny elements correctly; it mushes or
  hallucinates them. Many-tile passes help (fewer elements per tile) but do not
  fully solve it.
- **Text and fine printed graphics** — treated as texture and often re-rendered
  or garbled. For must-be-legible text or critical graphics, composite a clean
  layer in post rather than relying on the upscale.
- **Layered translucent materials in a single tile** — skin through plastic,
  glass over content — better served by the full build's transparency guards.

---

## Worked example

**Image:** blonde winged figure in polished steel armour, supermarket aisle.

> RFNTILE. refine and add detail to this upscaled tile. Restore the image
> quality and resolve it to a sharp, high-resolution result. Remove compression
> artifacts, banding, and noise, and clarify soft or blurred areas into crisp,
> clean edges and definition. Enrich existing textures and surfaces with fine,
> intricate, physically accurate detail — natural matte skin with pore-level
> texture; the soft sheen of the lips; detailed eyes with iris fibres and fine
> eyelashes; fine individual blonde hair strands with windblown flyaways; the
> polished reflective steel armour with its specular highlights, mirror
> reflections, rivets, and plate seams; the soft white feathered wings with
> their layered barbs and downy texture; the bright glowing halo ring; and the
> softly blurred grocery shelves, produce, and warm bokeh lights of the
> background — recovering realistic, lifelike micro-detail only where detail is
> present in the source, matching the existing grain, focus, and material
> properties of each surface. Keep in-focus subjects crisp and sharp, and keep
> softly blurred or out-of-focus areas soft, holding their existing depth of
> field. Preserve the original lighting, colour, contrast, and composition
> exactly as shown, leaving evenly-toned areas clean and untouched. Produce a
> clean, photorealistic result faithful to the source.

---

## Checklist

- [ ] Opens with the full trigger phrase verbatim
- [ ] Texture survey covers the whole frame, environment included
- [ ] Each surface named with its real, observed finish (matte vs sheen)
- [ ] Distinct material families named separately
- [ ] Survey is a noun list — no guards, no sub-clauses
- [ ] All fixed clauses present and unreworded
- [ ] Image suits the texture tier (high-res, many-tile) — not a few-tile pass
      with a hard material, and not a pass with mostly context-free tiles

---

## See also

- `full_build_upscale_prompt.md` — block-based per-image build for low-res
  few-tile passes.
- `subject_less_upscale_prompt.md` — subject-less generic for context-free
  tiles, dense-repeated subjects, or large empty regions.
