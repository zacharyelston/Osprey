# The Beet: a flying buoy, by the numbers

A circular RIB with a 360° glass observation cabin, its mass low and a coaxial rotor on a mast at the top. Each is sized for one hop: climb to 150 m at 3 m/s, look for 5 min, come down at 2 m/s and land on the water (`src/osprey/beet.py`, inputs in `design/beet.toml`, every number a REF stand-in).

Calibration: the model puts an R44 at 136 kW to hover at its max weight; it is rated 153 kW continuous and 168 kW for take-off.

## Every case, every way of powering it

| Case | Power | Max weight | Rotor | Hover | Installed | Genset | Battery | Fuel | Hull | Top of mast | Waterline | GM | Roll | Rights itself |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Beet-2 | battery-hop | 1738 kg | 8.6 m | 310 kW | 403 kW | 86 kW | 58 kWh, 446 kg | 74 kg | 4.3 m | 3.9 m | 15 cm | 7.4 m | 1.1 s | no: floats upside down past 70° |
| Beet-2 | gen-hover | 1509 kg | 8.0 m | 269 kW | 350 kW | 298 kW | 14 kWh, 89 kg | 45 kg | 4.3 m | 3.7 m | 14 cm | 8.1 m | 1.1 s | no: floats upside down past 70° |
| Beet-2 | turbogen | 1218 kg | 7.2 m | 217 kW | 282 kW | 241 kW | 12 kWh, 72 kg | 54 kg | 4.3 m | 3.6 m | 12 cm | 9.3 m | 1.0 s | no: floats upside down past 70° |
| Beet-2 | turbine | 1041 kg | 6.6 m | 186 kW | 241 kW | 0 kW | 0 kWh, 0 kg | 40 kg | 4.3 m | 3.4 m | 10 cm | 10.1 m | 0.9 s | no: floats upside down past 70° |
| Beet-4 | battery-hop | 2248 kg | 9.8 m | 401 kW | 521 kW | 111 kW | 76 kWh, 577 kg | 95 kg | 4.3 m | 4.1 m | 19 cm | 6.0 m | 1.2 s | no: floats upside down past 70° |
| Beet-4 | gen-hover | 1952 kg | 9.1 m | 348 kW | 452 kW | 386 kW | 18 kWh, 116 kg | 58 kg | 4.3 m | 4.0 m | 17 cm | 6.7 m | 1.2 s | no: floats upside down past 70° |
| Beet-4 | turbogen | 1576 kg | 8.2 m | 281 kW | 365 kW | 311 kW | 15 kWh, 93 kg | 70 kg | 4.3 m | 3.8 m | 14 cm | 7.8 m | 1.1 s | no: floats upside down past 70° |
| Beet-4 | turbine | 1347 kg | 7.6 m | 240 kW | 312 kW | 0 kW | 0 kWh, 0 kg | 52 kg | 4.3 m | 3.6 m | 13 cm | 8.6 m | 1.0 s | no: floats upside down past 70° |
| Beet-6 | battery-hop | 2758 kg | 10.8 m | 491 kW | 639 kW | 136 kW | 93 kWh, 708 kg | 117 kg | 4.3 m | 4.3 m | 23 cm | 4.9 m | 1.4 s | no: floats upside down past 70° |
| Beet-6 | gen-hover | 2396 kg | 10.1 m | 427 kW | 555 kW | 473 kW | 23 kWh, 142 kg | 71 kg | 4.3 m | 4.2 m | 20 cm | 5.6 m | 1.3 s | no: floats upside down past 70° |
| Beet-6 | turbogen | 1934 kg | 9.1 m | 344 kW | 448 kW | 382 kW | 18 kWh, 115 kg | 86 kg | 4.3 m | 4.0 m | 17 cm | 6.6 m | 1.2 s | no: floats upside down past 70° |
| Beet-6 | turbine | 1653 kg | 8.4 m | 294 kW | 383 kW | 0 kW | 0 kWh, 0 kg | 64 kg | 4.3 m | 3.8 m | 15 cm | 7.5 m | 1.1 s | no: floats upside down past 70° |
| Beet buoy | battery-hop | 276 kg | 3.4 m | 49 kW | 64 kW | 14 kW | 9 kWh, 71 kg | 12 kg | 1.5 m | 2.0 m | 20 cm | 0.5 m | 1.5 s | no: floats upside down past 40° |
| Beet buoy | gen-hover | 239 kg | 3.2 m | 43 kW | 55 kW | 47 kW | 2 kWh, 14 kg | 7 kg | 1.5 m | 1.9 m | 18 cm | 0.6 m | 1.4 s | no: floats upside down past 40° |
| Beet buoy | turbogen | 193 kg | 2.9 m | 34 kW | 45 kW | 38 kW | 2 kWh, 11 kg | 9 kg | 1.5 m | 1.9 m | 15 cm | 0.7 m | 1.2 s | no: floats upside down past 40° |
| Beet buoy | turbine | 165 kg | 2.6 m | 29 kW | 38 kW | 0 kW | 0 kWh, 0 kg | 6 kg | 1.5 m | 1.9 m | 13 cm | 0.8 m | 1.2 s | no: floats upside down past 40° |

Hover is shaft power; installed has the margin for climb and gusts. The battery-hop genset recharges the battery afloat; the others' gensets carry the hover. Fuel: four recharges for the battery hop, 30 min of hover for the rest. Waterline is above the keel.

