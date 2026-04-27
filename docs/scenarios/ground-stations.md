# `ground_stations` — receiving network

The `ground_stations` block defines the pool of ground stations available to **every** team. There is no per-team ground network — every station is shared. It maps to `FGroundStationsDefinition` in `studio/Plugins/SpaceRange/Source/SpaceRange/Public/Definitions/GroundStationsDefinition.h`.

```json
"ground_stations": {
  "locations": [
    "Madrid", "Dubai", "Singapore", "Auckland",
    "Easter Island", "Salvador", "Miami"
  ],
  "min_elevation": 0,
  "max_range":     0,
  "scale":         100
}
```

## Fields

| Key | JSON type | Default | Description |
| --- | --- | --- | --- |
| `locations` | `string[]` | _(empty)_ | City names. Each one matches an entry in Studio's built-in city table and instantiates a ground station at that city's coordinates. Duplicates are allowed but pointless. |
| `min_elevation` | `number` (deg) | `0` | Minimum elevation above the local horizon for a station to be considered "in view" of a spacecraft. `0` means at-the-horizon counts; `5–10` is realistic for masking effects. |
| `max_range` | `number` (km) | `0` | Maximum slant range over which a link can close. `0` means unlimited (link budget alone gates it). Use a finite value to cut off pathologically long links explicitly. |
| `scale` | `number` | `100` | Visual scale factor for ground-station markers in the world view. Doesn't affect simulation, only rendering. |

## Notes

- The first station in `locations` is treated specially: the per-team ground controllers are attached to it and inherit its default transmitter power, antenna gain, and bandwidth. Pick the most "central" or "primary" station as the first entry.
- Whether a spacecraft can talk to a station at runtime is gated by the link budget plus `min_elevation` and `max_range`. Teams choose which station to communicate with operationally — typically by setting [`guidance` mode](../api-reference/spacecraft-commands.md#guidance) to `"ground"` and pointing the antenna at the station of interest.
- Ground stations are **not** owned by teams — every team can request a downlink through any station whose link budget closes. To force a team to use a particular station, control it through scenario narrative (briefing, scoring) rather than configuration.

## Picking locations

Studio ships with a comprehensive city table — most major capitals and many secondary cities are available. The shipped scenarios use these patterns:

- **Global coverage** (`Orbital Sentinel`): seven well-spread stations so every spacecraft has a close contact. `Madrid`, `Dubai`, `Singapore`, `Auckland`, `Easter Island`, `Salvador`, `Miami`.
- **Regional coverage** (`Docking_Procedure`): a hemisphere-biased cluster for an exercise focused on a particular orbit. `Paris`, `Dubai`, `Colombo`, `Singapore`, `Sydney`, `Auckland`, `Lima`, `New York`.
- **Polar coverage** (`Telemetry_Drop`): includes `Amundsen-Scott` so that polar-orbit spacecraft are visible at most points of their orbit.

If a city name is not recognised, Studio logs a warning and skips it during load. Confirm the loaded set with [`admin_list_entities`](../api-reference/admin-requests.md#admin_list_entities) after a load.
