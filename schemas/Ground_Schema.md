# Ground Command Schema

Each team is provided access to **one ground controller**, which may be connected to multiple **ground stations**.

The ground controller allows teams to:

- Send commands to spacecraft over the telecommunications network (**uplink**)
- Receive telemetry and other data from the network (**downlink**)

Uplinked commands are published to a designated **MQTT topic** and must conform to the Spacecraft Command Schema. In addition to command uplinks and telemetry downlinks, teams can request **supplementary data** from the ground controller. This uses a **request–response messaging model**:

- Requests are sent on a team-specific **request topic**
- Responses are returned on a corresponding **response topic**

Each team has **one request topic and one response topic**, both scoped exclusively to that team. This document outlines all commands available for the **ground controller**.

### MQTT Topics

The MQTT **request** topic is defined by:

```json
Zendir/SpaceRange/**[GAME]**/**[TEAM]**/Request
```

where **`[GAME]`** is the name of the game defined by the simulation scenario and **`[TEAM]`** is the team’s ID. This is a numeric number and defines the instance of the team that is controlling the ground network.

The MQTT **response** topic is defined by:

```json
Zendir/SpaceRange/**[GAME]**/**[TEAM]**/Response
```

where **`[GAME]`** is the name of the game defined by the simulation scenario and **`[TEAM]`** is the team’s ID. This is a numeric number and defines the instance of the team that is controlling the ground network.

### Encryption

Each request and response is communicated over the **MQTT** topic is encrypted by a 6-character **alphanumeric** password using **XOR** encryption. Each team has a designated **password**, which is generated at the beginning of the scenario and is known by each team and the instructors. The password is not shared or discoverable by other teams (without cheating). Using this password, the data must be encrypted using this method. The XOR decryption has the same operation for encrypting and decrypting the data with the same **string key**. A sample piece of encryption code may look like the following:

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

## List Assets

**Command**: `list_assets`

**Description:** 
This request is used to fetch a list of all assets that exist on the particular team. This includes all assets that are currently controlled by the team, as there may be more than one spacecraft. This can be useful for understanding the ID of each of the assets which is used to send commands to the particular entity when in orbit, or fetching data from that entity.

### Request

```json
{
	"type": "list_assets",
	"req_id": 0
}
```

*There are no arguments to be passed into this request.*

### Response

```json
{
	"type": "list_assets",
	"req_id": 0,
	"args": {
		"space": [
			{
				"asset_id": "fb345a0c",
				"name": "Microsat",
				"rpo_enabled": true
			},
			...
		]
	},
	"success": true
}
```

| **Argument** | **Description** |
| --- | --- |
| space | A list of all asset IDs and names associated with a particular team. These are all space assets that are available to control or communicate with via the system. This also includes whether the spacecraft has RPO functionality enabled, which may be useful for some functions. |

---

## List Entity

**Command**: `list_entity`

**Description:** 
This request is used to fetch a list of all known information about a particular entity, such as a spacecraft, but not tied to the state of the entity. This includes information about what components are available and whether any of the states have been activated. This will not pull power or sensor information, as those are transmitted by the spacecraft via a **downlink** command. This is more about fetching **known** data of the spacecraft schematic.

### Request

```json
{
	"type": "list_entity",
	"req_id": 0,
	"args": {
		"asset_id": "fb345a0c"
	}
}
```

| **Argument** | **Description** |
| --- | --- |
| asset_id | The unique ID of the asset to list the information about. This will return the data about a particular entity and that entity only. If the ID does not match a known entity that the team controls, it will return an error. |

### Response

```json
{
	"type": "list_entity",
	"req_id": 0,
	"args": {
		"asset_id": "fb345a0c",
		"components": [
			{
				"name": "Solar Panel +X",
				"class": "Solar Panel",
				"component_id": 5,
				"is_imager": false
			},
			...
		],
		"jammer": {
			"is_active": true,
			"frequency": 474.0,
			"power": 23.0
		}
	},
	"success": true
}
```

