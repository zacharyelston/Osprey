# Osprey sweep

Generated 2026-11-06 at unknown by `uv run osprey sweep --workers 24`.

| Scenario | Rig | FAIL / WARN / PASS | Always a camera on watch | Whole horizon swept | Task needs met |
|---|---|---|---|---|---|
| coastal-watch | gecko5 | 4 / 21 / 16 | yes | 100% (8 s revisit) | buoy-1 80%, kayak 88%, ferry 84%, sloop 99% |
| coastal-watch | mast5 | 0 / 12 / 5 | yes | 0% (inf s revisit) | buoy-1 87%, kayak 57%, ferry 0%, sloop 96% |
| coastal-watch | mast5-spreaders | 0 / 12 / 5 | yes | 0% (inf s revisit) | buoy-1 86%, kayak 84%, ferry 86%, sloop 88% |
| coastal-watch | whole-boat | 0 / 12 / 9 | yes | 0% (inf s revisit) | buoy-1 87%, kayak 57%, ferry 0%, sloop 97% |
| docking | gecko5 | 3 / 3 / 45 | yes | 100% (1 s revisit) |  |
| docking | mast5 | 2 / 1 / 19 | yes | 100% (2 s revisit) |  |
| docking | mast5-spreaders | 3 / 1 / 18 | yes | 100% (2 s revisit) |  |
| docking | whole-boat | 1 / 2 / 23 | yes | 100% (2 s revisit) |  |
| mob | gecko5 | 4 / 0 / 34 | yes | 100% (8 s revisit) | mob 99%, buoy-2 99% |
| mob | mast5 | 0 / 1 / 13 | yes | 0% (inf s revisit) | mob 99%, buoy-2 99% |
| mob | mast5-spreaders | 0 / 1 / 13 | yes | 0% (inf s revisit) | mob 99%, buoy-2 0% |
| mob | whole-boat | 0 / 1 / 17 | yes | 0% (inf s revisit) | mob 99%, buoy-2 99% |
