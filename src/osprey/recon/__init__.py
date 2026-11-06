"""Osprey Recon: the search-and-rescue drone launched from and recovered to
the boat. Mission profiles in design/recon/missions drive a search-theory
model, a 3-DOF flight simulation and an OpenMDAO / OpenAeroStruct sizing loop
for a printed fixed-wing airframe (design/recon/airframe.toml)."""

import os as _os

from osprey.params import OUT as _OUT

# OpenMDAO writes <problem>_out folders (colorings, reports) into its work
# directory; keep them in the gitignored out/ rather than wherever we run.
_os.environ.setdefault("OPENMDAO_WORKDIR", str(_OUT / "openmdao"))
_os.environ.setdefault("OPENMDAO_REPORTS", "0")
