# [SPACE RANGE] Spacecraft Command Schema

This document contains the structure for the commands used for the spacecraft within Space Range, including all parameters for each of the commands. Commands are sent over the **uplink** MQTT topic and follow a particular JSON packet structure. The structure for the packet, along with all arguments for the commands are outlined in this document. The data is read by the **ground controller** associated with a particular team and then uplinked by the transmitter of the ground station network to the target spacecraft’s receiver.

### MQTT Topic

The MQTT topic is defined by:

```json
Zendir/SpaceRange/**[GAME]**/**[TEAM]**/Uplink
```

where **`[GAME]`** is the name of the game defined by the simulation scenario and **`[TEAM]`** is the team’s ID. This is a numeric number and defines the instance of the team that is controlling the ground network. Only commands sent to a particular ground network are transmitted on this **MQTT** topic.

### Encryption

Each command communicated over the **MQTT** topic is encrypted by a 6-character **alphanumeric** password using **XOR** encryption. Each team has a designated **password**, which is generated at the beginning of the scenario and is known by each team and the instructors. The password is not shared or discoverable by other teams (without cheating). Using this password, the data must be encrypted using this method. The XOR decryption has the same operation for encrypting and decrypting the data with the same **string key**. A sample piece of encryption code may look like the following:

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

Each command is structured with the following JSON packet:

```json
{
	"id": "fb345a0c",
	"command": "x",
	"time": 0.0,
	"args": {
		"arg_1": "x",
		...
	}
}
```

| **Property** | **Description** |
| --- | --- |
| id | This is the ID of the asset. The ID must match the asset ID for the command to be executed. This is useful to ensure that the spacecraft itself is executing a command that is designed for itself. Each asset has a particular ID that is associated with it and that is defined in the Space Range configuration for the scenario. This is an 8-character ID code. |
| command | The name of the command, where each command performs a particular action. For more information of each command, see the tables below. |
| time | The time, measured in simulation seconds since the start of the scenario, to which to execute the command. Once that time is elapsed, the command will be executed. If the time is ≤ 0, then the command will be executed immediately. |
| args | A list of arguments that are applied to each of the commands. Each command may require additional arguments to process the commands. They are outlined in each of the tables below. The arguments are a dictionary of key-value pairs. |

---

## Guidance Pointing

**Command**: `guidance`

**Description:** 
This command can be used to execute a **guidance pointing mode** on the spacecraft, which will use the ADCS system to point the spacecraft towards a specific set of directions. For each ‘pointing’ option, there are a number of sub-parameters that can be applied to determine the correct location that the spacecraft will point towards. The default options will work for a number of pointing modes. For some pointing modes, there are additional arguments that are required. They are noted in the table below, as described in the parameter if it applies to only a particular pointing mode.

| **Argument** | **Default Value** | **Range** | **Unit** | **Description** |
| --- | --- | --- | --- | --- |
| pointing | inertial | inertial,
velocity,
sun,
nadir,
ground,
location,
idle |  | The pointing direction for the spacecraft, based on the alignment vector, attempting to align the up-vector of a component with this particular direction. If **idle** is inputted, the reaction wheels will stop inputting torque commands and will not use up energy. |
| target |  |  |  | The component on the spacecraft to align the pointing vector towards. This can be fetched from the list of components available on the spacecraft. The name of the component is case-insensitive and will find the component by name. |
| alignment | +z | +z,
-z,
+y,
-y,
+z,
-z |  | The alignment vector of the component to match. Typical components, such as cameras, solar-panels, sensors, have their primary axis about the +z axis. Taking an image would require using an alignment in the +z for example. |
| pitch
 **INERTIAL POINTING**  | 0.0 | -90.0 to 90.0 | deg | The angle in degrees to target an arbitrary pitch angle in an inertial pointing mode to, relative to the alignment vector. |
| roll
 **INERTIAL POINTING**  | 0.0 | -180.0 to 180.0 | deg | The angle in degrees to target an arbitrary roll angle in an inertial pointing mode to, relative to the alignment vector. |
| yaw
 **INERTIAL POINTING**  | 0.0 | -180.0 to 180.0 | deg | The angle in degrees to target an arbitrary yaw angle in an inertial pointing mode to, relative to the alignment vector. |
| station
 **GROUND POINTING**  |  |  |  | The ground station for the primary alignment vector to point towards. This can be fetched from the list of ground station names available within the scenario. |
| planet
 **NADIR POINTING 
 LOCATION POINTING**  | earth | sun,
earth,
moon,
mars |  | The planet to target the primary alignment vector towards, which will point the spacecraft in the direction of the body (the center of the celestial body, not necessarily the nearest surface). |
| latitude
 **LOCATION POINTING**  | 0.0 | -90.0 to 90.0 | deg | The latitude in degrees for the ground location to align the target vector towards. This will attempt to point at this latitude, on the target planet. |
| longitude
 **LOCATION POINTING**  | 0.0 | -180.0 to 180.0 | deg | The longitude in degrees for the ground location to align the target vector towards. This will attempt to point at this longitude, on the target planet. |