| **Argument** | **Description** |
| --- | --- |
| asset_id | The unique ID of the asset that the information in the response is regarding. This is associated with the spacecraft asset that the team controls. |
| components | A list of all components found on the entity. Each component has a dictionary value of key-value pairs of data. This includes the **name** of the component, which is used to define which component can be looked up and the **class** of the component, which helps to describe what the component is. The ‘component_id’ is an indexed number which is used for the message subtype to identify components within telemetry messages. The **is_imager** bool will return whether this component can image objects. This could include the cameras or CCD components. |
| jammer | A dictionary storing information about the jammer, if it exists, on the spacecraft. This includes the current power (Watts), the frequency (Megahertz_ and whether it is active. Each entry is stored in a key-value pair within this dictionary. |

---

## List Ground Stations

**Command**: `list_stations`

**Description:** 
This request is used to fetch a list of all ground stations that are connected to the current ground controller, including the names of each one and the locations of them across the world. This can be used for populating fields and providing context for maps about which regions of the planet are available for downlinking data.

### Request

```json
{
	"type": "list_stations",
	"req_id": 0
}
```

*There are no arguments to be passed into this request.*

### Response

```json
{
	"type": "list_stations",
	"req_id": 0,
	"args": {
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
| stations | A list of the station objects, each themselves a dictionary of data. Each station contains the information about the name of the ground station, the latitude (in degrees), the longitude (in degrees) and the altitude (in meters) of the ground station. |

---

## Get Telemetry

**Command**: `get_telemetry`

**Description:** 
This request is used to fetch information about the current telemetry status. This will include detailed information about the uplink (from ground station to spacecraft) and downlink (from spacecraft to ground station) budgets, as well as the frequency, key and bandwidth of the telecommunication systems.

### Request

```json
{
	"type": "get_telemetry",
	"req_id": 0,
	"args": {
		"asset_id": "fb345a0c"
	}
}
```

| **Argument** | **Description** |
| --- | --- |
| asset_id | The unique ID of the asset to list the information about. This will return the data about a particular entity and that entity only. If the ID does not match a known entity that the team controls, it will return an error. |

### Response

```json
{
	"type": "get_telemetry",
	"req_id": 0,
	"args": {
		"asset_id": "fb345a0c",
		"frequency": 500.0,
		"key": 10,
		"bandwidth": 1.0,
		"uplink": {
			"IsConnected": true,
			"Frequency": 473.0,
			"Distance": 67032.0,
			"SignalPower": 1.23e-12,
			"InterferencePower": 7e-13,
			"EffectiveSignalToNoise": 3.12,
			"BitErrorRate": 0.001,
			"TransmissionRate": 236782.0,
			...
		},
		"downlink": {
			"IsConnected": true,
			"Frequency": 473.0,
			"Distance": 67032.0,
			"SignalPower": 1.23e-12,
			"InterferencePower": 7e-13,
			"EffectiveSignalToNoise": 3.12,
			"BitErrorRate": 0.001,
			"TransmissionRate": 236782.0,
			...
		}
	},
	"success": true
}
```

| **Argument** | **Description** |
| --- | --- |
| asset_id | The unique ID of the asset that the information is regarding. This will return the data about a particular entity and that entity only. |
| frequency | The current frequency of the ground network that it is communicating over. This is for both listening and transmitting data. It is measured in Megahertz. |
| key | The current key, which is a number, that is used for the Caesar cypher encryption on the communication channels within the simulation. This is not the same as the password to encrypt the data going to and from the MQTT server and the operation tools. |
| bandwidth | The bandwidth of the ground station which defines the range at which the ground network can listen into data on, defined in Megahertz. |
| uplink | A dictionary storing information about the link budgets of the uplink network. This is the link between the ground station and the spacecraft. Each entry is stored in a key-value pair within this dictionary. These are automatically generated from the link budget message. |
| downlink | A dictionary storing information about the link budgets of the downlink network. This is the link between the spacecraft and the ground station. Each entry is stored in a key-value pair within this dictionary. These are automatically generated from the link budget message. |

---

## Set Telemetry

**Command**: `set_telemetry`

**Description:** 
This request can update the telemetry information of the spacecraft and ground station. This includes updating the frequency, key and bandwidth of the transmitters and receivers that are controlled by this particular team. This will send a request to the spacecraft over the network to update the frequencies of the antennae and attempt to respond with a status that is okay.

### Request

```json
{
	"type": "set_telemetry",
	"req_id": 0,
	"args": {
		"frequency": 500.0,
		"key": 10,
		"bandwidth": 1.0,
	}
}
```

| **Argument** | **Description** |
| --- | --- |
| frequency | The new frequency of the communications with the team, which is defined in Megahertz and will attempt to update the frequency of the receiver and transmitters, on both the spacecraft and the ground network. |
| key | The new encryption key, which is a number, that is used for the Caesar cypher encryption on the communication channels within the simulation. This is not the same as the password to encrypt the data going to and from the MQTT server and the operation tools. |
| bandwidth | The new bandwidth of the ground station which defines the range at which the ground network can listen into data on, defined in Megahertz. |

### Response

```json
{
	"type": "set_telemetry"
	"req_id": 0,
	"success": true
}
```

*There are no arguments outputted by this response.*

---

## Chat Assistant Query

**Command**: `chat_query`

**Description:** 
This request will send a new chat request to an AI chat model, provided it is enabled within Space Range. Some scenarios may not have the chat assistant enabled, so would result in no conversation happening. This will send through a query with a prompt and some context data, if provided, containing the last information from the different message types from the downlinked data.

### Request

```json
{
	"type": "chat_query",
	"req_id": 0,
	"args": {
		"asset_id": "fb345a0c",
		"prompt": "Tell me more about...",
		"messages": [
			{
				...
			}
		]
	}
}
```

| **Argument** | **Description** |
| --- | --- |
| asset_id | The unique ID of the asset to query the data from. This will perform the chat query about a particular entity and that entity only. If the ID does not match a known entity that the team controls, it will return an error. |
| prompt | The question to ask the chat assistant, which will have context over some of the information provided. It only has access to the messages that are sent with it for the satellite state, but will understand the general component structure and actions available for the operation tool. |
| messages | A list of messages containing data from the spacecraft as context about what has been received so that it knows the current (or most recently downlinked) state of the spacecraft. |

### Response

```json
{
	"type": "chat_query",
	"req_id": 0,
	"success": true
}
```

*There are no arguments outputted by this response. This will not return any data straight away, but rather there will be data coming through the `chat_response` command over the response topic once an answer has been produced.*

### Response - *Delayed*

Once the query has been returned via the assistant, and a response has been generated, it will be published over the **response** topic under the type `chat_response`. It will contain the following structure:

```json
{
	"type": "chat_response",
	"req_id": 0,
	"args": {
		"valid": true,
		"role": "assistant",
		"message": "This is the response...",
		"timestamp": "2026/01/25 13:05:12"
	},
	"success": true
}
```

| **Argument** | **Description** |
| --- | --- |
| valid | Whether the response is valid. If not valid, it means a response is currently loading. |
| role | The author of the message. This will either be ‘assistant’, if the chat has responded back with some data, or ‘user’, which is when the user has sent a request. |
| message | The actual response text, using Rich Text styled format from the chat assistant. This may also be the same text the user sent, which would have a role of ‘user’. |
| timestamp | The exact local datetime that the message was created at. |

---

## Event Triggered

**Command**: `event_triggered`

**Description:** 
This is a special type of response since it **does not require a request**. Any time an event is triggered by the ground station or spacecraft that is known, this will send through information about the event. This will be the case when telemetry are set, guidance modes are changed or any command is sent to the spacecraft via the ground station. It can help keep log of the events that are sent and useful for record keeping. This response will only show events from the current team being operated on.

### Response

```json
{
	"type": "event_triggered",
	"req_id": 0,
	"args": {
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
| simulation_time | The current time of the simulation at which this event occurred. This is time in seconds since the initial start of the simulation, being time = 0. |
| simulation_utc | The UTC time of the simulation at which this event occurred. This is the simulation time and does not correspond to the real clock time. |
| clock_time | The real local time of the scenario at which this event occurred. This is the current timestamp and is independent of the scenario or simulation time. |
| trigger | The reason for the event that was triggered. It was either ‘Scenario’, ‘Operator’, ‘Spacecraft’ or ‘Ground’ based on the origin of the event. |
| team_id | The unique ID of the team, as specified by the scenario configuration. This identifies which team is associated with this event. In this case, the team ID will always match the known team. |
| asset_id | The unique ID of the spacecraft asset that this event pertains to. Each spacecraft or ground asset has a unique ID that is associated with that asset, enabling identifying the exact asset that was affected.  |
| name | The name of the event, which provides more context into what happened for the event to trigger. |
| arguments | A list of arguments from the event. This is dependent on the event triggered and provides some more details about the event itself. |

---

## Get Packet Schemas

**Command**: `get_packet_schemas`

**Description:** 
This endpoint returns the telemetry schema definitions for all known packet types in the simulation. These schemas follow the XTCE (XML Telemetric and Command Exchange) standard, an industry-standard format used in space missions to describe the structure of telemetry data. Each schema defines how a CCSDS Space Packet -- the standard framing protocol used by spacecraft to package and transmit data -- is laid out, including its header fields, timestamp format, spacecraft identifier, and the individual data parameters (along with their types, units, and valid ranges). By retrieving these schemas, a ground application can understand the binary format of every telemetry message the spacecraft may send, allowing it to decode raw downlink packets into meaningful, human-readable values without requiring any hardcoded knowledge of the mission's data formats.

### Request

```json
{
	"type": "get_packet_schemas",
	"req_id": 0
}
```

*There are no arguments to be passed into this request.*

### Response

```json
{
	"type": "get_packet_schemas",
	"req_id": 0,
	"args": {
		"telemetry": [
			"",
			...
		]
	},
	"success": true
}
```

| **Argument** | **Description** |
| --- | --- |
| telemetry | A list of XML files, as strings, that are associated with each individual packet definition following the CCSDS XTCE definition styles. |