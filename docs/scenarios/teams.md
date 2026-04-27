# `teams[]` — units of identity

Each entry in `teams[]` is one team in the scenario. The order doesn't matter; the IDs do. Each team maps to one `FTeamConfig` (`studio/Plugins/SpaceRange/Source/SpaceRange/Public/Structs/TeamConfig.h`), parsed by `TeamConfigFromJson`.

```json
"teams": [
  {
    "enabled":    true,
    "id":         111111,
    "password":   "AB12CD",
    "name":       "Red Team",
    "key":        17,
    "frequency":  500,
    "collection": "RED",
    "color":      "#FF366A"
  }
]
```

## Fields

| Key | JSON type | Default | Description |
| --- | --- | --- | --- |
| `enabled` | `bool` | `true` | If `false`, the team is parsed but not instantiated (no ground controller, no MQTT credentials, no downlink). Useful for keeping inactive teams in the file for later. |
| `id` | `integer` | _(required)_ | Numeric team ID. Used in MQTT topic paths (`<GAME>/<ID>/...`) and in the `team_id` field of every event. **Must be unique** within the scenario. |
| `password` | `string` | _(required)_ | 6-character alphanumeric XOR password. **Must be unique** per team. Teams use this to encrypt their MQTT traffic — see [Encryption](../concepts/encryption.md). |
| `name` | `string` | _(required)_ | Display name (`"Red Team"`, `"Blue Team"`). Used by the Operator UI, admin tools, and ground-controller responses. |
| `key` | `integer` `0–255` | `0` | Initial Caesar key. Teams can rotate this at runtime via [`encryption`](../api-reference/spacecraft-commands.md#encryption). |
| `frequency` | `number` (MHz) | `0` | Initial RF carrier frequency. Pick distinct values per team to avoid cross-talk. The shipped scenarios spread teams across `468–901 MHz`. |
| `collection` | `string` | `""` | Name of an entry in [`assets.collections`](spacecraft.md#collections) listing the spacecraft this team controls. Empty = no spacecraft. Must match an `id` in `assets.collections[]`. |
| `color` | `string` (hex) | `"#FFFFFF"` | Hex RGB. Used for ground tracks, asset markers, plot colours, and OperatorUI accents. Accepts `#RRGGBB` or `#RGB`. |

## Notes

- Teams can share a `collection` to share spacecraft, though that is rare in practice and complicates Q&A scoring.
- Multiple teams can use the same `key` (Caesar key); it's per-team-scoped at the RF layer, so collisions don't cause cross-decryption.
- `password` is the **strong** layer (XOR per byte against the password); don't reuse passwords between teams. The Caesar `key` is the weak layer used for over-the-air RF and is intended to be visible to anyone with an [`EM Sensor`](components.md#electromagnetic-sensor).
- The number of teams is not bounded by the simulation, but practical exercises rarely exceed 12. Each team adds a ground controller, an MQTT credential set, and per-team telemetry bandwidth.

## Authoring rules of thumb

- **IDs**: small round numbers (`111111`, `222222`) are fine for tutorials. For competition / multi-event use, prefer larger random IDs to reduce muscle-memory mistakes.
- **Passwords**: random 6-character alphanumeric. The Operator UI accepts the team password as the secret to log in, so make them unguessable.
- **Frequencies**: spread across the band. Closer-spaced frequencies (within ~10 MHz) make jamming exercises more interesting; widely-spaced frequencies make accidents less likely. Two-team scenarios often use `473` and `474` (next-door); large competitions spread across `~430` MHz of the RF band.
- **Colors**: use distinct hues. Teams identify each other by colour in the Operator UI, on plot lines, and on ground tracks. Avoid two teams with similar shades (e.g. `#00CED1` and `#00FFFF`).
- **Collections**: keep collection names descriptive (`Main`, `Red`, `Rogue`, `Hub`) — they appear in admin tools.

## Example: a multi-team competition team list

From `Orbital Sentinel`:

```json
"teams": [
  { "enabled": true, "id": 212997, "password": "2EM6DF", "name": "Rogue",       "key":   1, "frequency": 500, "collection": "Rogue", "color": "#FF0000" },
  { "enabled": true, "id": 584203, "password": "Q7X9PL", "name": "Team Blue",   "key":  42, "frequency": 612, "collection": "Main",  "color": "#020CF1" },
  { "enabled": true, "id": 917462, "password": "M3K8ZT", "name": "Team Green",  "key":  87, "frequency": 745, "collection": "Main",  "color": "#00FF00" },
  { "enabled": true, "id": 263891, "password": "X9L2QA", "name": "Team Yellow", "key": 154, "frequency": 889, "collection": "Main",  "color": "#FFFF00" }
]
```

Note how the `Rogue` team has its own collection (a single rogue spacecraft) while every other team shares the `Main` collection (the same defender spacecraft, viewed from different identities). This is the standard "constructive-agent" shape — see the recipes in [recipes.md](recipes.md).
