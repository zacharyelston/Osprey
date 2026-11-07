# Ladder frame: sar-offshore, crescent

An interlocking egg-crate of flat parts, CNC-cut from sheet, that stands on a flat table. Its top edges trace the wing's surface 3 mm inside the outer mould line: plank or fill it, fair to the frame, and the surface comes out at the designed shape. Two frames: the upper surface, and the lower surface turned over. Millimetres; x forward, y port, z up.

| | Upper frame | Lower frame |
|---|---|---|
| Ribs / stringers / joints | 21 / 24 / 36 | 21 / 24 / 36 |
| Height off the table | 160 | 157 |
| Footprint on the table (x by y) | 579 x 1939 | 579 x 1939 |

Stock: 1 sheet of 2440 x 1220 x 6 mm (MDF or birch ply); the parts use 1.63 m² of 2.98 m². Slots are 6 mm + 0.3 mm clearance, widened by 1/sin of the crossing angle where a stringer runs swept.

Files: `frame_sheet<N>.dxf` (R12, layer CUT: closed outlines with slots; LABEL: part names to engrave or ignore; SHEET: the stock, not cut) and `frame_sheet<N>.svg` to look at. Cut with a 6 mm or smaller end mill; dog-bone the slot corners if the bit is round.

Assembly:
- Ribs (`R`): `RC0000` is the root; `RP`/`RS` are port and starboard, named by their distance out in mm. Their slots open downward.
- Stringers (`S`): `SP`/`SS` port and starboard, named by the fraction of the chord they follow, and `-1`, `-2`... for the straight runs from root to tip. Their slots open upward. Their ends butt the faces of the root rib, the tip ribs and the break ribs (the ribs with no slots); glue or screw them there.
- Drop each stringer onto the ribs from above. Every part's bottom edge is the base line: screw or hot-glue them all to the table.
- Prefixes `U-` and `L-` on the sheets say which frame a part belongs to.

