# `ground_stations` — receiving network

The `ground_stations` block defines the pool of ground stations available to **every** team. There is no per-team ground network — every station is shared. It maps to `FGroundStationsDefinition` in `studio/Plugins/SpaceRange/Source/SpaceRange/Public/Definitions/GroundStationsDefinition.h`.

```json
"ground_stations": {
  "locations": [
    "Madrid", "Dubai", "Singapore", "Auckland",
    "Easter Island", "Salvador", "Miami"
  ],
  "min_elevation": 0,
  "max_range":     0,
  "scale":         100
}
```

## Fields

| Key | JSON type | Default | Description |
| --- | --- | --- | --- |
| `locations` | `string[]` | _(empty)_ | City names. Each one matches an entry in Studio's built-in city table and instantiates a ground station at that city's coordinates. Duplicates are allowed but pointless. |
| `min_elevation` | `number` (deg) | `0` | Minimum elevation above the local horizon for a station to be considered "in view" of a spacecraft. `0` means at-the-horizon counts; `5–10` is realistic for masking effects. |
| `max_range` | `number` (km) | `0` | Maximum slant range over which a link can close. `0` means unlimited (link budget alone gates it). Use a finite value to cut off pathologically long links explicitly. |
| `scale` | `number` | `100` | Visual scale factor for ground-station markers in the world view. Doesn't affect simulation, only rendering. |

## Notes

