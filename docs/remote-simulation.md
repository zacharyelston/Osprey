# Remote runs on the ML hosts

Two Linux workstations take Osprey's CPU sweeps and GPU (EGL) renders. Both
are ThinkStation P620s with 32 hardware threads on Ubuntu 20.04.

| Host | Login | GPUs | RAM | uv |
|---|---|---|---|---|
| gpu1 | `user@gpu1` | Quadro RTX 8000 48 GB, RTX 6000 24 GB | 125 GB | `~/.local/bin/uv` |
| gpu2 | `user@gpu2` (a dev host, despite the name) | 2x Quadro RTX 6000 24 GB | 157 GB | install to `~/.local/bin/uv` |

Checked 2026-11-06. Both were idle; check `nvidia-smi` and `uptime` before a
long job, since other projects (eOx) share gpu1.

## Ship a committed snapshot

Uncommitted edits do not travel. Record the SHA with the results.

```bash
HOST=user@gpu1       # or user@gpu2
SHA=$(git rev-parse --short HEAD)
git archive --format=tar HEAD -o /tmp/osprey-$SHA.tar
RUN=$(ssh $HOST 'mkdir -p ~/osprey-sim && mktemp -d ~/osprey-sim/run-XXXXXX')
scp /tmp/osprey-$SHA.tar $HOST:$RUN/source.tar
ssh $HOST "cd $RUN && tar -xf source.tar && rm source.tar && echo $SHA > SOURCE_SHA && ~/.local/bin/uv sync --python 3.12"
```

## Sweep every scenario and rig (CPU)

```bash
ssh $HOST "cd $RUN && OMP_NUM_THREADS=1 .venv/bin/osprey sweep --workers 18 --out \$PWD/out/sweep > out-sweep.log 2>&1"
```

Each job is one process; 3 scenarios x 3 rigs x (calc, sim) is 18 jobs.

## Render synthetic camera data (GPU, headless EGL)

```bash
ssh $HOST "cd $RUN && MUJOCO_GL=egl MUJOCO_EGL_DEVICE_ID=0 .venv/bin/osprey render --scenario docking \
  --rig mast5-spreaders --seconds 20 --fps 10 --scale 0.5 --out \$PWD/out/render-docking"
```

The renderer picks EGL by itself on a Linux host with no display. EGL device
numbering need not match `nvidia-smi`, and it is not stable: eOx found EGL
device 0 was the RTX 8000 on gpu1, but on 2026-11-06 `MUJOCO_EGL_DEVICE_ID=0`
gave the RTX 6000. Check before a long render:

```bash
ssh $HOST "cd $RUN && MUJOCO_GL=egl MUJOCO_EGL_DEVICE_ID=0 .venv/bin/python -c \
'import mujoco; from OpenGL import GL; m=mujoco.MjModel.from_xml_string(\"<mujoco/>\"); r=mujoco.Renderer(m,8,8); print(GL.glGetString(GL.GL_RENDERER).decode())'"
```

A 20 s, 10 fps docking clip at half resolution (200 frames x 5 cameras, RGB +
depth + class masks) took 7 min and 1.3 GB. Most of that is PNG encoding on
one CPU core, not the GPU. Run `tmux` for anything long.

## Bring results home

```bash
mkdir -p out/remote
scp -r $HOST:$RUN/out/. out/remote/
```

Review before copying anything to `runs/`.
