# `universe` — environment toggles

The `universe` block toggles environment systems and tunes a few visual parameters. It maps to `FUniverseDefinition` in `studio/Plugins/SpaceRange/Source/SpaceRange/Public/Definitions/UniverseDefinition.h`, parsed by `UniverseDefinitionFromJson` in `SpaceRangeDefinitionFunctionLibrary.cpp`.

```json
"universe": {
  "atmosphere":     false,
  "magnetosphere":  true,
  "gps":            true,
  "cloud_opacity":  0.9,
  "cloud_contrast": 2.5,
  "ambient_light":  0.25
}
```

## Fields

| Key | JSON type | Default | Description |
| --- | --- | --- | --- |
| `atmosphere` | `bool` | `false` | If `true`, atmospheric drag is applied to spacecraft and atmospheric scattering is rendered. Off by default at typical operating altitudes (≥ 700 km). Turn on for low-perigee or re-entry scenarios. |
| `magnetosphere` | `bool` | `true` | If `true`, Earth's magnetic field is modelled. Affects `Magnetometer` telemetry and any magnetorquer-style components. Set `false` to disable magnetic-field effects entirely. |
| `gps` | `bool` | `true` | If `true`, the `GPS Sensor` returns valid fixes. Set `false` to model a globally GPS-denied scenario (every spacecraft's GPS sensor returns no fix). For partial / regional GPS denial use a `GPS` event instead — see [events.md#gps-events](events.md#gps-events). |
| `cloud_opacity` | `number` `0.0–1.0` | `0.7` | Opacity of the rendered cloud layer. `0.0` = clear sky, `1.0` = solid cloud cover. Affects how Earth imagery looks from the camera. |
| `cloud_contrast` | `number` | `2.5` | Contrast applied to the cloud layer. Typical values are `1.0–3.0`. Higher values emphasise cloud structure. |
| `ambient_light` | `number` `0.0–1.0` | `0.25` | Scene ambient light. Higher values brighten dark sides for visualisation; **does not** affect physics or solar-panel power generation. |

## Notes

- These flags change the *experience* of the scenario — they do not change command/telemetry semantics. The same uplink commands and downlink packets are emitted regardless of `cloud_opacity` or `ambient_light`.
- `gps: false` is **global**. To disable GPS only over a region, leave `gps: true` and add a `GPS` event with `Type: "Spoofing"` (see [events.md#gps-events](events.md#gps-events)).
- The cloud and ambient-light values are only meaningful if the scenario uses `Camera` or `Optical Camera` components — they're rendered by Unreal but never read by simulation code.

## Picking values, in practice

- **Low-altitude or re-entry exercise**: `atmosphere: true`. Otherwise leave it `false`.
- **Counter-piracy / maritime imagery exercise**: `cloud_opacity: 0.6–0.9`, `cloud_contrast: 2.0–2.5` for natural-looking imagery; `ambient_light: 0.20–0.30` so dark hemispheres are still visible to teams.
- **Magnetic-field-aware exercise**: `magnetosphere: true` (the default). Most scenarios leave this on.
- **GPS-denied exercise**: `gps: false` for global denial; otherwise `true` plus a regional `GPS` event.
