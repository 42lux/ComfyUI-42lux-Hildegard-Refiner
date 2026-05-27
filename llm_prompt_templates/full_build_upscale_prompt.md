# Full per-image build upscale prompt — Flux2 Klein

A block-based, per-element prompt for the RFNTILE upscaler. Names the focal
subject, the materials present, and the fragile elements individually, each
with its own positive guard. This is the working tool for low-resolution,
few-tile passes where each tile holds the whole subject or scene.

---

## When to use it

The choice between the three tiers tracks **tile resolution and tile count**,
not image complexity:

- **Full per-image build (this document)** — low-resolution images with **few
  tiles**. Each tile holds most of the subject, so focal-subject framing and
  per-element guards have something to bind to. Also the right call for any
  pass where one tile contains a genuinely hard material (fine lace, dense
  ornament, layered translucent plastic, a patterned garment) — the named
  guards rescue what generic descriptions miss.
- **Texture tier** — high-resolution, many-tile passes where each tile is a
  surface crop. See `texture_upscale_prompt.md`.
- **Subject-less generic** — very high-res passes where most tiles are
  context-free, or images with dense repeated subjects / large empty regions.
  See `subject_less_upscale_prompt.md`.

---

## Skeleton

Assemble in this order. Fixed blocks are verbatim; semi-fixed take a small
slot; variable blocks are per-image.

| # | Block | Type | Include when |
|---|-------|------|--------------|
| 0 | Reference handling | Fixed* | Always — *single-reference uses the short form |
| 1 | Master framing | Fixed | Always |
| 2 | Focal subject — person / object / scene | Semi-fixed | Always — pick the matching mode |
| 3 | Hair | Semi-fixed | Person mode, visible hair |
| 4 | Special materials | Variable | Always — core slot |
| 5 | Fine-detail elements | Variable | Always |
| 6 | Environment / background | Variable | There is a background |
| 7 | Lighting & grade preservation | Semi-fixed | Always |
| 8 | Source clean-up | Fixed | Always |
| 9 | Scope lock | Fixed | Always |
| 10 | Style / Mood tag | Optional | Painterly/illustrated, or aesthetic drift |

Blocks 0 and 1 are written as one continuous opening; the trigger phrase
begins it.

---

## Block-by-block

### 0 + 1. Trigger, reference handling & master framing — FIXED

Every prompt opens with the full LoRA trigger phrase verbatim — never reword.

**Multi-reference pipeline** (tile passed alongside context slots):

> RFNTILE. refine and add detail to this upscaled tile. Image 1 is the tile to refine — resolve fine detail and crisp, clean edges across image 1 only, as a high-resolution delivery master of {SCENE}. Image 2 shows where this tile sits within the full frame; image 3 is the full source photo — draw on images 2 and 3 only for matching colour, lighting, and edge continuity, keeping all rendered content sourced from image 1.

**Single-reference pipeline** (only the tile is passed):

> RFNTILE. refine and add detail to this upscaled tile. Finish this image as a high-resolution delivery master. Resolve fine detail and crisp, clean edges throughout {SCENE}.

`{SCENE}` is a 1–3 word noun phrase: `this portrait`, `this image`, `this
fantasy scene`. With the multi-reference form, the scope lock (block 9) must
also pin to "image 1".

> **Pending validation:** the multi-reference slot order is assumed to be
> tile = image 1, position-map = image 2, full photo = image 3. Confirm
> against the pipeline before relying on it; if the order differs, update the
> image indices throughout.

### 2. Focal subject — SEMI-FIXED

Three modes. Pick one, or combine.

**Person mode** — a person or face is the subject.
**Object mode** — a product, vehicle, animal, creature, or hero object is the subject.
**Scene / no-hero mode** — a wide or dense scene with no single subject.

Modes can combine. An android with a porcelain body uses person mode for the
face and object mode for the body. A headless cropped figure (legs in a
product shot) uses object mode and carries only the person-mode skin clause.
When in doubt, derive a preset (see "Fallback" below) rather than force-fit.

#### Person mode — skin & eyes

Pick the skin variant that matches the observed surface. The skin clause
follows what the image actually shows, not a default — see writing rule 7.

**Young adult, normal portrait light:**
> Render the skin with a realistic matte finish and lifelike, pore-level texture — keep visible pores, fine skin detail, freckles, and natural soft highlights, so the skin reads as real, textured, and matte.

**Older subject:**
> Render the skin with a realistic matte finish and lifelike, pore-level texture — keep the wrinkles, crow's-feet, skin pigmentation, and full age character, so the face keeps its real, lived-in detail.

**Child:**
> Render the skin with a soft, natural matte finish appropriate to a young child — keep the skin smooth, soft, and lifelike with realistic fine detail.