| altitude
 **LOCATION POINTING**  | 0.0 | 0.0 to 100000.0 | m | The altitude in meters for the ground location to align the target vector towards. This will attempt to point at this altitude, on the target planet. |
| spacecraft
 **RELATIVE POINTING**  | spacecraft |  |  | The asset ID corresponding to the space asset of another spacecraft that exists in the simulation. This will attempt to point the spacecraft towards that spacecraft in the direction of the target and alignment. |

---

## Downlink

**Command**: `downlink`

**Description:** 
All sensor data and cached images are stored on the spacecraft in a storage system. When ready, data can be downlinked over the ground station network via the telecommunication system. This relies on transmitters communicating the data over a network to a receiver. All data on the spacecraft is actively downlinked over the network and the cache onboard the spacecraft is cleared.

| **Argument** | **Default Value** | **Range** | **Unit** | **Description** |
| --- | --- | --- | --- | --- |
| downlink | true | false,
true |  | Whether to perform the downlink. If this is not the case, then no downlink will be performed. |
| ping | false | false,
true |  | A downlink is only performed manually. However, by turning on this parameter, the data can be downlinked every time a **ping** occurs, which is typically every 20 simulated seconds by the spacecraft. Although this keeps the cache clean and data always downlinked, this can increase the power usage of the transmitter as it will perform operations more frequently. |

---

## Camera Configure

**Command**: `camera`

**Description:** 
This command will configure a specific camera based on some camera specifications. This is typically done before a capture is performed, to ensure that the FOV, aperture and other properties are taken in account. The configure command itself will not capture an image, unless the ‘sample’ argument is enabled.

| **Argument** | **Default Value** | **Range** | **Unit** | **Description** |
| --- | --- | --- | --- | --- |
| target |  |  |  | This is the target component to capture an image with. This is the name of the component and is case-insensitive. It will find a component with that name onboard the spacecraft, provided it is a camera, and configure that camera. Some space range scenarios come preconfigured with multiple cameras, but using ‘Camera’ by default will usually pick up the correct sensor. |
| monochromatic | false | false,
true |  | Whether to capture the image in monochromatic colors - which would just be greyscale. This saves on image downlink budget, but loses the color resolution from the image. |
| resolution | 512 | 128 to 1024 | px | The number of pixels in the image. Cameras are currently configured to be square, so the resolution will be multiplied by itself. |
| coc | 0.03 | 0.0 to 1.0 | mm | This is the circle of confusion. It defines the acceptable level of blur, light from an object converging before or after the sensor will be out of focus, if it is blurred by more than the circle of confusion it is not inside the depth of field planes this is measured on the sensor itself in this case. |
| pixel_pitch | 0.012 | 0.0 to 1.0 | mm | The spacing from one pixel to its X or Y neighbor, center to center. A smaller pixel pitch and resolution reduces the physical size of the sensor resulting in a more cropped image. |
| focusing_distance | 4.0 | 0.0 to 1000000.0 | m | Defines the distance from the lens to where objects are in focus. This is useful for imaging other spacecraft in similar orbits. |
| aperture | 1.0 | 0.0 to 1000.0 | mm | The diameter of the opening of the lens, larger opening means wider FOV. The large the lens will also enable more light to come through, typically allowing for a brighter image. |
| focal_length | 100.0 | 0.0 to 1000.0 | mm | The distance from the nodal point (where light converges) of the lens to the sensor, longer distance confines field of view. Moving the sensor closer to the nodal point will catch more light and increase field of view. |
| fov | 60.0 | 0.01 to 150.0 | deg | The field of view (FOV) of the camera, which defines how much of the environment is taken in the image. A large field of view will include more of the environment than a small field of view. Large FOV images will also be brighter, if the aperture is not adjusted for it. |
| sample | false | false,
true |  | Whether or not to downlink a sample image (a 32x32 sample) taken from the camera which can be used as an indication of what the camera looks like with the current settings. This will be downlinked on the next **ping** of the spacecraft. |

---

## Camera Capture

**Command**: `capture`

**Description:** 
This command will capture an image from one of the cameras. It assumes that the camera has already been configured correctly. The capture command can also name the image, which can be useful for designating images within a gallery. The image itself is stored in storage until a downlink command is executed.

| **Argument** | **Default Value** | **Range** | **Unit** | **Description** |
| --- | --- | --- | --- | --- |
| target |  |  |  | This is the target component to capture an image with. This is the name of the component and is case-insensitive. It will find a component with that name onboard the spacecraft, provided it is a camera, and configure that camera. Some space range scenarios come preconfigured with multiple cameras, but using ‘Camera’ by default will usually pick up the correct sensor. |
| name | image |  |  | The name of the image to capture. This will store the name in the first **50 bytes** of the image data. Regardless how short the name is, the first **50 bytes** will be the name of the image in ASCII format. If the name is longer than this, the remainder of the characters will be cut off. All other bytes from the image will be the actual JPEG image data itself. |

---

## Telemetry Configure

**Command**: `telemetry`

**Description:** 
This command can change the frequency or encryption key of the communication channel. The uplink and downlink across the simulated components (spacecraft to ground station) encrypts data using a **Caesar Cypher** with a key between 0 and 255 and rotates the bytes by a specific amount. If a frequency matches another team, or the key is discovered, it is suggested that the telemetry information should be updated.

