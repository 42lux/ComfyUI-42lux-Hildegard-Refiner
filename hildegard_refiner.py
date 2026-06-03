# Tiling math and feathered-mask compositing adapted from
# https://github.com/Steudio/ComfyUI_Steudio (GPL-3.0).

from __future__ import annotations

import math
import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFilter
from typing_extensions import override

import comfy.utils
from comfy_api.latest import ComfyExtension, io
from server import PromptServer


OVERLAP_DICT = {
    "None": 0,
    "1/64 Tile": 0.015625,
    "1/32 Tile": 0.03125,
    "1/16 Tile": 0.0625,
    "1/8 Tile": 0.125,
    "1/4 Tile": 0.25,
    "1/2 Tile": 0.5,
}

TILE_ORDER_DICT = {"linear": 0, "spiral": 1}

SCALING_METHODS = ["nearest-exact", "bilinear", "area", "bicubic", "lanczos"]

# Matches the official EmptyFlux2LatentImage node (step=16, spacial_downscale_ratio=16).
LATENT_ALIGN = 16
MIN_SCALE_FACTOR_THRESHOLD = 1.0

# Position-map cosmetic constants (cyan corner markers around the center cell).
_MARKER_COLOR = (0, 255, 255)
_MARKER_THICKNESS = 4
_MARKER_ARM_RATIO = 0.09
_GRAY_FILL = (128, 128, 128)


def _status(cls, text):
    try:
        uid = getattr(cls.hidden, "unique_id", None)
    except Exception:
        uid = None
    if uid is None:
        return
    try:
        PromptServer.instance.send_progress_text(text, uid)
    except Exception:
        pass


def _calc_overlap(tile_size, overlap_fraction):
    return int(overlap_fraction * tile_size)


