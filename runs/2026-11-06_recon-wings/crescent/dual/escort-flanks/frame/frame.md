# Ladder frame: escort-flanks, crescent

An interlocking egg-crate of flat parts, CNC-cut from sheet, that stands on a flat table. Its top edges trace the wing's surface 3 mm inside the outer mould line: plank or fill it, fair to the frame, and the surface comes out at the designed shape. Two frames: the upper surface, and the lower surface turned over. Millimetres; x forward, y port, z up.

| | Upper frame | Lower frame |
|---|---|---|
| Ribs / stringers / joints | 19 / 24 / 30 | 19 / 24 / 30 |
| Height off the table | 162 | 160 |
| Footprint on the table (x by y) | 414 x 1654 | 414 x 1654 |

Stock: 1 sheet of 2440 x 1220 x 6 mm (MDF or birch ply); the parts use 1.36 m² of 2.98 m². Slots are 6 mm + 0.3 mm clearance, widened by 1/sin of the crossing angle where a stringer runs swept.

Files: `frame_sheet<N>.dxf` (R12, layer CUT: closed outlines with slots; LABEL: part names to engrave or ignore; SHEET: the stock, not cut) and `frame_sheet<N>.svg` to look at. Cut with a 6 mm or smaller end mill; dog-bone the slot corners if the bit is round.

Assembly:
- Ribs (`R`): `RC0000` is the root; `RP`/`RS` are port and starboard, named by their distance out in mm. Their slots open downward.
- Stringers (`S`): `SP`/`SS` port and starboard, named by the fraction of the chord they follow, and `-1`, `-2`... for the straight runs from root to tip. Their slots open upward. Their ends butt the faces of the root rib, the tip ribs and the break ribs (the ribs with no slots); glue or screw them there.
- Drop each stringer onto the ribs from above. Every part's bottom edge is the base line: screw or hot-glue them all to the table.
- Prefixes `U-` and `L-` on the sheets say which frame a part belongs to.

