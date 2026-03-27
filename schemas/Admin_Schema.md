# Admin Schema

Space Range provides a set of **admin commands** that allow authorized users to retrieve data from the Space Range server. These commands are intended for **instructors** and **constructive agents**, not for participant teams.

Using these admin commands, instructors and agents can:

- Retrieve information about the simulation state
- Monitor team performance and progress
- Access scenario-level and system data

The system operates using a **request–response messaging model**:

- Data requests are published to a designated **request topic**
- Responses are returned on a corresponding **response topic**

Each simulation session has **one shared request topic and one shared response topic**. These topics are **session-wide** and are **not associated with individual teams**. This document lists and describes all admin commands available to the admin controller.

### MQTT Topics

The MQTT **request** topic is defined by:

```json
Zendir/SpaceRange/**[GAME]**/Admin/Request
```

where **`[GAME]`** is the name of the game defined by the simulation scenario.

The MQTT **response** topic is defined by:

```json
Zendir/SpaceRange/**[GAME]**/Admin/Response
```

where **`[GAME]`** is the name of the game defined by the simulation scenario.

### Encryption

Each command communicated over the **MQTT** topic is encrypted by a 6-character **alphanumeric** password using **XOR** encryption. The password for the admin controls is designated and generated at the beginning of the scenario. It must not be known by any of the teams and should not be shared, as it provides access to all team information. It is not discoverable by other teams (without cheating). Using this password, the data must be encrypted using this method. The XOR decryption has the same operation for encrypting and decrypting the data with the same **string key**. A sample piece of encryption code may look like the following:

```jsx
// Convert the password into bytes, assuminmg 'data' is already in a byte array
const encoder = new TextEncoder();
const passwordBytes = encoder.encode(password);

// Create an empty array ready to be encrypted, at the length of the 'data'
const encryptedData = new Uint8Array(data.length);

// Encrypt the data using the XOR method with the password
for (let i = 0; i < data.length; ++i) {
    encryptedData[i] = data[i] ^ passwordBytes[i % passwordBytes.length];
}

// The final data is encrypted using the password
return encryptedData;
```

### Schema

Each request is structured with the following JSON packet:

```json
{
	"type": "x",
	"req_id": 0,
	"args": {
		"arg_1": "x",
		...
	}
}
```

| **Property** | **Description** |
| --- | --- |
| type | The request type to send through. This will determine what kind of request  and response is executed. This document outlines each of the requests in more detail, including the required arguments needed. |
| req_id | This is the ID of a request as a number. This can be any number and can be repeated. The **response** will return back a response with this same ID so that that it can be tracked correctly and handled. The ID can be designated by the sender and it can be left as 0 if not required. |
| args | A list of arguments that are applied to each request. Each command may require additional arguments to process the commands. They are outlined in each of the tables below. The arguments are a dictionary of key-value pairs. |

Once the request has been made and fulfilled, the server will respond to the request on the **response** topic. It will look like the following JSON packet sent over the response MQTT topic:

```json
{
	"type": "x",
	"req_id": 0,
	"args": {
		"arg_1": "x",
		...
	},
	"success": true,
	"error": ""
}
```

| **Property** | **Description** |
| --- | --- |
| type | This is the same command type designated in the **request** packet. |
| req_id | The request ID is the same ID as designated in the **request** packet. It will not change - useful for matching a response with a certain request. |
| args | A list of data arguments provided by the space range server. This is the information inside the result of the request and is stored as a dictionary of key-value pairs. Each response will have a different set of arguments that it will return. |
| success | This will be either **true** or **false**. If true, then the request succeeded correctly. If **false**, then there was an error when the request was attempted. If **false**, then the **error** message will appear. |
| error | This property will only show if the **success** flag is **false**. If so, the **error** will show information about what was incorrect about the request, if possible. |

---

## List Entities

**Command**: `admin_list_entities`

**Description:** 
This request can be used to return a list of all entities within the simulation, including all teams and all ground station names. This will not change during scenario runtimes but can be used to fetch the information at the beginning of a session.

### Request

```json
{
	"type": "admin_list_entities",
	"req_id": 0
}
```

*There are no arguments to be passed into this command.*

### Response

```json
{
	"type": "admin_list_entities",
	"req_id": 0,
	"args": {
		"teams": [
			{
				"name": "Red Team",
				"id": 10,
				"password": "AAAAAA",
				"color": "#FF366A"
			},
			...
		],
		"stations": [
			{
				"name": "Singapore",
				"latitude": 1.35,
				"longitude": 103.82,
				"altitude": 16.0
			},
			...
		]
	},
	"success": true
}
```