def _snap(value, multiple=LATENT_ALIGN):
    return max(multiple, (int(value) // multiple) * multiple)


def _create_tile_coordinates(image_width, image_height, tile_width, tile_height,
                             overlap_x, overlap_y, grid_x, grid_y, tile_order):
    tiles = []
    matrix = [["" for _ in range(grid_x)] for _ in range(grid_y)]

    for row in range(grid_y):
        y = row * (tile_height - overlap_y)
        if row == grid_y - 1:
            y = image_height - tile_height
        for col in range(grid_x):
            x = col * (tile_width - overlap_x)
            if col == grid_x - 1:
                x = image_width - tile_width
            tiles.append((x, y))

    if tile_order == 1:
        # Outward clockwise spiral starting from center, then reversed so the
        # iteration visits center-last.
        spiral_tiles = []
        visited = set()
        x, y = grid_x // 2, grid_y // 2
        dx, dy = 1, 0
        layer = 1
        while len(spiral_tiles) < len(tiles):
            for _ in range(2):
                for _ in range(layer):
                    if 0 <= x < grid_x and 0 <= y < grid_y and (x, y) not in visited:
                        index = y * grid_x + x
                        if index < len(tiles):
                            spiral_tiles.append(tiles[index])
                            visited.add((x, y))
                    x += dx
                    y += dy
                dx, dy = -dy, dx
            layer += 1
        spiral_tiles.reverse()
        tiles = spiral_tiles

    for i, (x, y) in enumerate(tiles):
        row, col = y // (tile_height - overlap_y), x // (tile_width - overlap_x)
        matrix[row][col] = f"{i + 1} ({x},{y})"

    return tiles, matrix


class Hildegard_Plan(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Hildegard Plan",
            display_name="Hildegard Plan",
            category="upscale/hildegard-refiner",
            description=(
                "Calculate optimal upscaled dimensions and a tile grid that "
                "satisfies min_overlap + min_scale_factor. Upscale uses the "
                "chosen scaling_method (no model). "
                f"Tile dimensions snap to multiples of {LATENT_ALIGN}."
            ),
            inputs=[
                io.Image.Input("image"),
                io.Int.Input("tile_width", default=1536, min=LATENT_ALIGN, max=8192, step=LATENT_ALIGN),
                io.Int.Input("tile_height", default=1536, min=LATENT_ALIGN, max=8192, step=LATENT_ALIGN),
                io.Combo.Input("min_overlap", options=list(OVERLAP_DICT.keys()), default="1/32 Tile"),
                io.Float.Input("min_scale_factor", default=3.0, min=1.0, max=8.0, step=0.01),
                io.Combo.Input("tile_order", options=list(TILE_ORDER_DICT.keys()), default="spiral"),
                io.Combo.Input("scaling_method", options=SCALING_METHODS, default="lanczos"),
            ],
            outputs=[
                io.Image.Output(display_name="IMAGE"),
                io.Custom("HILDEGARD_DATA").Output(display_name="dac_data"),
            ],
            hidden=[io.Hidden.unique_id],
        )

    @classmethod
    def execute(cls, image, tile_width, tile_height, min_overlap, min_scale_factor,
                tile_order, scaling_method) -> io.NodeOutput:
        upscaled_image, dac_data, text = _hildegard_compute_upscale(
            image=image,
            tile_width=tile_width,
            tile_height=tile_height,
            overlap=OVERLAP_DICT.get(min_overlap, 0),
            min_scale_factor=min_scale_factor,
            tile_order_v=TILE_ORDER_DICT.get(tile_order, 0),
            scaling_method=scaling_method,
        )
        _status(cls, text)
        return io.NodeOutput(upscaled_image, dac_data)


def _hildegard_compute_upscale(image, tile_width, tile_height, overlap, min_scale_factor,
                               tile_order_v, scaling_method):
    tile_width = _snap(tile_width)
    tile_height = _snap(tile_height)
    _, height, width, _ = image.shape

    overlap_x = _calc_overlap(tile_width, overlap)
    overlap_y = _calc_overlap(tile_height, overlap)
    min_scale_factor = max(min_scale_factor, MIN_SCALE_FACTOR_THRESHOLD)

    if width <= height:
        multiply_factor = math.ceil(min_scale_factor * width / tile_width)
        while True:
            upscaled_width = tile_width * multiply_factor
            grid_x = math.ceil(upscaled_width / tile_width)
            upscaled_width = tile_width * grid_x - overlap_x * (grid_x - 1)
            upscale_ratio = upscaled_width / width
            if upscale_ratio >= min_scale_factor:
                break
            multiply_factor += 1
        upscaled_height = int(height * upscale_ratio)
        grid_y = math.ceil((upscaled_height - overlap_y) / (tile_height - overlap_y))
        if grid_y > 1:
            overlap_y = round((tile_height * grid_y - upscaled_height) / (grid_y - 1))
    else:
        multiply_factor = math.ceil(min_scale_factor * height / tile_height)
        while True:
            upscaled_height = tile_height * multiply_factor
            grid_y = math.ceil(upscaled_height / tile_height)
            upscaled_height = tile_height * grid_y - overlap_y * (grid_y - 1)
            upscale_ratio = upscaled_height / height
            if upscale_ratio >= min_scale_factor:
                break
            multiply_factor += 1
        upscaled_width = int(width * upscale_ratio)
        grid_x = math.ceil((upscaled_width - overlap_x) / (tile_width - overlap_x))
        if grid_x > 1:
            overlap_x = round((tile_width * grid_x - upscaled_width) / (grid_x - 1))

    dac_data = {
        "upscaled_width": upscaled_width,
        "upscaled_height": upscaled_height,
        "tile_width": tile_width,
        "tile_height": tile_height,
        "overlap_x": overlap_x,
        "overlap_y": overlap_y,
        "grid_x": grid_x,
        "grid_y": grid_y,
        "tile_order": tile_order_v,
    }

    samples = image.movedim(-1, 1)
    upscaled_image = comfy.utils.common_upscale(
        samples, upscaled_width, upscaled_height, scaling_method, crop=0,
    ).movedim(1, -1)

    info_text = (
        "Hildegard Plan:\n"
        f"Original: {width}x{height}\n"
        f"Upscaled: {upscaled_width}x{upscaled_height}\n"
        f"Grid: {grid_x}x{grid_y} ({grid_x * grid_y} tiles)\n"
        f"Tile: {tile_width}x{tile_height}\n"
        f"Overlap: {overlap_x}x{overlap_y} px\n"
        f"Effective scale: {round(upscaled_width / width, 2)}x"
    )
    return upscaled_image, dac_data, info_text


def _gaussian_blur_bhwc(image_bhwc, radius):
    """Gaussian-blur a single-batch BHWC float tensor via PIL."""
    arr = (image_bhwc[0].detach().clamp(0.0, 1.0) * 255.0).round().to(torch.uint8).cpu().numpy()
    pil = Image.fromarray(arr, mode="RGB").filter(ImageFilter.GaussianBlur(radius=radius))
    out = np.asarray(pil).astype(np.float32) / 255.0
    return torch.from_numpy(out).unsqueeze(0).to(image_bhwc.dtype)


class Hildegard_Combine(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Hildegard Combine",
            display_name="Hildegard Combine",
            category="upscale/hildegard-refiner",
            inputs=[
                io.Image.Input("images"),
                io.Custom("HILDEGARD_DATA").Input("dac_data"),
            ],
            outputs=[
                io.Image.Output(display_name="image"),
            ],
            is_input_list=True,
            hidden=[io.Hidden.unique_id],
        )

    @classmethod
    def execute(cls, images, dac_data) -> io.NodeOutput:
        if isinstance(dac_data, list):
            dac_data = dac_data[0]
        images = torch.stack(list(images)).squeeze(1)

        upscaled_width = dac_data["upscaled_width"]
        upscaled_height = dac_data["upscaled_height"]
        overlap_x = dac_data["overlap_x"]
        overlap_y = dac_data["overlap_y"]
        grid_x = dac_data["grid_x"]
        grid_y = dac_data["grid_y"]
        tile_order = dac_data["tile_order"]

        tile_height, tile_width = images.shape[1], images.shape[2]
        f_overlap_x = overlap_x // 4
        f_overlap_y = overlap_y // 4
        blend_x = math.sqrt(overlap_x)
        blend_y = math.sqrt(overlap_y)

        tile_coordinates, matrix = _create_tile_coordinates(
            upscaled_width, upscaled_height, tile_width, tile_height,
            overlap_x, overlap_y, grid_x, grid_y, tile_order,
        )

        output = torch.zeros((1, upscaled_height, upscaled_width, 3), dtype=images.dtype)

        for index, (x, y) in enumerate(tile_coordinates):
            image_tile = images[index]

            # Feather only on sides that border another tile.
            has_left = x != 0
            has_right = x != upscaled_width - tile_width
            has_top = y != 0
            has_bottom = y != upscaled_height - tile_height
            left = f_overlap_x if has_left else 0
            top = f_overlap_y if has_top else 0
            right = tile_width - f_overlap_x if has_right else tile_width
            bottom = tile_height - f_overlap_y if has_bottom else tile_height

            mask = Image.new("L", (tile_width, tile_height), 0)
            ImageDraw.Draw(mask).rectangle([left, top, right, bottom], fill=255)
            blur = ImageFilter.BoxBlur if overlap_x <= 64 or overlap_y <= 64 else ImageFilter.GaussianBlur
            mask = mask.filter(blur(radius=(blend_x, blend_y)))

            mask_tensor = torch.tensor(np.array(mask) / 255.0, dtype=images.dtype).unsqueeze(0).unsqueeze(-1)
            output[:, y:y + tile_height, x:x + tile_width, :] *= (1 - mask_tensor)
            output[:, y:y + tile_height, x:x + tile_width, :] += image_tile * mask_tensor

        _status(cls, "Tile matrix:\n" + "\n".join(" ".join(row) for row in matrix))
        return io.NodeOutput(output)


def _tensor_to_pil(t_hwc):
    arr = (t_hwc.detach().clamp(0.0, 1.0) * 255.0).round().to(torch.uint8).cpu().numpy()
    return Image.fromarray(arr, mode="RGB")


def _pil_to_tensor(img):
    arr = np.asarray(img.convert("RGB")).astype(np.float32) / 255.0
    return torch.from_numpy(arr).unsqueeze(0)


def _draw_corner_markers(image, cell_x, cell_y, cell_size, color, thickness, arm_length):
    draw = ImageDraw.Draw(image)
    t, a = thickness, arm_length
    x0, y0 = cell_x, cell_y
    x1, y1 = cell_x + cell_size, cell_y + cell_size
    draw.rectangle([x0 - t, y0 - t, x0 + a, y0],     fill=color)
    draw.rectangle([x0 - t, y0 - t, x0,     y0 + a], fill=color)
    draw.rectangle([x1 - a, y0 - t, x1 + t, y0],     fill=color)
    draw.rectangle([x1,     y0 - t, x1 + t, y0 + a], fill=color)
    draw.rectangle([x0 - t, y1,     x0 + a, y1 + t], fill=color)
    draw.rectangle([x0 - t, y1 - a, x0,     y1 + t], fill=color)
    draw.rectangle([x1 - a, y1,     x1 + t, y1 + t], fill=color)
    draw.rectangle([x1,     y1 - a, x1 + t, y1 + t], fill=color)


def _build_position_map(source_pil, tx, ty, tile_w, tile_h, cell_size):
    """3x3 grid showing the current tile in the center cell plus its 8
    neighbors. Off-canvas cells stay gray; corner markers ring the center."""
    grid_size = cell_size * 3
    canvas = Image.new("RGB", (grid_size, grid_size), _GRAY_FILL)
    img_w, img_h = source_pil.size

    offsets = [(-1, -1), (-1, 0), (-1, 1),
               ( 0, -1), ( 0, 0), ( 0, 1),
               ( 1, -1), ( 1, 0), ( 1, 1)]
    for idx, (dr, dc) in enumerate(offsets):
        nx = tx + dc * tile_w
        ny = ty + dr * tile_h
        grid_cx = (idx % 3) * cell_size
        grid_cy = (idx // 3) * cell_size

        src_x1 = max(0, nx)
        src_y1 = max(0, ny)
        src_x2 = min(nx + tile_w, img_w)
        src_y2 = min(ny + tile_h, img_h)
        if src_x1 >= src_x2 or src_y1 >= src_y2:
            continue

        crop = source_pil.crop((src_x1, src_y1, src_x2, src_y2))

        # Short-circuit fully-covered cells (always the case for the center
        # cell, and for any neighbor that isn't clipped by the source bounds).
        # Avoids both the per-axis floor-rounding gap and the bicubic edge
        # halo on the cell boundary.
        if src_x1 == nx and src_y1 == ny and src_x2 == nx + tile_w and src_y2 == ny + tile_h:
            dst_x = dst_y = 0
            dst_w = dst_h = cell_size
        else:
            # Derive dst extent by rounding end coords, then differencing —
            # guarantees dst_x + dst_w lands where the cell boundary expects it
            # (no 1-px gray strip exposed by independent floor() on each).
            dst_x = int((src_x1 - nx) / tile_w * cell_size)
            dst_y = int((src_y1 - ny) / tile_h * cell_size)
            dst_x2 = int(round((src_x2 - nx) / tile_w * cell_size))
            dst_y2 = int(round((src_y2 - ny) / tile_h * cell_size))
            dst_w = dst_x2 - dst_x
            dst_h = dst_y2 - dst_y
            if dst_w <= 0 or dst_h <= 0:
                continue

        cell = Image.new("RGB", (cell_size, cell_size), _GRAY_FILL)
        cell.paste(crop.resize((dst_w, dst_h), Image.BICUBIC), (dst_x, dst_y))
        canvas.paste(cell, (grid_cx, grid_cy))

    _draw_corner_markers(
        canvas,
        cell_x=cell_size, cell_y=cell_size, cell_size=cell_size,
        color=_MARKER_COLOR, thickness=_MARKER_THICKNESS,
        arm_length=int(cell_size * _MARKER_ARM_RATIO),
    )
    return canvas


def _build_global_thumb(source_pil, max_size):
    w, h = source_pil.size
    scale = min(max_size / w, max_size / h)
    if scale >= 1.0:
        return source_pil.copy()
    return source_pil.resize((int(w * scale), int(h * scale)), Image.BICUBIC)


class Hildegard_References_Split(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Hildegard References Split",
            display_name="Hildegard References Split",
            category="upscale/hildegard-refiner",
            description=(
                "Split the upscaled image into tiles and build the three Hildegard "
                "reference latents in one pass:\n"
                "  - tile_latent: VAE-encoded crop of each tile (with optional "
                "high-frequency reduction so the model has room to invent texture)\n"
                "  - position_latent: VAE-encoded 3x3 position map (current tile in "
                "center, 8 neighbors around it, cyan corner brackets ring the center)\n"
                "  - global_latent: VAE-encoded thumbnail of the whole upscaled image\n"
                "tile 0 = all tiles (lists), tile # = only that tile."
            ),
            inputs=[
                io.Image.Input(
                    "image",
                    tooltip="Upscaled IMAGE from Hildegard Plan."),
                io.Custom("HILDEGARD_DATA").Input(
                    "dac_data",
                    tooltip="dac_data from Hildegard Plan. Carries the tile grid, "
                            "overlaps, and ordering this node has to honor."),
                io.Vae.Input(
                    "vae",
                    tooltip="VAE used to encode the three reference image types into "
                            "latents. For FLUX.2 Klein, the Klein VAE."),
                io.Int.Input(
                    "tile", default=0, min=0, step=1,
                    tooltip="0 = process all tiles in the grid (each output is a list "
                            "of N entries). N >= 1 = process only that single tile "
                            "(each output is a list of 1). Index follows the same "
                            "linear/spiral ordering Hildegard Plan picked."),
                io.Int.Input(
                    "cell_size", default=512, min=64, max=2048, step=16,
                    tooltip="Side length (px) of each cell in the 3x3 position map. "
                            "The final position image is cell_size x 3 on each axis. "
                            "Larger = more spatial context detail, larger position "
                            "latent. 512 is the Hildegard training default."),
                io.Int.Input(
                    "ctrl3_max_size", default=2048, min=256, max=8192, step=16,
                    tooltip="Long-edge cap (px) for the global thumbnail before VAE "
                            "encoding. The whole upscaled image is downscaled so its "
                            "longer edge fits this. 2048 is the Hildegard training "
                            "default."),
                io.Float.Input(
                    "tile_high_freq_reduce", default=0.00, min=0.0, max=1.0, step=0.05,
                    tooltip="Attenuate the tile reference's high-frequency band "
                            "(micro-detail / edges / texture) before VAE-encoding. "
                            "0 = full source detail preserved in the reference "
                            "(tight fidelity, model has little room to add). "
                            "1 = soft, low-contrast version with only broad "
                            "shapes and color preserved.\n\n"
                            "Only affects the tile_latent output. The TILE(S) "
                            "image output, position_latent, and global_latent "
                            "are untouched."),
                io.Float.Input(
                    "low_freq_radius", default=256.0, min=1.0, max=256.0, step=1.0,
                    tooltip="Gaussian-blur radius (px) defining the cutoff between "
                            "low and high frequencies for tile_high_freq_reduce. "
                            "Larger = more of the source's detail is classified as "
                            "'low frequency' and survives the reduce. Smaller = only "
                            "the very-broadest shapes survive; the model regenerates "
                            "everything else."),
            ],
            outputs=[
                io.Image.Output(display_name="TILE(S)", is_output_list=True),
                io.Image.Output(display_name="POSITION(S)", is_output_list=True),
                io.Latent.Output(display_name="tile_latent", is_output_list=True),
                io.Latent.Output(display_name="position_latent", is_output_list=True),
                io.Latent.Output(display_name="global_latent"),
            ],
            hidden=[io.Hidden.unique_id],
        )

    @classmethod
    def execute(cls, image, dac_data, vae, tile, cell_size, ctrl3_max_size,
                tile_high_freq_reduce=0.50, low_freq_radius=15.0) -> io.NodeOutput:
        tile_width = dac_data["tile_width"]
        tile_height = dac_data["tile_height"]

        tile_coords, _ = _create_tile_coordinates(
            image.shape[2], image.shape[1],
            tile_width, tile_height,
            dac_data["overlap_x"], dac_data["overlap_y"],
            dac_data["grid_x"], dac_data["grid_y"],
            dac_data["tile_order"],
        )
        num_tiles = len(tile_coords)
        if num_tiles == 0:
            raise ValueError("dac_data produced zero tiles")
        if tile < 0 or tile > num_tiles:
            raise ValueError(f"tile {tile} out of range (0..{num_tiles})")

        source_pil = _tensor_to_pil(image[0])
        global_latent = {"samples": vae.encode(_pil_to_tensor(_build_global_thumb(source_pil, ctrl3_max_size)))}

        indices = list(range(num_tiles)) if tile == 0 else [tile - 1]

        tiles_out = []
        tile_latents = []
        position_latents = []
        position_images = []

        for n, idx in enumerate(indices):
            x, y = tile_coords[idx]
            _status(cls, f"Slicing + encoding {n + 1}/{len(indices)}")

            crop = image[:, y:y + tile_height, x:x + tile_width, :].contiguous()
            tiles_out.append(crop)

            # Optionally attenuate the tile reference's high-frequency band.
            # crop_for_latent = (1 − reduce) × crop + reduce × low
            #   reduce = 0 → crop (unchanged)
            #   reduce = 1 → fully blurred (only broad shapes / color survive)
            if tile_high_freq_reduce > 0.0:
                low = _gaussian_blur_bhwc(crop, low_freq_radius)
                crop_for_latent = ((1.0 - tile_high_freq_reduce) * crop
                                   + tile_high_freq_reduce * low).clamp(0.0, 1.0)
            else:
                crop_for_latent = crop
            tile_latents.append({"samples": vae.encode(crop_for_latent)})

            pos_pil = _build_position_map(source_pil, x, y, tile_width, tile_height, cell_size)
            pos_tensor = _pil_to_tensor(pos_pil)
            position_images.append(pos_tensor)
            position_latents.append({"samples": vae.encode(pos_tensor)})

        result_tiles = [t[0].unsqueeze(0) if t.shape[0] == 1 else t for t in tiles_out]
        return io.NodeOutput(result_tiles, position_images, tile_latents, position_latents, global_latent)


class HildegardExtension(ComfyExtension):
    @override
    async def get_node_list(self):
        return [
            Hildegard_Plan,
            Hildegard_References_Split,
            Hildegard_Combine,
        ]