**Macro / sweat / oil / strong directional light** (override the matte default):
> Render the skin with realistic pore-level texture and its natural sheen — keep the visible pores, fine skin detail, and the existing wet/oily highlights as part of the source.

**Non-human creature** (orc, monster, fantasy being):
> Render the {creature's} skin/hide with a realistic matte finish and weathered, pore-level texture — keep the deep wrinkles, coarse leathery surface, painted markings, scars, and blemishes, so the face keeps its real, lived-in character.

Then the eyes (all variants):
> Resolve the eyes with sharp, lifelike clarity — crisp irises, clean specular catchlights, and individual eyelashes.

#### Object mode — focal object

Give the focal object a priority sentence naming its primary surfaces, then
resolve key materials in detail.

> Resolve the {OBJECT} as the sharp focal subject — render {PRIMARY SURFACES} with crisp form, clean edges, and accurate detail true to the source.

Examples: *Vehicle* — "render the body panels, glass, headlights, grille, and
wheels..."; *Product* — "render its form, surface material, cap, and
label..."; *Animal* — "render the coat, eyes, nose, and facial detail with
crisp, lifelike clarity."

#### Scene / no-hero mode

For wide or crowd scenes with no dominant subject:

> Treat this as a layered scene with no single subject — resolve each depth layer at the clarity it already holds, recovering detail that is present rather than inventing new content.

For crowds or repeated figures: "each figure kept separate, holding only the
detail the source supports." See "Known limitations" — dense crowds have a
hard ceiling.

### 3. Hair — SEMI-FIXED — person mode only

> Resolve the hair as fine, individual strands{HAIR_DETAIL}, with soft, defined flyaways.

`{HAIR_DETAIL}` adds source notes: `, the defined curls`, `, the silver-grey
and dark hairs`, `, the windblown wisps`. Drop the block if hair is not visible.

### 4. Special materials — VARIABLE (core slot)

One sentence per high-risk material. Name the surface and its sub-features,
then add the positive guard (the desired state):

> On the {MATERIAL}, resolve {SUB-FEATURES} as crisp, well-defined detail, {GUARD}.

Pull phrasing from the vocabulary bank below. List materials foreground-first.

### 5. Fine-detail elements — VARIABLE

Small high-frequency elements — sparkles, particles, beadwork, light glints,
flyaway strands. One short positive clause each ("as clean, sharp points of
light", "each one separate with its own defined edge").

### 6. Environment / background — VARIABLE

> Keep the {BACKGROUND} naturally detailed within its existing {depth of field / atmospheric depth}, holding the {bokeh / haze / glints} as {smooth, soft, intact}.

Soft-gradient elements (sky, haze, aurora, cast shadows) are also named in
block 8.

### 7. Lighting & grade preservation — SEMI-FIXED

> Maintain the {LIGHTING} and the {GRADE} colour grade, with the existing contrast, white balance, framing, and depth of field exactly as shown.

Describe the lighting concretely — source, quality, direction, temperature
(`warm, soft directional interior light`, `dramatic low-key chiaroscuro`,
`hard direct on-camera flash`). `{GRADE}` is a short descriptor: `muted
desaturated`, `deep cosmic`, `warm sunlit`.

### 8. Source clean-up — FIXED

> Clean up degradation from the source: suppress compression artifacts, colour banding, and aliasing, and render smooth, even tonal gradients and clean, clear shadow detail.

Add `luminance noise` to the list for real photographs (camera sensor noise),
especially underexposed or flash-lit shots. For film-look images,
preserve the grain explicitly: "while preserving the natural film grain as
part of the look."

### 9. Scope lock — FIXED

> Keep the content, composition, framing, colours, and style identical to the source image — change only resolution, sharpness, and fine detail.

In the multi-reference form, pin to "identical to image 1" instead of "the
source image". Always the final sentence before the optional tag.

### 10. Style / Mood tag — OPTIONAL

> Style: {medium}. Mood: {existing mood}.

Use whenever the source is painterly/illustrated, or whenever the upscale
drifts. Example: `Style: digital concept art. Mood: cold, cinematic.`

---

## Material vocabulary bank

Sub-features and positive guards per material type.

| Material | Sub-features to name | Guard |
|----------|---------------------|-------|
| Polished metal | specular highlights, mirror reflections, scratches, rivets, hinges, seams | reflections accurate and true to the source |
| Aged / weathered metal | worn patina, cracked finish, tarnish, scratches | aged, weathered character intact |
| Translucent glass | refraction, internal caustics, surface highlights, content within | clean, clear, and fully transparent |
| Sheer fabric | layered weave, chiffon/tulle, beadwork, panel translucency | each layer crisp and individually defined |
| Lace / fine openwork fabric | floral lace pattern, mesh ground, scalloped edges, skin visible through the weave | pattern faithful to the source, skin visible through the open weave |
| Feathers | barbs, downy texture, flyaway strands | each barb a separate, cleanly defined strand |
| Short animal fur | individual hairs, directional flow, natural clumping | fine, distinct hairs with natural flow and clumping |
| Reptilian / scaled hide | overlapping scales, scale texture, edges | crisp, distinct overlapping scales |
| Antlers / bone | velvet and bone texture, tine tips | crisp surface texture with sharp tips |
| Carved stone | relief, scrollwork, patina, lichen | sharp, deep-cut geometric detail |
| Foliage / ground | moss, bark, growth rings, rock, soil | each surface its own distinct texture |
| Sparkles / particles | points of light | clean, sharp, well-defined points of light |
| Bokeh discs | smooth defocused circles | smooth discs, evenly filled, with soft edges |
| Lips | natural lip texture, soft sheen | natural texture with controlled, realistic sheen |
| Tattoos / body art | linework, shading, colour of the artwork | faithful to the source as drawn, not redrawn |
| Glitter makeup | sparkle points across the skin | clean, distinct points of light over matte skin |
| Painted nails | smooth nail surface, polish colour | clean, smooth, defined surfaces |
| Automotive paint | metallic flake, specular rolloff, panel reflections | reflections clean and true to the source |
| Glossy spheres / clustered objects | each object, single clean highlight | each object separate with its own defined edge |
| Printed text / labels | letterforms, layout, logo marks | reproduce the existing lettering exactly (see Limitations) |
| Matte plastic | moulded form, fine surface grain, panel seams | even matte surface with crisp moulded edges |
| Glossy plastic | smooth shell, highlights, moulded detail | clean even gloss with sharp moulded edges |
| Brushed / chrome metal | brushed grain or mirror finish, edge highlights | accurate finish true to the source |
| Rubber / tyres | moulded surface, tread pattern, sidewall texture | defined detail and even matte rubber surface |
| Liquid / fluid | surface highlights, translucency, meniscus, bubbles | clean, translucent, with crisp surface detail |
| Water surface / caustics | ripples, refraction, caustic light patterns | crisp, clean detail held as source content |
| Air bubbles | rounded bubble shapes, highlights | clean, well-defined rounded shapes |
| Screens / displays | pixels, UI elements, emitted glow | crisp display content with even emitted light |
| Paper / packaging | fibre texture, print, folds and creases, embossing | crisp print and clean material texture |
| Translucent / backlit organic | subsurface glow, veining, colour gradients | luminous translucency, smooth clean gradients |
| Regular tiled patterns | tile grid, straight edges, joints | clean, straight tile edges |
| Candle / small flame | flame shape, emitted glow | clean, even flames with soft, intact glow |
| Patterned silk / printed fabric | woven sheen, fabric folds, the print | pattern faithful to the source, weave intact |
| Velvet / matte fabric | directional nap, soft surface | soft matte nap, no false sheen |
| Lens distortion / optical aberration | barrel curvature, warped reflections, soft aberration | preserved exactly as in the source |

Note: matte as a *material description* (rubber, matte plastic, velvet) is
fine in block 4 — distinct from rule 7, which only restricts "matte" as an
anti-gloss instruction on glossy skin.

---

## Writing rules

1. **Positive framing, never negation.** State the desired result, not the
   failure to avoid. "without clumping" → "as separate, well-defined strands".
   "no waxy plastic skin" → "matte, lifelike skin with visible pores".
   "not cloudy" → "clean and clear". The one exception is block 8, where an
   active "suppress / clean up" verb is fine.
2. **Recovery verbs only.** Resolve, recover, preserve, sharpen, render,
   hold, maintain. Never "enhance", "improve", "make better", "fix" — these
   push the model off-source.
3. **Name specifics, not adjectives.** "Sharpen the rivets and plate seams"
   beats "make the armour more detailed."
4. **Describe lighting concretely** in block 7 — source, quality, direction,
   temperature. "Good lighting" is not enough.
5. **Soft-gradient elements are named twice** — once in block 6 to preserve
   their shape, once in block 8 to clean up banding in those same gradients.
6. **Specific detail helps, filler hurts.** Cut any clause that does not name
   something concrete in this image. If you see drift, trimmable filler
   usually lives in the environment and hair blocks.
7. **Observed surface, not default.** Matte skin is the right default for
   normal portrait light, but skin under macro, sweat, oil, or strong
   directional light is genuinely glossy — use the sheen variant. The same
   applies to every surface: describe what the image actually shows.
8. **Length matches image complexity.** Tight build for simple subjects,
   detailed build for genuinely multi-material images. Drift toward length
   for its own sake hurts; specific detail per material helps.

---

## Painterly / illustration variant

For painted, illustrated, or concept-art sources, adjust three things:

- **Block 1:** "...while preserving its painterly, concept-art rendering and
  brushwork..."
- **Block 2/skin:** drop "pore-level"; say "clear, well-rendered facial
  detail in keeping with the painted style."
- **Block 10:** always use the Style tag — `Style: oil painting.` /
  `Style: digital concept art.` — and name the style again in block 7.

---

## Fallback — deriving a preset on the fly

When an image matches no existing mode cleanly, derive a preset rather than
force-fit. The derived preset still obeys the full skeleton — only the
middle blocks (2, 4, 5) are improvised:

1. Classify the focal structure — single hero, layered scene, abstract,
   partial figure — and choose or combine modes accordingly.
2. List the fragile materials present.
3. Assign each a positive guard — reuse vocabulary-bank rows where they fit,
   coin new ones in the same sub-features-plus-guard form where they don't.
4. Assemble through blocks 0–10 as normal; all writing rules still bind.
5. Treat any coined material as a candidate row for the vocabulary bank.

Bias toward deriving on ambiguous images — a forced-fit preset is worse than
a derived one.

---

## Known limitations

No prompt fully solves these — the full build included:

- **Dense crowds / repeated small figures** — the model cannot resolve many
  tiny figures correctly; it mushes or hallucinates them. Scene mode's
  "recovering detail that is present rather than inventing" is the best
  available nudge, not a fix. In a high-res many-tile pass, prefer the
  subject-less tier.
- **Text and fine printed graphics** — treated as texture and often
  re-rendered or garbled. Quoting text in the prompt is the wrong tool — it
  invites re-typesetting. Use the preservation guard, and for must-be-legible
  text, composite a clean layer in post.
- **Tattoos / fine artwork on a surface** — same family as text; the design
  can be reinterpreted. The guard helps but does not guarantee fidelity.
- **Layered transparency in a single tile** (skin through plastic, glass over
  content) — handled here with named transparency guards, but it remains a
  hard case and worth verifying in the output.

---

## Worked example

**Person mode, multi-reference:** woman in polished plate armour with
feathered wings, supermarket aisle.

> RFNTILE. refine and add detail to this upscaled tile. Image 1 is the tile to refine — resolve fine detail and crisp, clean edges across image 1 only, as a high-resolution delivery master of this portrait. Image 2 shows where this tile sits within the full frame; image 3 is the full source photo — draw on images 2 and 3 only for matching colour, lighting, and edge continuity, keeping all rendered content sourced from image 1. Render the skin with a realistic matte finish and lifelike, pore-level texture — keep visible pores, fine skin detail, and natural soft highlights, so the skin reads as real, textured, and matte. Resolve the eyes with sharp, lifelike clarity — crisp irises, clean catchlights, and individual eyelashes. Resolve the hair as fine, individual strands with soft, defined flyaways. On the polished steel armour, resolve the specular highlights, mirror reflections, surface scratches, rivets, hinges, and plate seams as crisp, well-defined detail, with reflections accurate and true to the source. On the feathered wings, resolve individual barbs and downy texture so each barb reads as a separate, cleanly defined strand. Hold the glowing halo as a smooth, even ring of light. Keep the background produce and shelving naturally detailed within the existing shallow depth of field, holding the soft bokeh as smooth, evenly filled discs. Maintain the warm, soft directional interior light and the existing colour grade, with the existing contrast, white balance, framing, and depth of field exactly as shown. Clean up degradation from the source: suppress compression artifacts, colour banding, and aliasing, and render smooth, even tonal gradients and clean, clear shadow detail. Keep the content, composition, framing, colours, and style identical to image 1 — change only resolution, sharpness, and fine detail.

---

## Checklist

- [ ] Opens with the full trigger phrase verbatim
- [ ] Reference form matches the pipeline (multi or single)
- [ ] Block 2 mode chosen — person / object / scene, or a justified combination
- [ ] Skin variant matches the *observed surface*, not a default
- [ ] Every high-risk material has a sentence with sub-features + a guard
- [ ] No "without X" / "no X" framing anywhere except block 8
- [ ] No transformation verbs (enhance / improve / fix / make better)
- [ ] Lighting in block 7 described concretely
- [ ] Soft-gradient elements named in both block 6 and block 8
- [ ] "Matte" used as an instruction only on skin (and only where appropriate)
- [ ] Scope lock is the final sentence; pinned to "image 1" in multi-reference
- [ ] Style/Mood tag added if the source is painterly or drift appears
- [ ] Image suits the full build (low-res, few-tile) — not a many-tile pass

---

## See also

- `texture_upscale_prompt.md` — texture tier for high-res many-tile passes.
- `subject_less_upscale_prompt.md` — subject-less generic for context-free
  tiles, dense-repeated subjects, or large empty regions.