| **Argument** | **Description** |
| --- | --- |
| teams | A list of all teams present within the simulation. This will be a list of dictionaries containing key-value pairs of each of the data associated to a particular team. This includes the **name** of the team, the **ID** of the team and the **password** of the team. The **color** is the hexadecimal color that identifies the team information. |
| stations | A list of all stations present within the scenario. This will be a list of dictionaries containing key-value pairs of each ground station. They will include the **latitude**, in degrees, the **longitude**, in degrees, the **altitude**, in meters and the **name** of the ground station. |

---

## List Team

**Command**: `admin_list_team`

**Description:** 
This request can be used to return a list of all entities within the simulation, including all teams and all ground station names. This will not change during scenario runtimes but can be used to fetch the information at the beginning of a session.

### Request

```json
{
	"type": "admin_list_team",
	"req_id": 0,
	"args": {
		"team": "Red Team"
	}
}
```

| **Argument** | **Description** |
| --- | --- |
| team | The name of the team to fetch information from. This is case-insensitive and must match the name and not the ID of the team. |

### Response

```json
{
	"type": "admin_list_team",
	"req_id": 0,
	"args": {
		"name": "Red Team",
		"id": 10,
		"password": "AAAAAA",
		"color": "#FF366A",
		"assets": {
			"space": [
				{
					"asset_id": "fb345a0c",
					"name": "Microsat",
					"rpo_enabled": true,
					"components": [
						{
							"name": "Solar Panel +X",
							"class": "Solar Panel",
							"component_id": 5,
							"is_imager": false
						},
						...
					]
				},
				...
			]
		}
	},
	"success": true
}
```

| **Argument** | **Description** |
| --- | --- |
| name | The name of the team found in the entity. This should match the team name found in the request. |
| id | The unique ID of the team which can be used for sending commands to the team. This is defined by the scenario and cannot change during the simulation. |
| password | The alphanumeric (usually 6 character) password that the teams use to control and read data from their spacecraft. This is defined by the scenario and cannot change during the simulation. |
| color | The hexa-decimal color, in the RGB format, of the team. This can be useful for identifying which team is present and useful for plotting values. |
| assets | A list of all assets associated with the team. This can include space and ground assets. Each team may have one or many assets that can be controlled and configured. This will list each one and the properties associated with it. |
| space | A subset of the assets that are space-bound. These are spacecraft of forms and are able to communicated with via the team information. |
| asset_id | The asset ID of the spacecraft or ground asset associated with the asset that can be controlled by the team. This is a 8 character long ID that is unique. |
| name | The common name of the asset that can be controlled. This may not be unique but helps with providing information about what the asset is. |
| rpo_enabled | Whether this particular space asset has RPOD functionality available, such as maneuver software or docking. |
| components | A list of all components found on the associated asset. Each component has a dictionary value of key-value pairs of data. This includes the **name** of the component, which is used to define which component can be looked up and the **class** of the component, which helps to describe what the component is. The ‘component_id’ is an indexed number which is used for the message subtype to identify components within telemetry messages. The **is_imager** bool will return whether this component can image objects. This could include the cameras or CCD components. |

---

## Query Data

**Command**: `admin_query_data`

**Description:** 
This request can fetch all current and accurate information from a particular spacecraft. This includes all valid sensor data, information about the encryption and telecommunication systems and power information. This is a hardcoded set of data but can be expanded upon in future space range versions. All data is stored inside the payload of the response and grouped by category into sections. This can help aide the instructors to help teams diagnose their problems and fix their spacecraft when it is disabled. The query can also select multiple data by specifying a minimum and a maximum range, or just the most recent data point using the recent flag. By default, the space range application stores data every 10 seconds in a local database that can be pulled from later using this API call.

### Request

```json
{
	"type": "admin_query_data",
	"req_id": 0,
	"args": {
		"asset_id": "fb345a0c",
		"min_time": 0,
		"max_time": 20,
		"recent": false
	}
}
```

| **Argument** | **Description** |
| --- | --- |
| asset_id | The unique asset ID, associated with the particular asset that needs to be fetched the data for. This is the unique 8 character code for the asset to fetch from the storage. |
| min_time | The minimum time, in simulation seconds, to query the data from. This will include any data from this time and higher (provided it is within the range of the max time). If this parameter is not set, it will assume there is **no** minimum time. |
| max_time | The maximum time, in simulation seconds, to query the data from. This will include any data up until this time (provided it is within the range of the min time). If this parameter is not set, it will assume there is **no** maximum time. |
| recent | An **optional** flag that can be used. If this is set to **true**, only the **latest** data will be returned from the query and will not include any other data, regardless of what the **min_time** and **max_time** are set to. |

