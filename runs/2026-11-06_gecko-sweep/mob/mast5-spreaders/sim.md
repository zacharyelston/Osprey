# Looking groups: mob on mast5-spreaders (reserve 1, max group 4)

Generated 2026-11-06 at unknown by `uv run osprey sim --scenario mob --rig mast5-spreaders`.

A camera always on watch: **yes**. Whole horizon swept: **0%** of the time (worst moment 88%); worst-bearing revisit inf s median, inf s p95. Pairs in groups: 0 within a pod, 1800 across pods (pair-ticks).

| Task | Class | Need | Priority | Need met | Group median / max | px median | Range σ/R median | Starved |
|---|---|---|---|---|---|---|---|---|
| mob | person in water | recognize | 0 | 99% | 4 / 4 | 80 | 0.1% | 0% |
| buoy-2 | lobster buoy | detect | 2 | 0% | 0 / 0 | 0 | inf% | 100% |

| Station | Tasked | Slewing | Watch |
|---|---|---|---|
| top | 99% | 1% | 0% |
| fwd | 0% | 0% | 100% |
| port | 99% | 1% | 0% |
| stbd | 99% | 1% | 0% |
| aft | 99% | 1% | 0% |

![groups](groups.png)
