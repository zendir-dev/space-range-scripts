# `objects.space[]` — passive orbital objects

The `objects.space[]` array defines passive space objects — bare spacecraft placed in orbit (or at a fixed geodetic location) that have **no controller and no components** attached. They are just objects in space: debris, spent rocket bodies, defunct satellites, or visual markers. Space objects do not generate telemetry, cannot be commanded, and are not part of the team configuration.

Each entry is loaded when the scenario starts.

```json
{
  "name":         "Defunct Satellite",
  "orbit":        [7800.0, 0.01, 51.6, 90.0, 0.0, 0.0],
  "planet":       "Earth",
  "dynamic_type": "Orbit",
  "attitude":      [0.0, 0.0, 0.0],
  "attitude_rate": [0.0, 0.0, 0.0],
  "mesh":         "/ZendirAssetsSpace/Blueprints/Spacecraft/ZenSat/BP_Z_SC_ZenSat_Chassis",
  "scale":        1.0,
  "color":        "#FFFFFF",
  "reflectivity": 0.5
}
```

## Fields

| Key | JSON type | Default | Description |
| --- | --- | --- | --- |
| `name` | `string` | `"Space Object"` | Display name surfaced by admin tools. |
| `orbit` | `number[6]` | `[0,0,0,0,0,0]` | Keplerian elements `[semi-major axis (km), eccentricity, inclination (deg), RAAN (deg), argument of periapsis (deg), true anomaly (deg)]`. Used when `geodetic` is absent. |
| `geodetic` | `number[3]` | _(unset)_ | Fixed `[latitude (deg), longitude (deg), altitude (m)]`. **Optional** and **mutually exclusive** with `orbit` — when present it takes precedence and the object is positioned by LLA instead of orbital elements. |
| `planet` | `string` | `"Earth"` | Body the object orbits. Accepts `"Earth"`, `"Moon"`, `"Mars"`. |
| `dynamic_type` | `string` | `"Orbit"` | Motion model. One of `Orbit` (fixed Keplerian propagation), `Static` (frozen position/attitude), `Integration` (full dynamics), `Lookup` (table-driven). Case-insensitive. |
| `attitude` | `number[3]` (deg) | `[0,0,0]` | Initial body attitude as **1-2-3 Euler angles**. Applied at spawn via `SetAttitude` (converted to MRP internally). |
| `attitude_rate` | `number[3]` (deg/s) | `[0,0,0]` | Initial body angular rate in the **body frame**. Applied at spawn via `SetAttitudeRate` (converted to rad/s internally). Useful for tumbling debris. |
| `mesh` | `string` | `"none"` | Visual mesh. Either a static-mesh name or the full path to a Blueprint physical-object class used as the chassis. `"none"` (or empty) leaves the object with no visual mesh. |
| `scale` | `number` | `1.0` | Visual scale factor applied to the mesh. |
| `color` | `string` (hex) | `"#FFFFFF"` | Hex RGB. Accepts `#RRGGBB` or `#RGB`. |
| `reflectivity` | `number` | `0.5` | How reflective the object material is (`0.0`–`1.0`). Left at the default the material properties are untouched; any other value is applied at load via `SetMaterialProperties`. Feeds sensor models such as optical / radar detection. |
| `trackable` | `boolean` | `true` | When `true`, the object is broadcast to every team's operator UI as a selectable [relative-pointing](../api-reference/spacecraft-commands.md#relative) target (in the `trackable[]` list of [`list_assets`](../api-reference/ground-requests.md#list_assets)). Set `false` to keep an object in the scene but hidden from targeting. |

## Positioning: `orbit` vs `geodetic`

A space object is positioned **either** from orbital elements **or** from a geodetic coordinate — never both:

- Provide `orbit` (6 doubles) for an object that follows an orbit.
- Provide `geodetic` (3 doubles) for an object pinned above a lat/lon at a given altitude. When `geodetic` is present, `orbit` is ignored.

Pair `geodetic` with `dynamic_type: "Static"` for a marker that stays put, or with `dynamic_type: "Orbit"` to seed a circular orbit at that altitude.

## Notes

- Space objects are passive: no controller, no components, no telemetry. They exist to populate the scene (debris fields, rendezvous/inspection targets, visual references).
- `Orbit` is the natural default — the object coasts along its Keplerian orbit without integrating perturbations.
- Choose distinct `color` values so objects can be referred to by colour in imagery or inspection exercises.
- Space objects are **trackable by default**, so they show up in the operator UI as relative-pointing targets. Because they have no components, the "Aim Component" option resolves to `None` (pointing at the object's centre). Set `trackable: false` to hide one from targeting.

## Example cluster

A small debris field trailing/leading a main spacecraft, plus a fixed geostationary marker:

```json
"objects": {
  "space": [
    { "name": "Debris Alpha", "orbit": [7500.0, 0.0, 45.0, 220.0, 0.0, 82.0],
      "planet": "Earth", "dynamic_type": "Orbit", "color": "#FF0000" },
    { "name": "Debris Beta", "orbit": [7500.0, 0.0, 45.0, 220.0, 0.0, 78.0],
      "planet": "Earth", "dynamic_type": "Orbit", "color": "#FF7000" },
    { "name": "Spent Rocket Body", "orbit": [9200.0, 0.12, 63.4, 45.0, 270.0, 120.0],
      "planet": "Earth", "dynamic_type": "Orbit",
      "mesh": "/ZendirAssetsSpace/Blueprints/Spacecraft/ZenSat/BP_Z_SC_ZenSat_Chassis",
      "scale": 2.0, "color": "#808080" },
    { "name": "Fixed Geo Marker", "geodetic": [0.0, 150.0, 35786000.0],
      "planet": "Earth", "dynamic_type": "Static", "color": "#00FF00" }
  ]
}
```
