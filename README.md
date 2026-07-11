# Wool Stairs & Slabs Backport

Server-side backport of Minecraft 26.3's wool stairs and slabs (all 16 colors) to 26.2, built with [Polymer](https://polymer.pb4.eu) + Fabric. Players need **only a resource pack** (for the shapes) — no client mod. Names, drops, recipes and shears-mining all work server-side. Designed to vanish the moment 26.3 ships: the blocks use their native `minecraft:` ids, so world data is identical and native takes over with zero migration.

## Requirements

- A Fabric 26.2 server
- **Fabric API**
- **Polymer**

## Install

1. Drop the jar into the server's `mods/` folder (alongside Fabric API and Polymer).
2. Make the generated resource pack reach players (it's marked **required**). Easiest path —
   the bundled **autohost** serves it automatically; enable it once in
   `config/polymer/auto-host.json`:
   ```json
   { "enabled": true }
   ```
   (Behind a proxy, also set `"forced_address"`.) Alternatively run `/polymer generate-pack`
   and serve `polymer/resourcepack.zip` yourself via `resource-pack` in `server.properties`.
3. Players accept the pack on join and see proper wool stairs/slabs. Craft them with the usual patterns.

## When 26.3 arrives

The blocks are real `minecraft:<color>_wool_stairs` / `_slab`, so existing builds load **natively** with no conversion. The mod also refuses to load on 26.3 (`"minecraft": ">=26.2 <26.3"`), and even if forced it no-ops when the ids already exist. Just delete the jar.

## In Memory of Apollo

This mod was created because we wanted to make a statue of our dog Apollo, who recently passed away.
Our server runs some light mods but is 100% vanilla-client compatible so we couldn't use some of the other mods that backport wool stairs and slabs.