| Part | Frame | Kind | Length x height | Slots | Sheet |
|---|---|---|---|---|---|
| RS0970 | upper | rib | 133 x 160 | 0 | 1 |
| RS0900 | upper | rib | 130 x 128 | 3 | 1 |
| RS0800 | upper | rib | 126 x 92 | 0 | 1 |
| RS0700 | upper | rib | 124 x 68 | 3 | 1 |
| RS0600 | upper | rib | 122 x 56 | 0 | 1 |
| RS0500 | upper | rib | 120 x 47 | 3 | 1 |
| RS0400 | upper | rib | 118 x 41 | 3 | 1 |
| RS0300 | upper | rib | 115 x 37 | 0 | 1 |
| RS0200 | upper | rib | 117 x 35 | 3 | 1 |
| RS0100 | upper | rib | 122 x 36 | 3 | 1 |
| RC0000 | upper | rib | 133 x 40 | 0 | 1 |
| RP0100 | upper | rib | 122 x 36 | 3 | 1 |
| RP0200 | upper | rib | 117 x 35 | 3 | 1 |
| RP0300 | upper | rib | 115 x 37 | 0 | 1 |
| RP0400 | upper | rib | 118 x 41 | 3 | 1 |
| RP0500 | upper | rib | 120 x 47 | 3 | 1 |
| RP0600 | upper | rib | 122 x 56 | 0 | 1 |
| RP0700 | upper | rib | 124 x 68 | 3 | 1 |
| RP0800 | upper | rib | 126 x 92 | 0 | 1 |
| RP0900 | upper | rib | 130 x 128 | 3 | 1 |
| RP0970 | upper | rib | 133 x 160 | 0 | 1 |
| SP20-1 | upper | stringer | 321 x 37 | 2 | 1 |
| SP20-2 | upper | stringer | 302 x 55 | 2 | 1 |
| SP20-3 | upper | stringer | 207 x 91 | 1 | 1 |
| SP20-4 | upper | stringer | 229 x 158 | 1 | 1 |
| SP50-1 | upper | stringer | 319 x 40 | 2 | 1 |
| SP50-2 | upper | stringer | 303 x 54 | 2 | 1 |
| SP50-3 | upper | stringer | 207 x 91 | 1 | 1 |
| SP50-4 | upper | stringer | 230 x 157 | 1 | 1 |
| SP80-1 | upper | stringer | 317 x 38 | 2 | 1 |
| SP80-2 | upper | stringer | 303 x 50 | 2 | 1 |
| SP80-3 | upper | stringer | 208 x 87 | 1 | 1 |
| SP80-4 | upper | stringer | 232 x 152 | 1 | 1 |
| SS20-1 | upper | stringer | 321 x 37 | 2 | 1 |
| SS20-2 | upper | stringer | 302 x 55 | 2 | 1 |
| SS20-3 | upper | stringer | 207 x 91 | 1 | 1 |
| SS20-4 | upper | stringer | 229 x 158 | 1 | 1 |
| SS50-1 | upper | stringer | 319 x 40 | 2 | 1 |
| SS50-2 | upper | stringer | 303 x 54 | 2 | 1 |
| SS50-3 | upper | stringer | 207 x 91 | 1 | 1 |
| SS50-4 | upper | stringer | 230 x 157 | 1 | 1 |
| SS80-1 | upper | stringer | 317 x 38 | 2 | 1 |
| SS80-2 | upper | stringer | 303 x 50 | 2 | 1 |
| SS80-3 | upper | stringer | 208 x 87 | 1 | 1 |
| SS80-4 | upper | stringer | 232 x 152 | 1 | 1 |
| RS0970 | lower | rib | 133 x 30 | 0 | 1 |
| RS0900 | lower | rib | 130 x 62 | 3 | 1 |
| RS0800 | lower | rib | 126 x 98 | 0 | 1 |
| RS0700 | lower | rib | 124 x 122 | 3 | 1 |
| RS0600 | lower | rib | 122 x 135 | 0 | 1 |
| RS0500 | lower | rib | 120 x 144 | 3 | 1 |
| RS0400 | lower | rib | 118 x 150 | 3 | 1 |
| RS0300 | lower | rib | 115 x 154 | 0 | 1 |
| RS0200 | lower | rib | 117 x 156 | 3 | 1 |
| RS0100 | lower | rib | 122 x 157 | 3 | 1 |
| RC0000 | lower | rib | 133 x 156 | 0 | 1 |
| RP0100 | lower | rib | 122 x 157 | 3 | 1 |
| RP0200 | lower | rib | 117 x 156 | 3 | 1 |
| RP0300 | lower | rib | 115 x 154 | 0 | 1 |
| RP0400 | lower | rib | 118 x 150 | 3 | 1 |
| RP0500 | lower | rib | 120 x 144 | 3 | 1 |
| RP0600 | lower | rib | 122 x 135 | 0 | 1 |
| RP0700 | lower | rib | 124 x 122 | 3 | 1 |
| RP0800 | lower | rib | 126 x 98 | 0 | 1 |
| RP0900 | lower | rib | 130 x 62 | 3 | 1 |
| RP0970 | lower | rib | 133 x 30 | 0 | 1 |
| SP20-1 | lower | stringer | 321 x 157 | 2 | 1 |
| SP20-2 | lower | stringer | 302 x 154 | 2 | 1 |
| SP20-3 | lower | stringer | 207 x 135 | 1 | 1 |
| SP20-4 | lower | stringer | 229 x 97 | 1 | 1 |
| SP50-1 | lower | stringer | 319 x 156 | 2 | 1 |
| SP50-2 | lower | stringer | 303 x 153 | 2 | 1 |
| SP50-3 | lower | stringer | 207 x 134 | 1 | 1 |
| SP50-4 | lower | stringer | 230 x 96 | 1 | 1 |
| SP80-1 | lower | stringer | 317 x 153 | 2 | 1 |
| SP80-2 | lower | stringer | 303 x 152 | 2 | 1 |
| SP80-3 | lower | stringer | 208 x 132 | 1 | 1 |
| SP80-4 | lower | stringer | 232 x 94 | 1 | 1 |
| SS20-1 | lower | stringer | 321 x 157 | 2 | 1 |
| SS20-2 | lower | stringer | 302 x 154 | 2 | 1 |
| SS20-3 | lower | stringer | 207 x 135 | 1 | 1 |
| SS20-4 | lower | stringer | 229 x 97 | 1 | 1 |
| SS50-1 | lower | stringer | 319 x 156 | 2 | 1 |
| SS50-2 | lower | stringer | 303 x 153 | 2 | 1 |
| SS50-3 | lower | stringer | 207 x 134 | 1 | 1 |
| SS50-4 | lower | stringer | 230 x 96 | 1 | 1 |
| SS80-1 | lower | stringer | 317 x 153 | 2 | 1 |
| SS80-2 | lower | stringer | 303 x 152 | 2 | 1 |
| SS80-3 | lower | stringer | 208 x 132 | 1 | 1 |
| SS80-4 | lower | stringer | 232 x 94 | 1 | 1 |
