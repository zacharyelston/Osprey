# Ladder frame: escort-flanks, bwb

An interlocking egg-crate of flat parts, CNC-cut from sheet, that stands on a flat table. Its top edges trace the wing's surface 3 mm inside the outer mould line: plank or fill it, fair to the frame, and the surface comes out at the designed shape. Two frames: the upper surface, and the lower surface turned over. Millimetres; x forward, y port, z up.

| | Upper frame | Lower frame |
|---|---|---|
| Ribs / stringers / joints | 13 / 12 / 24 | 13 / 12 / 24 |
| Height off the table | 93 | 79 |
| Footprint on the table (x by y) | 569 x 1107 | 569 x 1107 |

Stock: 1 sheet of 2440 x 1220 x 6 mm (MDF or birch ply); the parts use 0.65 m² of 2.98 m². Slots are 6 mm + 0.3 mm clearance, widened by 1/sin of the crossing angle where a stringer runs swept.

Files: `frame_sheet<N>.dxf` (R12, layer CUT: closed outlines with slots; LABEL: part names to engrave or ignore; SHEET: the stock, not cut) and `frame_sheet<N>.svg` to look at. Cut with a 6 mm or smaller end mill; dog-bone the slot corners if the bit is round.

Assembly:
- Ribs (`R`): `RC0000` is the root; `RP`/`RS` are port and starboard, named by their distance out in mm. Their slots open downward.
- Stringers (`S`): `SP`/`SS` port and starboard, named by the fraction of the chord they follow, and `-1`, `-2`... for the straight runs from root to tip. Their slots open upward. Their ends butt the faces of the root rib, the tip ribs and the break ribs (the ribs with no slots); glue or screw them there.
- Drop each stringer onto the ribs from above. Every part's bottom edge is the base line: screw or hot-glue them all to the table.
- Prefixes `U-` and `L-` on the sheets say which frame a part belongs to.

| Part | Frame | Kind | Length x height | Slots | Sheet |
|---|---|---|---|---|---|
| RS0554 | upper | rib | 127 x 35 | 0 | 1 |
| RS0500 | upper | rib | 115 x 36 | 3 | 1 |
| RS0400 | upper | rib | 106 x 39 | 3 | 1 |
| RS0300 | upper | rib | 124 x 43 | 0 | 1 |
| RS0200 | upper | rib | 180 x 51 | 3 | 1 |
| RS0100 | upper | rib | 282 x 67 | 3 | 1 |
| RC0000 | upper | rib | 440 x 93 | 0 | 1 |
| RP0100 | upper | rib | 282 x 67 | 3 | 1 |
| RP0200 | upper | rib | 180 x 51 | 3 | 1 |
| RP0300 | upper | rib | 124 x 43 | 0 | 1 |
| RP0400 | upper | rib | 106 x 39 | 3 | 1 |
| RP0500 | upper | rib | 115 x 36 | 3 | 1 |
| RP0554 | upper | rib | 127 x 35 | 0 | 1 |
| SP20-1 | upper | stringer | 360 x 84 | 2 | 1 |
| SP20-2 | upper | stringer | 296 x 40 | 2 | 1 |
| SP50-1 | upper | stringer | 316 x 91 | 2 | 1 |
| SP50-2 | upper | stringer | 296 x 43 | 2 | 1 |
| SP80-1 | upper | stringer | 295 x 80 | 2 | 1 |
| SP80-2 | upper | stringer | 297 x 41 | 2 | 1 |
| SS20-1 | upper | stringer | 360 x 84 | 2 | 1 |
| SS20-2 | upper | stringer | 296 x 40 | 2 | 1 |
| SS50-1 | upper | stringer | 316 x 91 | 2 | 1 |
| SS50-2 | upper | stringer | 296 x 43 | 2 | 1 |
| SS80-1 | upper | stringer | 295 x 80 | 2 | 1 |
| SS80-2 | upper | stringer | 297 x 41 | 2 | 1 |
| RS0554 | lower | rib | 127 x 68 | 0 | 1 |
| RS0500 | lower | rib | 115 x 67 | 3 | 1 |
| RS0400 | lower | rib | 106 x 65 | 3 | 1 |
| RS0300 | lower | rib | 124 x 65 | 0 | 1 |
| RS0200 | lower | rib | 180 x 67 | 3 | 1 |
| RS0100 | lower | rib | 282 x 71 | 3 | 1 |
| RC0000 | lower | rib | 440 x 79 | 0 | 1 |
| RP0100 | lower | rib | 282 x 71 | 3 | 1 |
| RP0200 | lower | rib | 180 x 67 | 3 | 1 |
| RP0300 | lower | rib | 124 x 65 | 0 | 1 |
| RP0400 | lower | rib | 106 x 65 | 3 | 1 |
| RP0500 | lower | rib | 115 x 67 | 3 | 1 |
| RP0554 | lower | rib | 127 x 68 | 0 | 1 |
| SP20-1 | lower | stringer | 360 x 78 | 2 | 1 |
| SP20-2 | lower | stringer | 296 x 68 | 2 | 1 |
| SP50-1 | lower | stringer | 316 x 65 | 2 | 1 |
| SP50-2 | lower | stringer | 296 x 68 | 2 | 1 |
| SP80-1 | lower | stringer | 295 x 56 | 2 | 1 |
| SP80-2 | lower | stringer | 297 x 66 | 2 | 1 |
| SS20-1 | lower | stringer | 360 x 78 | 2 | 1 |
| SS20-2 | lower | stringer | 296 x 68 | 2 | 1 |
| SS50-1 | lower | stringer | 316 x 65 | 2 | 1 |
| SS50-2 | lower | stringer | 296 x 68 | 2 | 1 |
| SS80-1 | lower | stringer | 295 x 56 | 2 | 1 |
| SS80-2 | lower | stringer | 297 x 66 | 2 | 1 |
