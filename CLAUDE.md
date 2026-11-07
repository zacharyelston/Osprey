# Working in Osprey

- **Branches and PRs:** after the initial commit, make every change on a branch (`feat/…`, `fix/…`, `chore/…`) and merge through a PR into `main`. Never commit credentials, keys or personal data.
- **Design inputs live in `design/`** as TOML: the boat, sea states, camera classes, target classes, rigs and scenarios. Code reads them; it never hard-codes a boat or camera number. Values marked REF are stand-ins until measured.
- **Frames:** body frame is x forward, y port, z up from the waterline under the mast; world is ENU. Roll + is starboard down, pitch + is bow down, nautical bearings are clockwise from the bow. See `src/osprey/frames.py`.
- **Rigs:** a rig is a list of camera stations. New cameras (deck, cabin, dockside) are new stations in a rig file, with `zones` saying what they can serve; `include` extends another rig. The tasking, calcs and renderer take any number of stations.
- **Outputs:** `out/` is gitignored scratch. Runs worth keeping are copied to `runs/<date>_<name>/` with the source SHA and listed in `runs/README.md`. Never edit an archived run.
- **Remote runs:** ML hosts run a `git archive` snapshot of a commit, never a working tree. See `docs/remote-simulation.md`.
- **Recon:** the drone lives in `src/osprey/recon` with inputs in `design/recon`. Sizing is OpenMDAO + OpenAeroStruct; keep derivatives analytic or complex-step (no `abs()`, `max()` or branches on complex values) and check them with `check_totals`. OpenMDAO's work folders go to `out/openmdao`.
- **Public repo:** never commit internal hostnames, logins, company domains or other projects' names; the compute hosts are `gpu1` and `gpu2`.
- **Checks:** `uv run pytest` before any commit; `uv run osprey calc` exits 1 on a FAIL, which is a design finding, not a crash.