### Response

```json
{
	"type": "admin_query_data",
	"req_id": 0,
	"args": {
		"asset_id": "fb345a0c",
		"team": "Red Team",
		"data": [
			{
				"time": 10.7,
				...
			},
			...
		]
	},
	"success": true
}
```

| **Argument** | **Description** |
| --- | --- |
| asset_id | The unique asset ID that the data is associated with. This is tied to the data itself, as each team may have multiple assets associated. |
| team | The name of the team that the data was queried from. This only includes the team name and not the other information about the team. |
| data | An array of objects for the data that was queried. Even if there is only one entry, there will still be an array in data. It will be ordered by simulation time. Each data entry will include a time, in simulation seconds, and the list of data associated with that team at that point in time. The data can be shown in the section below, which explains what kind of data may be present within the system. |

## Example Data Packet

The following is an example **data packet** that can come from the simulation. This shows some of the data that is included in each of the team data. It is broken down into sections, defined using the **category.property** system, where the category defines what kind of data it is and the property is the actual data. 

```json
{
	"time": 10.7,
	"communications.frequency": 500.0,
	"communications.key": 12,
	"communications.bandwidth": 1.0,
	"location.latitude": 15.2,
	"location.longitude": 23.0,
	"location.altitude": 323000.0,
	"location.position_x": 1323132.0,
	"location.position_y": -231232.4,
	"location.position_z": 0.3,
	"location.velocity_x": 2314.0,
	"location.velocity_y": -89.2,
	"location.velocity_z": 15.0,,
	"location.station": "Singapore",
	"rotation.euler_x": 45.0,
	"rotation.euler_y": -23.0,
	"rotation.euler_z": 138.0,
	"rotation.attitude_rate_x": 0.1,
	"rotation.attitude_rate_y": 0.5,
	"rotation.attitude_rate_z": 0.4,
	"power.battery_percent": 45.0,
	"power.battery_capacity": 12.0,
	"power.sunlight_percent": 100.0,
	"power.power_generated": 5.0,
	"storage.storage_percent": 1.2,
	"storage.storage_used": 23321.0,
	"computer.state": "Running",
	"computer.navigation_mode": "Simple",
	"computer.pointing_mode": "Sun",
	"computer.controller_mode": "MRP",
	"computer.mapping_mode": "Reaction Wheels",
	"uplink.IsConnected": true,
	"uplink.Frequency": 473.0,
	"uplink.Distance": 67032.0,
	"uplink.SignalPower": 1.23e-12,
	"uplink.InterferencePower": 7e-13,
	"uplink.EffectiveSignalToNoise": 3.12,
	"uplink.BitErrorRate": 0.001,
	"uplink.TransmissionRate": 236782.0,
	...,
	"downlink.IsConnected": true,
	"downlink.Frequency": 473.0,
	"downlink.Distance": 67032.0,
	"downlink.SignalPower": 1.23e-12,
	"downlink.InterferencePower": 7e-13,
	"downlink.EffectiveSignalToNoise": 3.12,
	"downlink.BitErrorRate": 0.001,
	"downlink.TransmissionRate": 236782.0,
	...,
	"jammer.is_active": true,
	"jammer.frequency": 474.0,
	"jammer.power": 23.0
}
```

