# `simulation` — clock & solver

The `simulation` block sets the simulation time origin, how fast simulated time runs by default, and what integrator advances the dynamics. It maps to `FSimulationDefinition` in `studio/Plugins/SpaceRange/Source/SpaceRange/Public/Definitions/SimulationDefinition.h`, parsed by `SimulationDefinitionFromJson` in `SpaceRangeDefinitionFunctionLibrary.cpp`.

```json
"simulation": {
  "epoch":      "2026/04/15 07:30:00",
  "speed":      5.0,
  "step_size":  0.12,
  "integrator": "Euler",
  "end_time":   0.0
}
```

## Fields

| Key | JSON type | Default | Description |
| --- | --- | --- | --- |
| `epoch` | `string` (UTC) | _(required for time-dependent exercises)_ | Wall-clock UTC the simulation starts at. Format `YYYY/MM/DD HH:MM:SS`. Drives sun position, Earth rotation, ground tracks, and any time-of-day effects. |
| `speed` | `number` | `1.0` | Default `simulation_speed` (sim seconds per real second). Instructors can change this at runtime via [`admin_set_simulation`](../api-reference/admin-requests.md#admin_set_simulation). |
| `step_size` | `number` (sim s) | `0.1` | Integrator step. Smaller = more accurate dynamics, more CPU. `0.10–0.20` is the typical band. Below `0.05` is rarely useful for the kind of orbits Space Range models. |
| `integrator` | `string` | `"Euler"` | Numerical integrator. Accepts `"Euler"` or `"RK4"` (case-insensitive). Use `RK4` if a scenario depends on multi-orbit propagation accuracy (rendezvous, formation, long-duration manoeuvres); `Euler` is fine otherwise. |
| `end_time` | `number` (sim s) | `0.0` | Hard stop in sim seconds. `0.0` means "run forever / until reset". A non-zero value will stop the simulation when reached. |

## Notes

- `epoch` is parsed by `UJSONLibrary::GetDateTimeValue`, which accepts the `YYYY/MM/DD HH:MM:SS` format used in every shipped scenario. Other Unreal-supported `FDateTime` formats also parse.
- `speed`, `step_size`, and `end_time` are doubles internally. Whole-number values are fine without a decimal point but the convention in shipped scenarios is to write them as floats (`5.0` rather than `5`).
- `integrator` is converted to lower-case before comparison; only `rk4` selects RK4. Anything else falls back to Euler.
- `simulation` is loaded *first* during scenario load, so any clock-dependent setup elsewhere in the file (e.g. event `Time` values, sun-angle-based imagery exercises) sees this clock.

## Picking values, in practice

- For tutorial / first-flight scenarios: `speed: 1.0`, `step_size: 0.1`, `integrator: Euler`. The clock matches real time; nothing's surprising.
- For competition scenarios that span hours of mission time: `speed: 5.0` to `10.0`, `step_size: 0.10–0.15`, `integrator: Euler`.
- For orbit-precision scenarios (formation flying, rendezvous): `step_size: 0.05–0.10`, `integrator: RK4`. The CPU cost is real but worth it for the accuracy.
- `end_time` is most useful as a safety net for unattended demos. For instructor-led exercises, leave it `0.0` and stop manually.
