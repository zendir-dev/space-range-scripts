# Session Information Schema

The scenario, when running, will consistently output data over a particular topic for any entity to listen to. This will include the simulation time, epoch and instance information about the current session. This data is outputted **3** times every real-time second of simulation run. It requires no actioning and no response from any entity and will publish as long as the simulation is running.

### MQTT Topic

The MQTT topic is defined by:

```json
Zendir/SpaceRange/**[GAME]**/Session
```

where **`[GAME]`** is the name of the game defined by the simulation scenario.

### Encryption

This data is **not** encrypted. Since the data contains no information about team data, it is only published in ASCII format with the specific schema defined below every 0.3 seconds, while the simulation is running within the scenario.

### Schema

Each command is structured with the following JSON packet:

```json
{
	"time": 32.5
	"utc": "2026/01/26 13:23:13",
	"instance": 10234141
}
```

| **Property** | **Description** |
| --- | --- |
| time | The current simulation time of the scenario in simulation seconds. This is not the real-time of the scenario but rather the time elapsed from 0. |
| utc | The current UTC time of the simulation, fetched from the simulation data. This is based on the solar system epoch and the simulation time is added. |
| instance | A unique instance number of the simulation. This is generated each time the scenario is run. When the scenario is restarted, the instance number will change. This can be used to detect the scenario has restarted and for all the data to be cleared and refreshed for a new scenario run. |