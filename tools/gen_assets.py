#!/usr/bin/env python3
"""Generate all templated assets/data for the wool stairs+slabs backport.

One DRY source for 16 colors x {stairs, slab}. Re-run after editing templates:
    python3 tools/gen_assets.py

Emits into src/main/resources:
  - assets/woolbackport/models/block/<color>_wool_{stairs,stairs_inner,stairs_outer,slab,slab_top}.json
  - assets/woolbackport/items/<color>_wool_{stairs,stairs_inner,stairs_outer,slab,slab_top}.json
  - assets/woolbackport/lang/en_us.json (resource-pack names for pack-having clients)
  - data/woolbackport/lang/en_us.json   (Server Translations API names for pack-less clients)
  - data/minecraft/recipe/<color>_wool_{stairs,slab}.json
  - data/minecraft/tags/block/shears_major_breaking_speed.json  (shears mine them fast, like wool)

No PNG textures: every model reuses the existing vanilla minecraft:block/<color>_wool texture.
"""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
RES = ROOT / "src/main/resources"

# id -> display name
COLORS = {
    "white": "White", "orange": "Orange", "magenta": "Magenta",
    "light_blue": "Light Blue", "yellow": "Yellow", "lime": "Lime",
    "pink": "Pink", "gray": "Gray", "light_gray": "Light Gray",
    "cyan": "Cyan", "purple": "Purple", "blue": "Blue",
    "brown": "Brown", "green": "Green", "red": "Red", "black": "Black",
}

# block model parent per variant suffix
STAIR_VARIANTS = {
    "_wool_stairs": "minecraft:block/stairs",
    "_wool_stairs_inner": "minecraft:block/inner_stairs",
    "_wool_stairs_outer": "minecraft:block/outer_stairs",
}
SLAB_VARIANTS = {
    "_wool_slab": "minecraft:block/slab",
    "_wool_slab_top": "minecraft:block/slab_top",
}
ALL_VARIANTS = {**STAIR_VARIANTS, **SLAB_VARIANTS}


def write(path: pathlib.Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n")


def main():
    lang = {}
    shears = []  # block ids that shears mine fast (added to #minecraft:shears_major_breaking_speed)
    n = 0
    for color, name in COLORS.items():
        tex = f"minecraft:block/{color}_wool"
        for suffix, parent in ALL_VARIANTS.items():
            model_name = f"{color}{suffix}"
            # block model — all faces use the existing vanilla wool texture.
            # Explicit fixed-display scale 0.5 (like minecraft:block/block): the inner/outer stair
            # and slab_top templates have NO parent/display, so without this they'd render at 1.0
            # and the item-display's x2 would double them. 0.5 * 2 = flush 1x1 for every model.
            write(RES / f"assets/woolbackport/models/block/{model_name}.json", {
                "parent": parent,
                "display": {"fixed": {"scale": [0.5, 0.5, 0.5]}},
                "textures": {"bottom": tex, "top": tex, "side": tex},
            })
            # item asset — points the item_model component at the block model above
            write(RES / f"assets/woolbackport/items/{model_name}.json", {
                "model": {"type": "minecraft:model", "model": f"woolbackport:block/{model_name}"},
            })
            n += 2

        # lang: blocks are registered under minecraft: ids, so keys are block.minecraft.*
        lang[f"block.minecraft.{color}_wool_stairs"] = f"{name} Wool Stairs"
        lang[f"block.minecraft.{color}_wool_slab"] = f"{name} Wool Slab"

        shears.append(f"minecraft:{color}_wool_stairs")
        shears.append(f"minecraft:{color}_wool_slab")

        # loot tables (drop self; no tool condition -> wool always drops with any tool).
        # Slab drops 2 when double, matching vanilla oak_slab.
        stairs_id = f"minecraft:{color}_wool_stairs"
        slab_id = f"minecraft:{color}_wool_slab"
        write(RES / f"data/minecraft/loot_table/blocks/{color}_wool_stairs.json", {
            "type": "minecraft:block",
            "pools": [{
                "rolls": 1.0,
                "conditions": [{"condition": "minecraft:survives_explosion"}],
                "entries": [{"type": "minecraft:item", "name": stairs_id}],
            }],
            "random_sequence": f"minecraft:blocks/{color}_wool_stairs",
        })
        write(RES / f"data/minecraft/loot_table/blocks/{color}_wool_slab.json", {
            "type": "minecraft:block",
            "pools": [{
                "rolls": 1.0,
                "entries": [{
                    "type": "minecraft:item",
                    "name": slab_id,
                    "functions": [
                        {"function": "minecraft:set_count", "count": 2.0, "conditions": [{
                            "condition": "minecraft:block_state_property",
                            "block": slab_id,
                            "properties": {"type": "double"},
                        }]},
                        {"function": "minecraft:explosion_decay"},
                    ],
                }],
            }],
            "random_sequence": f"minecraft:blocks/{color}_wool_slab",
        })

        # recipes (vanilla patterns: 6 wool -> 4 stairs, 3 wool -> 6 slabs)
        wool = f"minecraft:{color}_wool"
        write(RES / f"data/minecraft/recipe/{color}_wool_stairs.json", {
            "type": "minecraft:crafting_shaped", "category": "building",
            "key": {"#": wool}, "pattern": ["#  ", "## ", "###"],
            "result": {"id": f"minecraft:{color}_wool_stairs", "count": 4},
        })
        write(RES / f"data/minecraft/recipe/{color}_wool_slab.json", {
            "type": "minecraft:crafting_shaped", "category": "building",
            "key": {"#": wool}, "pattern": ["###"],
            "result": {"id": f"minecraft:{color}_wool_slab", "count": 6},
        })
        n += 2

    lang_sorted = dict(sorted(lang.items()))
    # Resource-pack lang. The client merges every namespace's lang/*.json into one global map, so the
    # block.minecraft.* keys resolve even from our namespace — and addModAssets(MOD_ID) bundles
    # assets/woolbackport/ into the pack (it does NOT bundle assets/minecraft/, which is why the
    # minecraft-namespace path silently failed before). This is what actually shows names in-game.
    write(RES / "assets/woolbackport/lang/en_us.json", lang_sorted)
    # Datapack lang: Server Translations API reads data/<ns>/lang/*.json and sends per-client name
    # fallbacks, so clients who decline the resource pack still get real names.
    write(RES / "data/woolbackport/lang/en_us.json", lang_sorted)
    # Additive tag (no "replace") -> our blocks join wool in the shears fast-mine rule.
    write(RES / "data/minecraft/tags/block/shears_major_breaking_speed.json", {"values": shears})
    n += 3
    print(f"generated {n} files for {len(COLORS)} colors")


if __name__ == "__main__":
    main()
