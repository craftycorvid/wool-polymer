# Wool Stairs & Slabs Backport

Server-side backport of Minecraft **26.3**'s wool stairs and slabs (all 16 colors) to **26.2**,
built with [Polymer](https://polymer.pb4.eu) + Fabric. Players need **only a resource pack** (for the
shapes) — no client mod. Names, drops, recipes and shears-mining all work server-side. Designed to
vanish the moment 26.3 ships: the blocks use their **native `minecraft:` ids**, so world data is
identical and native takes over with zero migration.

Craft them (6 wool → 4 stairs, 3 wool → 6 slabs), mine them fast with **shears** like wool, and they
**always drop themselves** (any tool or hand). Item names ("White Wool Stairs" …) are delivered by
the bundled [Server Translations API](https://github.com/NucleoidMC/Server-Translations), so they
render correctly on vanilla clients even without the pack.

## Requirements

- A **Fabric 26.2** server (Java 25). 26.x is unobfuscated, so no Yarn/mappings.
- **Fabric API** installed on the server.
- Polymer is bundled inside the jar (jar-in-jar) — nothing else to install.

## Build

```sh
./gradlew build      # -> build/libs/wool-backport-1.0.0.jar
```

## Install

1. Drop the jar into the server's `mods/` folder (alongside Fabric API).
2. Make the generated resource pack reach players (it's marked **required**). Easiest path —
   the bundled **autohost** serves it automatically; enable it once in
   `config/polymer/auto-host.json`:
   ```json
   { "enabled": true }
   ```
   (Behind a proxy, also set `"forced_address"`.) Alternatively run `/polymer generate-pack`
   and serve `polymer/resourcepack.zip` yourself via `resource-pack` in `server.properties`.
3. Players accept the pack on join and see proper wool stairs/slabs. Craft them with the usual
   patterns (6 wool → 4 stairs, 3 wool → 6 slabs).

## When 26.3 arrives

The blocks are real `minecraft:<color>_wool_stairs` / `_slab`, so existing builds load **natively**
with no conversion. The mod also refuses to load on 26.3 (`"minecraft": ">=26.2 <26.3"`), and even
if forced it no-ops when the ids already exist. **Just delete the jar** — or leave it; it's inert.

## How it works (and the tradeoffs)

Polymer's textured-block donor pools are tiny (~4 slab / ~3 stair colors, server-wide) — far short
of 16. So each placed block is a **real server-side block** (correct collision, hitbox, saved data)
whose client visual is a per-block **item-display entity** (`ItemDisplayContext.FIXED` + `scale 2`,
anchored at block center → flush 1×1) carrying the shape model from the pack. Item models have no
pool limit, so all 16 colors work. Double slabs render as a plain full wool block (free).

The client also needs a stand-in *block* at that position for collision, targeting and occlusion.
Both use an **invisible donor of the matching shape** (`requestEmpty`, which is exempt from the tiny
pool), so client collision and outline equal the real block:

- **Slabs** use an invisible **slab** donor (`getSlab(bottom, waterlogged)`) → exact shape; both
  top and bottom slabs are fully clickable.
- **Stairs** use an invisible **stair** donor matching the state's `facing/half/shape/waterlogged`
  → you walk up accurately and can break/place on the whole stair, **including the top step**. The
  stair donor's full faces cull neighbours, but the display entity renders the wool stair flush over
  the cell, so there's no see-through void. The real stair shape stays authoritative server-side.

- **No resource pack? No broken textures.** The display item is a `PolymerItem` that Polymer
  re-encodes per viewer, so a player *without* the pack gets a generic vanilla **oak stairs** (or,
  for slabs, just the invisible slab-shaped donor showing through) instead of the magenta
  missing-model cube. Held/inventory items degrade the same way. With the pack, they're colored wool.
- **Sounds.** Place, break, step, mining-hit and fall all play the **wool** sounds. Break is
  redirected server-side (`getPolymerBreakEventBlockState` → the real wool block: wool break sound +
  colored particles); place works because the held item falls back to the matching wool block, so
  the client predicts a wool placement. Step / hit / fall are predicted from the invisible copper
  donor, so `polymer-sound-patcher` silences *those* copper sounds and lets the server send wool
  instead — targeted at only the donor's three sounds. Side effect: every copper-material block
  becomes server-authoritative for step/hit/fall (still copper, just server-driven, ~one ping of
  latency). Needs the resource pack (already required).
- **Performance:** one display entity per placed block. Fine for normal builds; very large/dense
  wool structures add client entity load. (The cost of doing all 16 colors faithfully.)
- **The one thing to eyeball in-game — stair orientation.** Stair rotation is applied at runtime
  (`WoolStairsBlock.stairRotation`, a quaternion that reproduces vanilla `oak_stairs.json` (x,y),
  unit-verified for all 40 variants). The display math is sound, but if a placed stair faces wrong,
  a corner looks twisted, or a top (upside-down) stair renders normal, the fix lives in that one
  method (or a single base correction `setLeftRotation` in `WoolBackport.WoolDisplayHolder`).
  Everything else (size/centering/void/placement) is fixed and verified.

## Regenerating assets

All models/item-assets/recipes/lang are generated (no hand-edited JSON, no PNGs — models reuse the
existing vanilla wool textures):

```sh
python3 tools/gen_assets.py
```