| Category | **Description** |
| --- | --- |
| time | The time that this data packet occurred at in simulation seconds. This is since the start of the simulation time, being time = 0.0. |
| communications | Data storing information about the communications of the spacecraft, including the frequency, keys and bandwidth of each ground station. Each entry is stored in a key-value pair within this dictionary. |
| location | Data storing information about the current location of the spacecraft, including geodetic coordinates and the nearest ground station. This also includes the position and velocity of each spacecraft. Each entry is stored in a key-value pair within this dictionary. |
| rotation | Data storing information about the rotation rates in degrees, using the **euler** values, as well as the **attitude rate** measured in degrees per second. |
| power | Data storing information about the power levels of the spacecraft, including the power sources, battery charge and sunlight percent, which can define whether the spacecraft is in eclipse or not. Each entry is stored in a key-value pair within this dictionary. |
| storage | Data storing information about the data storage levels of the spacecraft, indicating when storage is low. Each entry is stored in a key-value pair within this dictionary. |
| computer | Data storing information about the current state of the guidance computer on the spacecraft, including the pointing and controller modes. Each entry is stored in a key-value pair within this dictionary. |
| uplink | Data storing information about the link budgets of the uplink network. This is the link between the ground station and the spacecraft. Each entry is stored in a key-value pair within this dictionary. These are automatically generated from the link budget message. The full message can be found here:
[Data Link Message](https://docs.zendir.io/v1.5/API/Reference/DataLinkMessage). |
| downlink | Data storing information about the link budgets of the downlink network. This is the link between the spacecraft and the ground station. Each entry is stored in a key-value pair within this dictionary. These are automatically generated from the link budget message. The full message can be found here:
[Data Link Message](https://docs.zendir.io/v1.5/API/Reference/DataLinkMessage). |
| jammer | Data storing information about the jammer, if it exists, on the spacecraft. This includes the current power and whether it is active. Each entry is stored in a key-value pair within this dictionary. |

---

## Query Events

**Command**: `admin_query_events`

**Description:** 
This request will attempt to fetch all events associated with a particular team, or all teams. This will fetch an array of events that have already been triggered, whether its from the scenario itself or from a team sending commands. This is useful for displaying the events in a timeline. The query events will be able to publish any of the historic ones that may have been missed from the event trigger.

### Request

```json
{
	"type": "admin_query_events",
	"req_id": 0,
	"args": {
		"asset_id": "fb345a0c",
		"team": "Red Team"
	}
}
```

| **Argument** | **Description** |
| --- | --- |
| asset_id | The unique asset ID, associated with the particular asset that needs to be used to query the events. This is the unique 8 character code for the asset to fetch from the storage. This is optional, if wanting to filter by asset and not by team |
| team | The name of the team to filter for. If not wanting to filter by asset in particular, then this will display all events associated with a particular team. |

### Response

```json
{
	"type": "admin_query_events",
	"req_id": 0,
	"args": {
		"events": [
			{
				"event_id": 1,
				"simulation_time": 10.0,
				"simulation_utc": "2026/01/23 13:23:45",
				"clock_time": "2026/01/23 25:12:56",
				"trigger": "Spacecraft",
				"team_id": 10,
				"asset_id": "fb345a0c",
				"name": "Spacecraft Reboot",
				"arguments": {
					...
				}
			},
			...
		]
	},
	"success": true
}
```

| **Argument** | **Description** |
| --- | --- |
| events | The array of objects containing information about each event. This will be ordered by the event_id of the associated team or no team. All events will be sent in this format. |
| event_id | The ID of the event, for keeping track of which events have already been processed. This will be in order from 0 counting up and will reset between scenarios. |
| simulation_time | The current time of the simulation at which this event occurred. This is time in seconds since the initial start of the simulation, being time = 0. |
| simulation_utc | The UTC time of the simulation at which this event occurred. This is the simulation time and does not correspond to the real clock time. |
| clock_time | The real local time of the scenario at which this event occurred. This is the current timestamp and is independent of the scenario or simulation time. |
| trigger | The reason for the event that was triggered. It was either ‘Scenario’, ‘Operator’, ‘Spacecraft’ or ‘Ground’ based on the origin of the event. |
| team_id | The unique ID of the team, as specified by the scenario configuration. This identifies which team is associated with this event. In this case, the team ID will always match the known team. |
| asset_id | The unique ID of the spacecraft asset that this event pertains to. Each spacecraft or ground asset has a unique ID that is associated with that asset, enabling identifying the exact asset that was affected.  |
| name | The name of the event, which provides more context into what happened for the event to trigger. |
| arguments | A list of arguments from the event. This is dependent on the event triggered and provides some more details about the event itself. |

---

## Event Triggered

**Command**: `admin_event_triggered`

**Description:** 
This is a special type of response since it **does not require a request**. Any time an event is triggered by the ground station or spacecraft that is known, this will send through information about the event. This will be the case when telemetry are set, guidance modes are changed or any command is sent to the spacecraft via the ground station. It can help keep log of the events that are sent and useful for record keeping. This response will include any team’s events.

### Response

```json
{
	"type": "admin_event_triggered",
	"req_id": 0,
	"args": {
		"event_id": 1,
		"simulation_time": 10.0,
		"simulation_utc": "2026/01/23 13:23:45",
		"clock_time": "2026/01/23 25:12:56",
		"trigger": "Spacecraft",
		"team_id": 10,
		"asset_id": "fb345a0c",
		"name": "Spacecraft Reboot",
		"arguments": {
			...
		}
	},
	"success": true
}
```

| **Argument** | **Description** |
| --- | --- |
| event_id | The ID of the event, for keeping track of which events have already been processed. This will be in order from 0 counting up and will reset between scenarios. |
| simulation_time | The current time of the simulation at which this event occurred. This is time in seconds since the initial start of the simulation, being time = 0. |
| simulation_utc | The UTC time of the simulation at which this event occurred. This is the simulation time and does not correspond to the real clock time. |
| clock_time | The real local time of the scenario at which this event occurred. This is the current timestamp and is independent of the scenario or simulation time. |
| trigger | The reason for the event that was triggered. It was either ‘Scenario’, ‘Operator’, ‘Spacecraft’ or ‘Ground’ based on the origin of the event. |
| team_id | The unique ID of the team, as specified by the scenario configuration. This identifies which team is associated with this event. In this case, the team ID will always match the known team. |
| asset_id | The unique ID of the spacecraft asset that this event pertains to. Each spacecraft or ground asset has a unique ID that is associated with that asset, enabling identifying the exact asset that was affected.  |
| name | The name of the event, which provides more context into what happened for the event to trigger. |
| arguments | A list of arguments from the event. This is dependent on the event triggered and provides some more details about the event itself. |

---

## **Get Simulation**

**Command**: `admin_get_simulation`

**Description:**
This request can be used to return the current state of the simulation, including whether it is running, paused, or stopped, and the current simulation speed multiplier. This can be polled periodically to keep the admin UI in sync with the simulation timeline controls.

### Request

```json
{
	"type": "admin_get_simulation",
	"req_id": 0
}
```

*There are no arguments to be passed into this command.*

### Response

```json
{
	"type": "admin_get_simulation",
	"req_id": 0,
	"args": {
		"state": "Running",
		"speed": 5.0
	},
	"success": true
}
```

| **Argument** | **Description** |
| --- | --- |
| state | The current state of the simulation as a string. Possible values are **Running** (the simulation is actively simulating), **Paused** (the simulation has been started but is currently paused), **Stopped** (the simulation has not been started yet or has been reset) and **Scrubbing** (the simulation is scrubbing through the database timeline). |
| speed | The current simulation speed as a factor of real-time. A value of **1.0** indicates real-time, **5.0** indicates the simulation is running at five times real-time, and so on. |

---

## **Set Simulation**

**Command**: `admin_set_simulation`

**Description:**
This request can be used to control the simulation by setting its state and/or speed. At least one of state or speed must be provided. Both can be sent in a single request.

### Request

```json
{
	"type": "admin_set_simulation",
	"req_id": 0,
	"args": {
		"state": "Paused",
		"speed": 2.0
	}
}
```

| **Argument** | **Description** |
| --- | --- |
| state | The desired simulation state. Must be one of **Running** (starts or resumes the simulation), **Paused** (pauses the simulation) or **Stopped** (resets the simulation to initial conditions). |
| speed | The desired simulation speed as a factor of real-time. For example, 1.0 is real-time and 5.0 is five times real-time. |

### Response

```json
{
	"type": "admin_set_simulation",
	"req_id": 0,
	"success": true
}
```

*There are no arguments returned in the response. A success value of true indicates the requested changes were applied successfully.*

---

## **Get Scenario Events**

**Command**: `admin_get_scenario_events`

**Description:**
This request can be used to return the list of scenario events that are loaded into the current scenario. These are the predefined events (e.g. spacecraft failures) configured by the instructor, which can be triggered at specific simulation times.

### Request

```json
{
	"type": "admin_get_scenario_events",
	"req_id": 0
}
```

*There are no arguments to be passed into this command.*

### Response

```json
{
	"type": "admin_get_scenario_events",
	"req_id": 0,
	"args": {
		"events": [
			{
				"enabled": true,
				"name": "Battery Failure",
				"time": 600.0,
				"repeat": false,
				"interval": 1.0,
				"type": "Spacecraft",
				"assets": ["SC_001", ...],
				"target": "Battery",
				"data": {
					"mode": "disable"
				}
			},
			...
		]
	},
	"success": true
}
```

| **Argument** | **Description** |
| --- | --- |
| events | A list of all scenario events loaded in the current scenario. Each event contains: enabled (whether the event is  active), name (display name), type (the event type, e.g. "Spacecraft"), time (trigger time in simulation seconds), repeat (whether the event repeats), interval (repeat interval in seconds), target (the target component or sensor) and data (a dictionary of event specific parameters). The ‘assets’ define which assets the associated event affect. If missing any assets, it will target all assets of the event type chosen. |