| **Argument** | **Default Value** | **Range** | **Unit** | **Description** |
| --- | --- | --- | --- | --- |
| frequency | 0 | 0 to 10000 | MHz | The frequency of the uplink and downlink channels, between the spacecraft and the ground station, defined in Megahertz. |
| key | 0 | 0 to 255 |  | The key used to rotate the bits within each byte of the packets that are communicated over the network, to ensure each spacecraft operates on a specific command associated to itself. |

---

## Jamming

**Command**: `jammer`

**Description:** 
This command can enable or disable the jammer on-board the spacecraft. If no jammer exists, this command will not executed. The jammer can cause disruption in TT&C systems by outputting *garbage* over the communication channel. The current jammer supports a singular barrage jamming frequency. This will use up power based on the transmitter’s power value.

| **Argument** | **Default Value** | **Range** | **Unit** | **Description** |
| --- | --- | --- | --- | --- |
| active | false | false,
true |  | Whether to enable or disable the jammer. To turn off a jammer, simply set this value to ‘false’ to stop the jamming process from continuing. |
| frequencies | [ ] | 0 to 10000 | MHz | An array of frequencies, in Megahertz, that should be outputted from the jamming transmitter. This would be aligned to the target’s received frequency to cause disruption. This creates multi-band jamming. |
| power | 0 | 0 to 10000 | W | The power, in watts, that is consumed by the jammer. The larger the power, the more signal strength is outputted into the jamming transmitter and the larger the interference. However, the larger the power, the more battery power will be drained from the spacecraft by the jammer. |

---

## Component Reset

**Command**: `reset`

**Description:** 
If a component becomes corrupted, either through a specific set of events or due to an error model occurring over time, the component itself can be reset. Upon reset, the component *may* become operational again. However, during this process, the spacecraft will reboot. Depending on the scenario, this may take a minute of simulation time before the spacecraft can be interacted with again.

| **Argument** | **Default Value** | **Range** | **Unit** | **Description** |
| --- | --- | --- | --- | --- |
| target |  |  |  | This is the target component to reset and reboot. This is the name of the component and is case-insensitive. It will find a component with that name onboard the spacecraft and only reset that device. |

---

## Thruster

**Command**: `thrust`

**Description:** 
This command can start firing a particular thruster on board the spacecraft. Currently, it can fire the thruster at the targeted thrust force with a specific duration. It cannot yet gimbal or fire in a particular direction, but rather can ensure that the thruster is either turned on or off.

| **Argument** | **Default Value** | **Range** | **Unit** | **Description** |
| --- | --- | --- | --- | --- |
| target |  |  |  | This is the target thruster to start or stop firing, in the case there are multiple thrusters on board the spacecraft. |
| active | false |  |  | A flag whether the thruster should be thrusting or not. This can turn off a thruster, even if the desired duration has not yet been met. |
| duration | 0 |  | s | The initial duration to fire the thruster for, measured in seconds. Without interruptions (or fuel considerations), this is how long the thruster will fire for. |

---

## Rendezvous Maneuver

**Command**: `rendezvous`

**Description:**
Configures a perch-mode rendezvous with another spacecraft. The chaser holds a fixed offset from the target, specified in the target’s LVLH frame. X is radial (away from the planet), Y is along the velocity vector, and Z is “up” (cross product of radial and velocity). All offset components are in meters.

| **Argument** | **Default Value** | **Range** | **Unit** | **Description** |
| --- | --- | --- | --- | --- |
| target |  |  |  | Asset ID of the spacecraft to rendezvous with (the LVLH frame is defined relative to this target). |
| active | false |  |  | When true, the spacecraft attempts to reach and hold the given LVLH offset. When false, the maneuver is disabled. |
| offset | [0, 0, 0] | [-10000, 10000] per axis | m | Desired position offset in the target’s LVLH frame: `[X, Y, Z]` in meters. X = radial, Y = velocity direction, Z = up (radial × velocity). |

---

## **Docking**

**Command**: `docking`

**Description:**
Commands the current spacecraft to dock with or undock from a docking adapter on another team spacecraft. The current spacecraft must have at least one Docking Adapter component and RPO (rendezvous/proximity operations) must be enabled. **Target** is the other spacecraft (by asset ID). **Component** is the **name** of the docking adapter on that target spacecraft (not the component ID). **Dock** is a boolean: true to dock, false to undock. When the ‘dock’ is true, then this will set the correct target, but will only perform a docking with the physics (connecting the two objects together) once the two objects are close enough to each other.

| **Argument** | **Default Value** | **Range** | **Unit** | **Description** |
| --- | --- | --- | --- | --- |
| target |  |  |  | Asset ID of the other team spacecraft that has the docking adapter to dock with or undock from. |
| component |  |  |  | **Name** of the docking adapter component on the target spacecraft (e.g. as returned in component list: name, or class if name is absent). Identifies which adapter on the target to use. |
| dock |  |  |  | true to dock (attach) to the selected adapter; false to undock (detach) from it. |