## Where the Beet-4's weight goes

| Part | battery-hop | gen-hover | turbogen | turbine |
|---|---|---|---|---|
| payload | 380 kg | 380 kg | 380 kg | 380 kg |
| rotors | 146 kg | 127 kg | 102 kg | 88 kg |
| mast and controls | 90 kg | 78 kg | 63 kg | 54 kg |
| drive | 231 kg | 201 kg | 162 kg | 179 kg |
| hull | 261 kg | 261 kg | 261 kg | 261 kg |
| cabin glass | 133 kg | 133 kg | 133 kg | 133 kg |
| interior | 78 kg | 78 kg | 78 kg | 78 kg |
| systems | 95 kg | 89 kg | 82 kg | 77 kg |
| boat drive | 25 kg | 25 kg | 25 kg | 25 kg |
| safety | 15 kg | 15 kg | 15 kg | 15 kg |
| genset | 111 kg | 386 kg | 104 kg | 0 kg |
| fuel | 105 kg | 64 kg | 77 kg | 57 kg |
| battery | 577 kg | 116 kg | 93 kg | 0 kg |
| **total** | **2248 kg** | **1952 kg** | **1576 kg** | **1347 kg** |

## Beet-4: disc loading

| Power | Disc loading | Max weight | Rotor | Hover | Downwash |
|---|---|---|---|---|---|
| gen-hover | 15 kg/m² | 1577 kg | 11.6 m | 199 kW | 7.7 m/s |
| gen-hover | 20 kg/m² | 1699 kg | 10.4 m | 247 kW | 8.9 m/s |
| gen-hover | 30 kg/m² | 1952 kg | 9.1 m | 348 kW | 11.0 m/s |
| gen-hover | 40 kg/m² | 2233 kg | 8.4 m | 459 kW | 12.7 m/s |
| battery-hop | 15 kg/m² | 1706 kg | 12.0 m | 215 kW | 7.7 m/s |
| battery-hop | 20 kg/m² | 1875 kg | 10.9 m | 273 kW | 8.9 m/s |
| battery-hop | 30 kg/m² | 2248 kg | 9.8 m | 401 kW | 11.0 m/s |
| battery-hop | 40 kg/m² | 2702 kg | 9.3 m | 556 kW | 12.7 m/s |

## Beet-4: time at the top

| Power | At the top | Max weight | Battery |
|---|---|---|---|
| gen-hover | 2 min | 1952 kg | 18 kWh, 116 kg |
| gen-hover | 5 min | 1952 kg | 18 kWh, 116 kg |
| gen-hover | 10 min | 1952 kg | 18 kWh, 116 kg |
| gen-hover | 15 min | 1952 kg | 18 kWh, 116 kg |
| battery-hop | 2 min | 2152 kg | 43 kWh, 553 kg |
| battery-hop | 5 min | 2248 kg | 76 kWh, 577 kg |
| battery-hop | 10 min | 2832 kg | 159 kWh, 883 kg |
| battery-hop | 15 min | 5343 kg | 420 kWh, 2335 kg |
| turbine | 2 min | 1347 kg | 0 kWh, 0 kg |
| turbine | 5 min | 1347 kg | 0 kWh, 0 kg |
| turbine | 10 min | 1347 kg | 0 kWh, 0 kg |
| turbine | 15 min | 1347 kg | 0 kWh, 0 kg |

## Beet-4 battery hop: pack power

| Pack power | Max weight | Battery |
|---|---|---|
| 1 kW/kg | 2248 kg | 76 kWh, 577 kg |
| 2 kW/kg | 1927 kg | 65 kWh, 360 kg |
| 3 kW/kg | 1927 kg | 65 kWh, 360 kg |

## Beet-4 hybrid: will it always come back upright?

The cabin's roof radius over its floor's (1 is a cylinder, lower a cone, like the Roton's) and a keel pod under the hull holding the battery, genset and fuel.

| Roof / floor | Keel pod | Max weight | CG above keel | Waterline | GM | Rights itself | Least GZ |
|---|---|---|---|---|---|---|---|
| 1.00 | 0.0 m | 2089 kg | 0.99 m | 18 cm | 6.3 m | no: floats upside down past 70° | -60 cm |
| 1.00 | 0.5 m | 2089 kg | 0.87 m | 16 cm | 6.0 m | no: floats upside down past 80° | -49 cm |
| 1.00 | 1.0 m | 2089 kg | 0.80 m | 13 cm | 5.5 m | no: floats upside down past 80° | -43 cm |
| 0.55 | 0.0 m | 1952 kg | 0.97 m | 17 cm | 6.7 m | no: floats upside down past 70° | -84 cm |
| 0.55 | 0.5 m | 1952 kg | 0.85 m | 15 cm | 6.3 m | no: floats upside down past 80° | -74 cm |
| 0.55 | 1.0 m | 1952 kg | 0.77 m | 12 cm | 5.6 m | no: floats upside down past 80° | -68 cm |
| 0.35 | 0.0 m | 1914 kg | 0.96 m | 17 cm | 6.8 m | no: floats upside down past 70° | -95 cm |
| 0.35 | 0.5 m | 1914 kg | 0.84 m | 14 cm | 6.4 m | no: floats upside down past 80° | -85 cm |
| 0.35 | 1.0 m | 1914 kg | 0.77 m | 12 cm | 5.7 m | no: floats upside down past 80° | -78 cm |
