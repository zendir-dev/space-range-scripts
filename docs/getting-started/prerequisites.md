# Prerequisites

Before connecting to a Space Range scenario you need a small amount of infrastructure and a small set of credentials. This page lists everything required and how to obtain it.

---

## What you need

| Item | Why | Where it comes from |
| --- | --- | --- |
| A reachable **MQTT broker** | All Space Range traffic flows over MQTT. | Hosted broker (e.g. `mqtt.zendir.io`), or your own (Mosquitto, EMQX, HiveMQ, NanoMQ). |
| A running **Studio** instance with a scenario loaded and connected to that broker | Studio is the authoritative simulation. Without it, no session ticks, no telemetry, no command processing. | Operated by the instructor / scenario host. |
| The **game name** | Used as the namespace for every MQTT topic (`Zendir/SpaceRange/<GAME>/...`). | Configured in Studio at scenario launch. |
| Your **team ID** | Identifies your team on the broker (`<TEAM>` segment of every team-scoped topic). | Configured in the scenario JSON; given to you by the instructor. |
| Your **team password** | XOR key for all of your team's traffic. | Same — issued by the instructor. |
| Your **Caesar key** and **frequency** | Required to decode telemetry. | Issued by the instructor; can be rotated at runtime by your team via the [`encryption`](../api-reference/spacecraft-commands.md#encryption) command. |
| (Optional) The **admin password** | Required only if you operate as an instructor or a constructive agent. | Issued by the instructor. |
| An **MQTT 3.1.1+ client library** for your language | To publish, subscribe, and route messages. | Any library — `paho-mqtt` (Python), `mqtt.js` (JS), `MQTTnet` (.NET), etc. |

If any of these are missing, the failure mode is usually silent on the broker side — your client connects, subscribes, and waits indefinitely for traffic that never arrives. The [Troubleshooting guide](../guides/troubleshooting.md) walks through each failure case.

---

## Broker

### Hosted

Zendir runs a public broker at `mqtt.zendir.io` on the standard MQTT port. If your scenario is hosted on that broker, point your client at:

```text
host: mqtt.zendir.io
port: 1883            # plain MQTT
```

The broker accepts anonymous connections — there is no broker-level username/password. Team segregation is enforced by the in-payload XOR layer described in [Concepts → Encryption](../concepts/encryption.md).

### Self-hosted

Any MQTT 3.1.1+ broker works. For local development, the simplest setup is a one-liner Mosquitto:

```bash
docker run -p 1883:1883 -v $PWD/mosquitto.conf:/mosquitto/config/mosquitto.conf eclipse-mosquitto
```

with a minimal `mosquitto.conf`:

```text
listener 1883
allow_anonymous true
```

Note that Studio must be configured to point at the same broker — coordinate the host/port with whoever is running Studio.

### Network

Make sure your client's network can reach the broker on the chosen port. Common gotchas:

- Corporate or campus firewalls often block outbound `1883`. Use `8883` (TLS) or arrange a tunnel.
- Some Wi-Fi networks block client-isolated traffic; use a wired connection or a phone hotspot if the broker is on the LAN.
- The `mqtt://` URL scheme is for plain MQTT; `mqtts://` is for TLS. If your broker doesn't have TLS configured, mixing the two will silently fail to connect.

---

## Credentials

Every operator-side client needs **four** pieces of data, given to you by the instructor:

1. **Game name** — e.g. `SPACE RANGE` or `ZENDIR`. Case is significant; copy it exactly.
2. **Team ID** — a numeric ID like `111111`.
3. **Team password** — exactly 6 alphanumeric characters.
4. **Caesar key** and **frequency** — used by your client to decode incoming telemetry. The Caesar key is an integer 0–255; the frequency is in MHz.

Admin clients additionally need:

5. **Admin password** — also 6 alphanumeric characters, used for traffic on the `Admin/Request` and `Admin/Response` topics. **Do not share this with operator teams**; it grants read access to every team's telemetry, frequencies, and passwords.

Some example values you'll see in scenario JSON files for testing:

```jsonc
{
  "id": 111111,
  "password": "AAAAAA",
  "key": 6,
  "frequency": 473,
  "name": "Red Team"
}
```

Real scenarios use distinct, non-trivial passwords; the example above is for illustration only.

---

## Client libraries

Space Range does not ship its own MQTT client. Use any maintained library for your platform:

| Language | Recommended | Notes |
| --- | --- | --- |
| Python | [`paho-mqtt`](https://pypi.org/project/paho-mqtt/) | Used by the bundled `space-range-scripts` framework. |
| JavaScript / TypeScript | [`mqtt`](https://www.npmjs.com/package/mqtt) (Node) or [`mqtt`](https://www.npmjs.com/package/mqtt) over WebSockets (browser) | The Operator UI uses the WebSocket variant. |
| .NET | [`MQTTnet`](https://github.com/dotnet/MQTTnet) | |
| Rust | [`rumqttc`](https://crates.io/crates/rumqttc) | |
| Go | [`paho.mqtt.golang`](https://github.com/eclipse/paho.mqtt.golang) | |

Browser clients must use **MQTT over WebSockets**. Most brokers expose this on a separate port (e.g. `8083` for Mosquitto, `8084` for TLS).

You also need:

- A **JSON parser** (built in to most languages).
- An **XOR helper** (a few lines of code; see [Encryption walkthrough](../guides/encryption-walkthrough.md)).
- For decoding telemetry: a **Caesar helper** and an **XTCE-aware Space Packet parser**. The latter can be very small for the two messages Space Range emits today (`Ping` and `ScheduleReport`), or you can use a general XTCE library if you have one.

---

## Bundled tools (optional)

Two reference clients ship in the same repository:

- **`space-range-scripts/`** — a Python framework that handles the broker connection, encryption, scheduling, and ground / admin requests. Use it if you want to drive scenarios programmatically without rolling your own client. Setup is documented in the framework's own [`README.md`](../../README.md). These docs cover the wire formats it uses, not the framework itself.
- **`space-range-operator/`** — the React-based Operator UI. Run it locally with `npm install && npm start` from that directory, or use the production build hosted by your scenario operator. See [Operator UI quick start](operator-ui.md).

You don't have to use either; both exist as references and as turnkey tools.

---

## Sanity check

If you have everything in the table at the top of this page, you're ready to connect. The next page walks through subscribing to the session topic and confirming you see the simulation clock — the simplest possible "hello world" against a Space Range scenario.

→ [Connecting](connecting.md)
