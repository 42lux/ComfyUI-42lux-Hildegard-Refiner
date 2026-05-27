# Subject-less generic upscale prompt — Flux2 Klein

A single-paragraph, fully generic prompt for the RFNTILE upscaler. Names no
subjects, no objects, no specific surfaces — only generic texture *types* that
*may* be present, plus an explicit anti-hallucination clause. This is the
working tool for passes where each tile is a context-free crop, where naming
anything specific risks the model inventing it.

---

## When to use it

The choice between the three tiers tracks **tile resolution and tile count**,
plus the *content* of likely tiles:

- **Subject-less generic (this document)** — use when most tiles will be
  context-free. Three triggers:
  1. **Very high-res, very small tiles** — each tile is a tiny crop with no
     coherent subject, and the texture survey's named nouns become misleading
     (a tile of pure sky doesn't contain "the car").
  2. **Dense repeated subjects** — flocks, crowds, sticker fields, tiled
     ornament. Naming "faces" or "sheep" risks the model duplicating them
     into adjacent tiles to match the pattern.
  3. **Large empty / negative-space regions** — images where a real fraction
     of tiles will be pure background. Naming the subject risks the model
     inserting fragments of subject into empty tiles.
- **Texture tier** — high-res many-tile passes with recognisable material
  regions. See `texture_upscale_prompt.md`.
- **Full per-image build** — low-res few-tile passes where each tile holds
  most of the subject. See `full_build_upscale_prompt.md`.

The honest tradeoff: this tier is **safer but weaker**. Naming textures gives
the model anchors that improve detail recovery; removing the names trades
some of that for hallucination resistance. Use this when hallucination is the
dominant risk; use the texture tier when targeted detail is.

---

## The prompt

The trigger phrase is fixed. The texture-family slot is the only part that
varies per image — and it never names a specific subject or object, only
material types that may appear.

> RFNTILE. refine and add detail to this upscaled tile. Restore the image quality and resolve it to a sharp, high-resolution result. Remove compression artifacts, banding, and noise, and clarify soft or blurred areas into crisp, clean edges and definition. Enrich the existing textures and surfaces already present in this tile with fine, intricate, physically accurate detail — refining whatever materials appear, sharpening fine texture, edges, and surface structure, and resolving {TEXTURE FAMILIES} wherever they occur. Recover realistic, lifelike micro-detail only where detail is already present, matching the existing grain, focus, colour, and material properties of each surface. Keep in-focus areas crisp and sharp, keep softly blurred areas soft, and leave flat or evenly-toned areas clean and smooth. Add no new objects, elements, or content — refine only what is already in the tile. Preserve the original lighting, colour, contrast, and composition exactly as shown. Produce a clean, photorealistic result faithful to the source.

Everything except `{TEXTURE FAMILIES}` is fixed. Do not reword the trigger,
the anti-hallucination clause, the depth-of-field clause, the negative-space
clause, or the closing line.

---

## The texture-families slot

`{TEXTURE FAMILIES}` is a short list of **generic material types** that
*may* be present anywhere in the image. Three rules:

1. **No subjects, no objects, no named instances.** Not "the car", not "the
   sheep face", not "the dress." Only material families: "skin", "fabric",
   "metal", "fur".
2. **Use category nouns, not adjectives + nouns.** "Fabric weave" rather than
   "red canvas fabric." "Metal and reflections" rather than "polished steel
   helmet." Adjectives anchor to a specific instance; categories don't.
3. **Cover the families likely in the image, not exhaustively.** Three to
   seven category nouns is right. The list is hints about what *kinds* of
   detail to refine, not a description of the image.

Examples by image type — note none of these names a subject:

- **Portrait / figure pass:** `fabric weave, skin pores, hair, reflections, and fine grain`
- **Animal pass:** `fur and wool, fleece, animal hide, fine hair, and skin`
- **Vehicle pass:** `glossy painted surfaces, glass, metal, reflections, textured ground, foliage, and fine grain`
- **Landscape pass:** `foliage, bark, stone, grass and ground cover, water, and atmospheric depth`
- **Mixed scene:** `fabric, skin, hair, metal, reflections, and natural surfaces`

When in doubt, lean shorter. A texture family the model doesn't see in a tile
is ignored; a named subject that isn't in the tile may be hallucinated into
it.

---

## The fixed clauses — what they do

- **"enrich the existing textures and surfaces already present in this
  tile"** — the prompt's whole stance. Refine what's in the tile, not what
  the image *contains*.
- **"refining whatever materials appear"** — explicitly conditional. If a
  texture family isn't in the tile, the instruction doesn't apply.
- **"matching the existing grain, focus, colour, and material properties of
  each surface"** — refine each surface in character; do not apply one
  uniform sharpening pass.
- **depth-of-field clause** — keep intentionally soft/blurred areas soft;
  do not sharpen an out-of-focus background and flatten the depth.
- **negative-space clause** — leave large flat or evenly-toned areas clean
  and smooth; do not hallucinate detail into empty regions.
- **"Add no new objects, elements, or content — refine only what is already
  in the tile."** — the load-bearing anti-hallucination instruction. This
  clause is the reason the tier exists; do not drop or soften it.
- **scope lock** — change resolution and detail only, never content or look.

---

## Writing rules

1. **No named subjects, ever.** No "the cat", no "the woman", no "the car".
   This is the discipline that separates this tier from the texture tier.
2. **Material categories, not instances.** "Metal" not "the silver crown";
   "fabric" not "the lace dress."
3. **Positive framing throughout.** "Leave flat areas clean" rather than
   "do not invent detail in flat areas" (the anti-hallucination clause is the
   one place explicit instruction-to-omit is allowed, because it works).
4. **Recovery verbs only.** Restore, resolve, recover, refine, sharpen,
   preserve. Never "improve" / "enhance" / "make better".
5. **Keep it short.** Three to seven texture families. This tier's strength
   is what it *doesn't* name; more is not better.

---

## Known limitations

- **Weaker targeted detail.** With no specific anchors, fragile materials
  (lace, beadwork, fine ornament) get only generic treatment. If a fragile
  material matters, use the full build instead and accept the hallucination
  risk on empty tiles, or composite the fragile element in post.
- **Text and fine printed graphics** — same ceiling as every tier. Composite
  in post for must-be-legible content.
- **Will not rescue a wrong-tier choice.** If the image actually wants the
  texture tier or the full build, this prompt's safer behaviour will leave
  detail on the table that those would have recovered. The choice is the
  point, not a fallback.

---

## Worked examples

**Image:** a flock of near-identical sheep packed edge to edge, one black
ram in the centre. High-res many-tile pass.

> RFNTILE. refine and add detail to this upscaled tile. Restore the image quality and resolve it to a sharp, high-resolution result. Remove compression artifacts, banding, and noise, and clarify soft or blurred areas into crisp, clean edges and definition. Enrich the existing textures and surfaces already present in this tile with fine, intricate, physically accurate detail — refining whatever materials appear, sharpening fine texture, edges, and surface structure, and resolving fur and wool, fleece, animal hide, fine hair, and skin wherever they occur. Recover realistic, lifelike micro-detail only where detail is already present, matching the existing grain, focus, colour, and material properties of each surface. Keep in-focus areas crisp and sharp, keep softly blurred areas soft, and leave flat or evenly-toned areas clean and smooth. Add no new objects, elements, or content — refine only what is already in the tile. Preserve the original lighting, colour, contrast, and composition exactly as shown. Produce a clean, photorealistic result faithful to the source.

The flock is the canonical dense-repeated-subject case. Naming "sheep faces"
in the texture tier risks tiles with empty wool getting extra faces invented.
Here the families are only "fur and wool, fleece, animal hide, fine hair,
skin" — no count, no faces, no subjects — and the anti-hallucination clause
caps the door.

**Image:** a grey sports car centred under a dramatic single overhead light,
large dark sky and mountain surround. High-res many-tile pass.

> RFNTILE. refine and add detail to this upscaled tile. Restore the image quality and resolve it to a sharp, high-resolution result. Remove compression artifacts, banding, and noise, and clarify soft or blurred areas into crisp, clean edges and definition. Enrich the existing textures and surfaces already present in this tile with fine, intricate, physically accurate detail — refining whatever materials appear, sharpening fine texture, edges, and surface structure, and resolving glossy painted surfaces, glass, metal, reflections, textured ground, foliage, and fine grain wherever they occur. Recover realistic, lifelike micro-detail only where detail is already present, matching the existing grain, focus, colour, and material properties of each surface. Keep in-focus areas crisp and sharp, keep softly blurred areas soft, and leave flat or evenly-toned areas clean and smooth. Add no new objects, elements, or content — refine only what is already in the tile. Preserve the original lighting, colour, contrast, and composition exactly as shown. Produce a clean, photorealistic result faithful to the source.

The large empty sky is the trigger here. Tiles landing on pure dark sky get
correctly told to leave it clean; tiles landing on the car get the relevant
texture families. No tile is told "the car" belongs there.

---

## Checklist

- [ ] Opens with the full trigger phrase verbatim
- [ ] No subjects, objects, or named instances anywhere in the prompt
- [ ] Texture-families slot uses category nouns only (3–7 entries)
- [ ] Anti-hallucination clause present and unreworded
- [ ] Depth-of-field and negative-space clauses present
- [ ] Scope lock is the final sentence
- [ ] Image actually suits this tier — context-free crops, dense subjects, or
      large empty regions; not a recognisable single-subject image

---

## See also

- `texture_upscale_prompt.md` — texture tier for high-res many-tile passes
  with recognisable material regions.
- `full_build_upscale_prompt.md` — block-based per-image build for low-res
  few-tile passes.