| Part | Frame | Kind | Length x height | Slots | Sheet |
|---|---|---|---|---|---|
| RS0827 | upper | rib | 133 x 162 | 0 | 1 |
| RS0800 | upper | rib | 131 x 147 | 3 | 1 |
| RS0700 | upper | rib | 123 x 98 | 0 | 1 |
| RS0600 | upper | rib | 121 x 69 | 3 | 1 |
| RS0500 | upper | rib | 119 x 55 | 0 | 1 |
| RS0400 | upper | rib | 114 x 47 | 3 | 1 |
| RS0300 | upper | rib | 108 x 41 | 3 | 1 |
| RS0200 | upper | rib | 108 x 37 | 0 | 1 |
| RS0100 | upper | rib | 122 x 36 | 3 | 1 |
| RC0000 | upper | rib | 158 x 38 | 0 | 1 |
| RP0100 | upper | rib | 122 x 36 | 3 | 1 |
| RP0200 | upper | rib | 108 x 37 | 0 | 1 |
| RP0300 | upper | rib | 108 x 41 | 3 | 1 |
| RP0400 | upper | rib | 114 x 47 | 3 | 1 |
| RP0500 | upper | rib | 119 x 55 | 0 | 1 |
| RP0600 | upper | rib | 121 x 69 | 3 | 1 |
| RP0700 | upper | rib | 123 x 98 | 0 | 1 |
| RP0800 | upper | rib | 131 x 147 | 3 | 1 |
| RP0827 | upper | rib | 133 x 162 | 0 | 1 |
| SP20-1 | upper | stringer | 204 x 37 | 1 | 1 |
| SP20-2 | upper | stringer | 297 x 54 | 2 | 1 |
| SP20-3 | upper | stringer | 204 x 96 | 1 | 1 |
| SP20-4 | upper | stringer | 152 x 159 | 1 | 1 |
| SP50-1 | upper | stringer | 200 x 37 | 1 | 1 |
| SP50-2 | upper | stringer | 298 x 54 | 2 | 1 |
| SP50-3 | upper | stringer | 204 x 96 | 1 | 1 |
| SP50-4 | upper | stringer | 154 x 159 | 1 | 1 |
| SP80-1 | upper | stringer | 197 x 33 | 1 | 1 |
| SP80-2 | upper | stringer | 299 x 50 | 2 | 1 |
| SP80-3 | upper | stringer | 205 x 92 | 1 | 1 |
| SP80-4 | upper | stringer | 155 x 155 | 1 | 1 |
| SS20-1 | upper | stringer | 204 x 37 | 1 | 1 |
| SS20-2 | upper | stringer | 297 x 54 | 2 | 1 |
| SS20-3 | upper | stringer | 204 x 96 | 1 | 1 |
| SS20-4 | upper | stringer | 152 x 159 | 1 | 1 |
| SS50-1 | upper | stringer | 200 x 37 | 1 | 1 |
| SS50-2 | upper | stringer | 298 x 54 | 2 | 1 |
| SS50-3 | upper | stringer | 204 x 96 | 1 | 1 |
| SS50-4 | upper | stringer | 154 x 159 | 1 | 1 |
| SS80-1 | upper | stringer | 197 x 33 | 1 | 1 |
| SS80-2 | upper | stringer | 299 x 50 | 2 | 1 |
| SS80-3 | upper | stringer | 205 x 92 | 1 | 1 |
| SS80-4 | upper | stringer | 155 x 155 | 1 | 1 |
| RS0827 | lower | rib | 133 x 29 | 0 | 1 |
| RS0800 | lower | rib | 130 x 44 | 3 | 1 |
| RS0700 | lower | rib | 123 x 93 | 0 | 1 |
| RS0600 | lower | rib | 121 x 122 | 3 | 1 |
| RS0500 | lower | rib | 119 x 136 | 0 | 1 |
| RS0400 | lower | rib | 114 x 144 | 3 | 1 |
| RS0300 | lower | rib | 108 x 150 | 3 | 1 |
| RS0200 | lower | rib | 108 x 154 | 0 | 1 |
| RS0100 | lower | rib | 122 x 157 | 3 | 1 |
| RC0000 | lower | rib | 158 x 160 | 0 | 1 |
| RP0100 | lower | rib | 122 x 157 | 3 | 1 |
| RP0200 | lower | rib | 108 x 154 | 0 | 1 |
| RP0300 | lower | rib | 108 x 150 | 3 | 1 |
| RP0400 | lower | rib | 114 x 144 | 3 | 1 |
| RP0500 | lower | rib | 119 x 136 | 0 | 1 |
| RP0600 | lower | rib | 121 x 122 | 3 | 1 |
| RP0700 | lower | rib | 123 x 93 | 0 | 1 |
| RP0800 | lower | rib | 130 x 44 | 3 | 1 |
| RP0827 | lower | rib | 133 x 29 | 0 | 1 |
| SP20-1 | lower | stringer | 204 x 160 | 1 | 1 |
| SP20-2 | lower | stringer | 297 x 154 | 2 | 1 |
| SP20-3 | lower | stringer | 204 x 136 | 1 | 1 |
| SP20-4 | lower | stringer | 152 x 92 | 1 | 1 |
| SP50-1 | lower | stringer | 200 x 158 | 1 | 1 |
| SP50-2 | lower | stringer | 298 x 153 | 2 | 1 |
| SP50-3 | lower | stringer | 204 x 135 | 1 | 1 |
| SP50-4 | lower | stringer | 154 x 91 | 1 | 1 |
| SP80-1 | lower | stringer | 197 x 154 | 1 | 1 |
| SP80-2 | lower | stringer | 299 x 151 | 2 | 1 |
| SP80-3 | lower | stringer | 205 x 133 | 1 | 1 |
| SP80-4 | lower | stringer | 155 x 89 | 1 | 1 |
| SS20-1 | lower | stringer | 204 x 160 | 1 | 1 |
| SS20-2 | lower | stringer | 297 x 154 | 2 | 1 |
| SS20-3 | lower | stringer | 204 x 136 | 1 | 1 |
| SS20-4 | lower | stringer | 152 x 92 | 1 | 1 |
| SS50-1 | lower | stringer | 200 x 158 | 1 | 1 |
| SS50-2 | lower | stringer | 298 x 153 | 2 | 1 |
| SS50-3 | lower | stringer | 204 x 135 | 1 | 1 |
| SS50-4 | lower | stringer | 154 x 91 | 1 | 1 |
| SS80-1 | lower | stringer | 197 x 154 | 1 | 1 |
| SS80-2 | lower | stringer | 299 x 151 | 2 | 1 |
| SS80-3 | lower | stringer | 205 x 133 | 1 | 1 |
| SS80-4 | lower | stringer | 155 x 89 | 1 | 1 |