- The first station in `locations` is treated specially: the per-team ground controllers are attached to it and inherit its default transmitter power, antenna gain, and bandwidth. Pick the most "central" or "primary" station as the first entry.
- Whether a spacecraft can talk to a station at runtime is gated by the link budget plus `min_elevation` and `max_range`. Teams choose which station to communicate with operationally — typically by setting [`guidance` mode](../api-reference/spacecraft-commands.md#guidance) to `"ground"` and pointing the antenna at the station of interest.
- Ground stations are **not** owned by teams — every team can request a downlink through any station whose link budget closes. To force a team to use a particular station, control it through scenario narrative (briefing, scoring) rather than configuration.

## Picking locations

Studio ships with a comprehensive city table — most major capitals and many secondary cities are available. The shipped scenarios use these patterns:

- **Global coverage** (`Orbital Sentinel`): seven well-spread stations so every spacecraft has a close contact. `Madrid`, `Dubai`, `Singapore`, `Auckland`, `Easter Island`, `Salvador`, `Miami`.
- **Regional coverage** (`Docking_Procedure`): a hemisphere-biased cluster for an exercise focused on a particular orbit. `Paris`, `Dubai`, `Colombo`, `Singapore`, `Sydney`, `Auckland`, `Lima`, `New York`.
- **Polar coverage** (`Telemetry_Drop`): includes `Amundsen-Scott` so that polar-orbit spacecraft are visible at most points of their orbit.

If a city name is not recognised, Studio logs a warning and skips it during load. Confirm the loaded set with [`admin_list_entities`](../api-reference/admin-requests.md#admin_list_entities) after a load.

---

## Built-in location catalog

The full table below is the authoritative city list, mirrored from `studio/Plugins/ZendirForUnreal/Source/ZenFramework/Private/Libraries/GeodeticLibrary.cpp` (`UGeodeticLibrary::GetGeodeticLocations`). Names are matched **case-sensitive** — spell them exactly as listed.

Coordinates are geodetic `(lat°, lon°, alt m)` on each planet's WGS-84-equivalent reference ellipsoid. Altitude is `0.0 m` unless noted.

### Earth — 100 cities

| City | Lat (°) | Lon (°) | Alt (m) |
| --- | ---: | ---: | ---: |
| Abu Dhabi | 24.4539 | 54.3773 | 0 |
| Adelaide | -34.9285 | 138.6007 | 0 |
| Addis Ababa | 9.03 | 38.74 | 0 |
| Amsterdam | 52.3676 | 4.9041 | 0 |
| Amundsen-Scott | -89.99 | 0.00 | 2835 |
| Anchorage | 61.2181 | -149.9003 | 0 |
| Ankara | 39.9334 | 32.8597 | 0 |
| Athens | 37.9838 | 23.7275 | 0 |
| Auckland | -36.8485 | 174.7633 | 0 |
| Baghdad | 33.3128 | 44.3615 | 0 |
| Bangkok | 13.7563 | 100.5018 | 0 |
| Barcelona | 41.3851 | 2.1734 | 0 |
| Beijing | 39.9042 | 116.4074 | 0 |
| Bengaluru | 12.9716 | 77.5946 | 0 |
| Berlin | 52.5200 | 13.4050 | 0 |
| Boca Chica | 25.9972 | -97.1566 | 0 |
| Bogota | 4.7110 | -74.0721 | 0 |
| Brasilia | -15.7801 | -47.9292 | 0 |
| Brisbane | -27.4698 | 153.0251 | 0 |
| Brussels | 50.8503 | 4.3517 | 0 |
| Budapest | 47.4979 | 19.0402 | 0 |
| Buenos Aires | -34.6037 | -58.3816 | 0 |
| Cairo | 30.0444 | 31.2357 | 0 |
| Cairns | -16.9186 | 145.7781 | 0 |
| Canberra | -35.2809 | 149.1300 | 0 |
| Cape Canaveral | 28.3922 | -80.6077 | 0 |
| Cape Town | -33.9249 | 18.4241 | 0 |
| Caracas | 10.4806 | -66.9036 | 0 |
| Casablanca | 33.5731 | -7.5898 | 0 |
| Chicago | 41.8781 | -87.6298 | 0 |
| Colombo | 6.9271 | 79.8612 | 0 |
| Copenhagen | 55.6761 | 12.5683 | 0 |
| Dallas | 32.7767 | -96.7970 | 0 |
| Darwin | -12.4634 | 130.8456 | 0 |
| Davao | 7.1907 | 125.4553 | 0 |
| Delhi | 28.6139 | 77.2090 | 0 |
| Denver | 39.7392 | -104.9903 | 0 |
| Dhaka | 23.8103 | 90.4125 | 0 |
| Doha | 25.2854 | 51.5310 | 0 |
| Dubai | 25.276987 | 55.296249 | 0 |
| Dublin | 53.3498 | -6.2603 | 0 |
| Easter Island | -27.1127 | -109.3497 | 0 |
| Edinburgh | 55.9533 | -3.1883 | 0 |
| Frankfurt | 50.1109 | 8.6821 | 0 |
| Geneva | 46.2044 | 6.1432 | 0 |
| Guangzhou | 23.1291 | 113.2644 | 0 |
| Hanoi | 21.0285 | 105.8542 | 0 |
| Havana | 23.1136 | -82.3666 | 0 |
| Helsinki | 60.1695 | 24.9354 | 0 |
| Ho Chi Minh City | 10.7626 | 106.6602 | 0 |
| Hobart | -42.8821 | 147.3272 | 0 |
| Hong Kong | 22.3964 | 114.1095 | 0 |
| Honolulu | 21.3069 | -157.8583 | 0 |
| Houston | 29.7604 | -95.3698 | 0 |
| Istanbul | 41.0082 | 28.9784 | 0 |
| Jakarta | -6.2088 | 106.8456 | 0 |
| Johannesburg | -26.2041 | 28.0473 | 0 |
| Karachi | 24.8607 | 67.0011 | 0 |
| Kathmandu | 27.7172 | 85.3240 | 0 |
| Kinshasa | -4.4419 | 15.2663 | 0 |
| Kourou | 5.2057 | -52.7333 | 0 |
| Kuala Lumpur | 3.1390 | 101.6869 | 0 |
| Kuwait City | 29.3759 | 47.9774 | 0 |
| Kyiv | 50.4501 | 30.5234 | 0 |
| La Paz | -16.4897 | -68.1193 | 3640 |
| Lagos | 6.5244 | 3.3792 | 0 |
| Lisbon | 38.7223 | -9.1393 | 0 |
| Lima | -12.0464 | -77.0428 | 0 |
| London | 51.5074 | -0.1278 | 0 |
| Los Angeles | 34.0522 | -118.2437 | 0 |
| Luanda | -8.8390 | 13.2894 | 0 |
| Lusaka | -15.3875 | 28.3228 | 0 |
| Madrid | 40.4168 | -3.7038 | 0 |
| Male | 4.1755 | 73.5093 | 0 |
| Manila | 14.5995 | 120.9842 | 0 |
| Marrakech | 31.6295 | -7.9811 | 0 |
| Melbourne | -37.8136 | 144.9631 | 0 |
| Mexico City | 19.4326 | -99.1332 | 0 |
| Miami | 25.7617 | -80.1918 | 0 |
| Milan | 45.4642 | 9.1900 | 0 |
| Montreal | 45.5017 | -73.5673 | 0 |
| Moscow | 55.7558 | 37.6173 | 0 |
| Mumbai | 19.0760 | 72.8777 | 0 |
| Munich | 48.1351 | 11.5820 | 0 |
| Nadi | -24.9580 | 25.5878 | 0 |
| Nairobi | -1.286389 | 36.817223 | 0 |
| New York | 40.7128 | -74.0060 | 0 |
| Noumea | -22.2558 | 166.4505 | 0 |
| Osaka | 34.6937 | 135.5023 | 0 |
| Oslo | 59.9139 | 10.7522 | 0 |
| Paris | 48.8566 | 2.3522 | 0 |
| Perth | -31.9505 | 115.8605 | 0 |
| Port Louis | -20.1609 | 57.5012 | 0 |
| Prague | 50.0755 | 14.4378 | 0 |
| Reykjavik | 64.1355 | -21.8954 | 0 |
| Rio de Janeiro | -22.9068 | -43.1729 | 0 |
| Riyadh | 24.7136 | 46.6753 | 0 |
| Rome | 41.9028 | 12.4964 | 0 |
| Salvador | -12.9777 | -38.5016 | 0 |
| San Francisco | 37.7749 | -122.4194 | 0 |
| Santiago | -33.4489 | -70.6693 | 0 |
| Sao Paulo | -23.5505 | -46.6333 | 0 |
| Seattle | 47.6062 | -122.3321 | 0 |
| Seoul | 37.5665 | 126.9780 | 0 |
| Shanghai | 31.2304 | 121.4737 | 0 |
| Shenzhen | 22.5431 | 114.0579 | 0 |
| Singapore | 1.3521 | 103.8198 | 0 |
| Stockholm | 59.3293 | 18.0686 | 0 |
| Sydney | -33.8688 | 151.2093 | 0 |
| Taipei | 25.0330 | 121.5654 | 0 |
| Tehran | 35.6892 | 51.3890 | 0 |
| Tel Aviv | 32.0853 | 34.7818 | 0 |
| Tokyo | 35.6895 | 139.6917 | 0 |
| Toronto | 43.6532 | -79.3832 | 0 |
| Ulaanbaatar | 47.8864 | 106.9050 | 0 |
| Warsaw | 52.2297 | 21.0122 | 0 |
| Washington D.C. | 38.9072 | -77.0369 | 0 |
| Wellington | -41.2865 | 174.7762 | 0 |
| Vancouver | 49.2827 | -123.1207 | 0 |
| Vienna | 48.2082 | 16.3738 | 0 |
| Yangon | 16.8409 | 96.1735 | 0 |
| Zagreb | 45.8150 | 15.9819 | 0 |
| Zurich | 47.3769 | 8.5417 | 0 |

> `Amundsen-Scott` is the only Earth location with a non-zero altitude
> (2 835 m — the South Pole research station). `La Paz` is set at 3 640 m.
> Every other city is on the ellipsoid surface.

### Moon

The Moon catalog is available when a scenario uses `"planet": "Moon"` for an
asset or ground feature. Coordinates are selenographic.

| Location | Lat (°) | Lon (°) | Notes |
| --- | ---: | ---: | --- |
| **Apollo landing sites** | | | |
| Apollo 11 | 0.67408 | 23.47297 | Tranquility Base |
| Apollo 12 | -3.01239 | -23.42157 | Surveyor Crater |
| Apollo 14 | -3.64530 | -17.47136 | Fra Mauro |
| Apollo 15 | 26.13222 | 3.63386 | Hadley Rille |
| Apollo 16 | -8.97301 | 15.50019 | Descartes Highlands |
| Apollo 17 | 20.19080 | 30.77168 | Taurus-Littrow |
| **Historic uncrewed landers** | | | |
| Luna 2 | 29.1000 | 0.0000 | First human-made object on the Moon |
| Luna 9 | 7.0833 | -64.3667 | First soft landing |
| Lunokhod 1 | 38.3215 | -35.0000 | First robotic rover |
| Surveyor 1 | -2.4745 | -43.3394 | First US soft landing |
| **Modern landers** | | | |
| Chang'e 3 | 44.1206 | -19.5116 | Mare Imbrium |
| Chang'e 4 | -45.4446 | 177.5991 | Von Kármán crater (Far Side) |
| Chandrayaan-3 | -69.3730 | 32.3190 | Shiv Shakti Point (South Pole) |
| SLIM | -13.3160 | 25.2510 | Shioli Crater (Japan) |
| IM-1 Odysseus | -80.1270 | 1.4400 | Malapert A (Commercial US) |
| **Lunar features** | | | |
| Shackleton Crater | -89.6600 | 129.2000 | Lunar South Pole |
| Tycho Crater | -43.3000 | -11.2200 | |
| Copernicus Crater | 9.6200 | -20.0800 | |

### Mars

Available when an asset or feature uses `"planet": "Mars"`. Areocentric coordinates.

| Location | Lat (°) | Lon (°) | Region |
| --- | ---: | ---: | --- |
| Viking 1 | 22.697 | -48.222 | Chryse Planitia |
| Viking 2 | 47.664 | 134.285 | Utopia Planitia |
| Pathfinder | 19.13 | 33.22 | Ares Vallis |
| Spirit | -14.5684 | 175.472636 | Gusev Crater |
| Opportunity | -1.9462 | 354.4734 | Meridiani Planum |
| Curiosity | -4.5895 | 137.4417 | Gale Crater |
| Perseverance | 18.4447 | 77.4508 | Jezero Crater |
