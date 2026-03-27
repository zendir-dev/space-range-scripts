# Teams Configuration Schema

This document describes the structure of the team configuration used to define game instances and team configurations for Space Range scenarios.

## File Location

Team configuration is now embedded directly within each scenario's JSON file, located at:

```
scenarios/<scenario_name>.json
```

See the [scenario file](../scenarios/orbit_sentinel.json) for a full example.

## Schema

The `teams` array within a scenario JSON file follows this structure:

```json
{
    "teams": [
        {
            "enabled": true,
            "id": 111111,
            "password": "AAAAAA",
            "key": 6,
            "frequency": 473,
            "color": "#FF0000",
            "name": "Red Team",
            "collection": "RED"
        }
    ]
}
```

---

## Team Object Properties

Each team object within the `teams` array contains the following properties:

| **Property** | **Type** | **Default** | **Description** |
| --- | --- | --- | --- |
| enabled | boolean | `true` | Whether the team is active in the current scenario. Disabled teams will not be able to send or receive commands. |
| id | integer | | The unique numeric identifier for the team. This ID is used in MQTT topics and must match the `id` field in spacecraft commands for execution. |
| password | string | | A 6-character alphanumeric password used for XOR encryption of commands sent to the spacecraft. Each team has a unique password known only to that team and instructors. |
| key | integer | | The Caesar cipher key (0–255) used for telemetry encryption between the spacecraft and ground station. This rotates bytes in communication packets. |
| frequency | integer | | The communication frequency in MHz for the team's uplink and downlink channels. Teams should use distinct frequencies to avoid interference. |
| color | string | | A hex color code (e.g., `#FF0000`) used for visual identification of the team in the Space Range interface. |
| name | string | | A human-readable display name for the team (e.g., `"Red Team"`, `"Blue Team"`). |
| collection | string | `""` | The ID of the asset collection assigned to this team. Collections define which space assets the team controls. The collection ID must match an entry in the `assets.collections` array of the scenario file. If empty, the team has no assigned assets. |

---

## Collections

Asset collections are defined in the `assets.collections` array of the scenario JSON and link teams to their controllable spacecraft. Each team's `collection` field must reference a valid collection `id`.

```json
"assets": {
    "collections": [
        {
            "id": "Main",
            "space_assets": ["SC_001"]
        },
        {
            "id": "RED",
            "space_assets": ["SC_002"]
        }
    ]
}
```

| **Property** | **Type** | **Description** |
| --- | --- | --- |
| id | string | The unique identifier for the collection. Referenced by the `collection` field on each team object. |
| space_assets | array | A list of space asset IDs (matching entries in `assets.space`) that belong to this collection and are therefore controllable by the assigned team. |

---

## Example Configuration

A complete example with two teams and their collection assignments:

```json
{
    "teams": [
        {
            "enabled": true,
            "id": 111111,
            "password": "AAAAAA",
            "key": 6,
            "frequency": 473,
            "color": "#FF0000",
            "name": "Red Team",
            "collection": "RED"
        },
        {
            "enabled": true,
            "id": 222222,
            "password": "BBBBBB",
            "key": 7,
            "frequency": 474,
            "color": "#00AAFF",
            "name": "Blue Team",
            "collection": "Main"
        }
    ],
    "assets": {
        "space": [
            { "id": "SC_001", "name": "Microsat" },
            { "id": "SC_002", "name": "Recon" }
        ],
        "collections": [
            { "id": "Main", "space_assets": ["SC_001"] },
            { "id": "RED",  "space_assets": ["SC_002"] }
        ]
    }
}
```

---

## Security Considerations

- **Team Passwords**: Each team's `password` field is used for XOR encryption of spacecraft commands. These should be kept confidential and not shared between teams.
- **Frequency Separation**: Teams should be configured with different `frequency` values to prevent cross-talk and interference. If frequencies overlap, teams may need to update their telemetry configuration using the `telemetry` command.
- **Key Values**: The `key` field provides an additional layer of encryption via Caesar cipher. If a team suspects their key has been compromised, they can update it using the spacecraft's telemetry command.
