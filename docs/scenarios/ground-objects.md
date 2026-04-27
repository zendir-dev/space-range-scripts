# `objects.ground[]` — ground decorations

The `objects.ground[]` array defines passive ground actors — vessels, text labels, and any other object placed at a lat/lon. Ground objects do not generate telemetry, cannot be commanded, and are not part of the team configuration. They exist to give imagery and EM-sensor exercises something realistic to find.

Each entry maps to `FGroundObjectDefinition` (`studio/Plugins/SpaceRange/Source/SpaceRange/Public/Definitions/GroundObjectDefinition.h`), parsed by `GroundObjectDefinitionFromJson`.

```json
{
  "id":        "GO_001",
  "type":      "vessel",
  "name":      "EG01",
  "planet":    "Earth",
  "latitude":  12.1,
  "longitude": 44.2,
  "altitude":  1,
  "scale":     120,
  "color":     "#00FF00",
  "data":      { "heading": 76.0, "speed": 10.0 }
}
```

## Fields

| Key | JSON type | Default | Description |
| --- | --- | --- | --- |
| `id` | `string` | _(required)_ | Unique identifier within the scenario. |
| `type` | `string` | `"text"` | One of `vessel`, `text` (case-insensitive). Selects the actor class. |
| `name` | `string` | `""` | Display name surfaced by admin tools. |
| `planet` | `string` | `"Earth"` | Body the object sits on. Accepts `"Earth"`, `"Moon"`, `"Mars"`. |
| `latitude` | `number` (deg) | `0.0` | Geodetic latitude (`-90` to `+90`). |
| `longitude` | `number` (deg) | `0.0` | Geodetic longitude (`-180` to `+180`). |
| `altitude` | `number` (m) | `0.0` | Altitude above the surface. `1` is fine for vessels (sits on the water); larger values lift the object visibly above the ground. |
| `scale` | `number` | `1.0` | Visual scale factor. Vessel meshes are small at scale `1` — typical values are `60–225`. |
| `color` | `string` (hex) | `"#FFFFFF"` | Hex RGB. For vessels this is the hull colour; for text this is the glyph colour. Accepts `#RRGGBB` or `#RGB`. |
| `data` | `object` | `{}` | Type-specific values — see below. |

## Type-specific `data`

Vessel and text have different `data` keys (parsed in `SpaceRangeDefinitionFunctionLibrary.cpp` lines 1143–1166).

### `type: "vessel"`

A surface ship (or generic moving ground object) that travels on a heading.

| `data` key | Type | Default | Description |
| --- | --- | --- | --- |
| `heading` | `number` (deg) | `0.0` | Compass heading (`0` = north, `90` = east, etc.). |
| `speed` | `number` (m/s) | `0.0` | Constant speed along the heading. `0.0` makes the vessel stationary — useful for representing damaged or moored ships. |
| `em_gain` | `number` (dB) | `0.0` | EM emission strength. Set non-zero to make the vessel detectable by an `EM Sensor`. |
| `em_frequency` | `number` (MHz) | `0.0` | EM emission centre frequency. Required if `em_gain` is non-zero. |

### `type: "text"`

A flat text glyph rendered on the ground at the given lat/lon. Used as a label or marker.

| `data` key | Type | Default | Description |
| --- | --- | --- | --- |
| `text` | `string` | `""` | The glyph string to render. Tiny strings (`","`, `"X"`) render as visual markers; longer strings act as captions. |

## Notes

- Ground objects are passive: they do not respond to commands and emit no telemetry beyond the optional EM signature on a vessel.
- Vessels move in **constant-heading** straight lines on the planet's surface — they don't follow shipping lanes or avoid land. If you need a vessel to follow a path, place it at multiple waypoints at different `Time` events using a scripted scenario, or simply pick `speed: 0` and treat the vessel as stationary.
- For dense scenes (`Orbital Sentinel` has 22 vessels), keep `id` values monotonic (`GO_001`, `GO_002`, …) so they sort sensibly in admin tools.
- Color choices matter for imagery exercises — choose distinct hues so teams can refer to vessels by colour in Q&A. Avoid placing two same-colored vessels close together unless this ambiguity is the exercise.

## Example clusters

A small fleet representing a shipping lane (from `Orbital Sentinel`):

```json
{ "id": "GO_001", "type": "vessel", "name": "EG01", "planet": "Earth",
  "latitude": 12.1, "longitude": 44.2, "altitude": 1,
  "scale": 120, "color": "#00FF00",
  "data": { "heading": 76.0, "speed": 10.0 } },
{ "id": "GO_002", "type": "vessel", "name": "EG02", "planet": "Earth",
  "latitude": 11.5, "longitude": 44.2, "altitude": 1,
  "scale": 120, "color": "#00FF00",
  "data": { "heading": 86.0, "speed": 10.0 } },
{ "id": "GO_005", "type": "vessel", "name": "EG05", "planet": "Earth",
  "latitude": 13.6, "longitude": 43.0, "altitude": 1,
  "scale": 120, "color": "#00FF00",
  "data": { "heading": 178.0, "speed": 0.0 } }
```

A text marker for a region of interest:

```json
{ "id": "TX_01", "type": "text", "name": "tx01", "planet": "Earth",
  "latitude": 16.2, "longitude": 112.0, "altitude": 3,
  "scale": 160000, "color": "#011A01",
  "data": { "text": "," } }
```

A vessel that emits an EM signature an `EM Sensor` can detect:

```json
{ "id": "GO_BEACON", "type": "vessel", "name": "Beacon", "planet": "Earth",
  "latitude": 0.0, "longitude": 0.0, "altitude": 1,
  "scale": 120, "color": "#FFFFFF",
  "data": { "heading": 0.0, "speed": 0.0, "em_gain": 30.0, "em_frequency": 600.0 } }
```
