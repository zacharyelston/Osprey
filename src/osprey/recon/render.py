"""Renders of the Recon drone ("the bird") in MuJoCo, from a sized design:
- hero: out ahead of the sailboat, seen from further ahead looking back at it;
- three-view: orthographic top, front and side;
- exploded: the printed wing panels pulled apart along the carbon spar;
- lineup: every mission's drone side by side, to scale.

The wing is the sized one; the pod, booms, tail and prop are REF geometry
(recon/geometry.py). Colours: printed LW-PLA shell in white and off-white by
panel, carbon black, a hi-vis orange pod and fins.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from osprey import frames
from osprey.recon import geometry

RGBA = {"shell0": "0.94 0.94 0.92 1", "shell1": "0.74 0.77 0.77 1", "spar": "0.07 0.07 0.08 1",
        "carbon": "0.09 0.09 0.10 1", "pod": "0.96 0.45 0.10 1", "gimbal": "0.16 0.16 0.18 1",
        "lens": "0.05 0.12 0.25 1", "tail": "0.96 0.45 0.10 1", "prop": "0.08 0.08 0.08 1",
        "disc": "0.3 0.3 0.3 0.12", "red": "0.95 0.1 0.1 1", "green": "0.1 0.9 0.2 1",
        "plug": "0.70 0.52 0.33 1", "rib": "0.80 0.64 0.44 1", "stringer": "0.62 0.45 0.28 1", "stock": "0.55 0.70 0.85 0.12"}


def _mesh_xml(name: str, part: geometry.Part) -> str:
    v = " ".join(f"{x:.5f}" for x in part.verts.ravel())
    f = " ".join(str(i) for i in part.faces.ravel())
    return f'<mesh name="{name}" vertex="{v}" face="{f}"/>'


def _drone_xml(tag: str, parts, pos, quat) -> tuple[str, str]:
    assets, geoms = [], []
    for q in parts:
        mname = f"{tag}_{q.name}"
        assets.append(_mesh_xml(mname, q))
        mat = ' material="shell"' if q.kind.startswith("shell") or q.kind in ("pod", "tail") else ""
        geoms.append(f'<geom type="mesh" mesh="{mname}" rgba="{RGBA[q.kind]}"{mat} contype="0" conaffinity="0"/>')
    body = (f'<body name="{tag}" pos="{pos[0]:.4f} {pos[1]:.4f} {pos[2]:.4f}" '
            f'quat="{" ".join(f"{x:.6f}" for x in quat)}">{"".join(geoms)}</body>')
    return "".join(assets), body


def _cam(name: str, eye, target, *, ortho: float | None = None, fovy: float = 35.0) -> str:
    F = frames.look_frame(np.asarray(target, float) - np.asarray(eye, float))
    xy = " ".join(f"{v:.6f}" for v in np.r_[F[:, 0], F[:, 1]])
    proj = f' projection="orthographic" fovy="{ortho:.4f}"' if ortho else f' fovy="{fovy}"'
    return f'<camera name="{name}" pos="{eye[0]:.4f} {eye[1]:.4f} {eye[2]:.4f}" xyaxes="{xy}"{proj}/>'


def _quat(roll_deg: float = 0.0, pitch_deg: float = 0.0, yaw_deg: float = 0.0) -> np.ndarray:
    return frames.quat_from_matrix(frames.attitude(math.radians(roll_deg), math.radians(pitch_deg),
                                                   math.radians(yaw_deg)))


def _world(kind: str, assets: str, bodies: str, cams: str, W: int, H: int, extra: str = "",
           floor_on: bool = True) -> str:
    if kind == "sea":
        # Sparse soft white marks on a 64 px tile 25 m across: whitecaps about half a metre wide.
        env = """<texture name="sky" type="skybox" builtin="gradient" rgb1="0.80 0.88 0.96" rgb2="0.32 0.52 0.78"
                   width="512" height="512"/>
        <texture name="sea" type="2d" builtin="flat" rgb1="0.09 0.28 0.40" mark="random" random="0.004"
                 markrgb="0.42 0.56 0.64" width="48" height="48"/>
        <material name="sea" texture="sea" texrepeat="20 20" reflectance="0.08"/>"""
        floor = '<geom name="sea" type="plane" size="400 400 1" material="sea" contype="0" conaffinity="0"/>'
        haze = '<rgba haze="0.78 0.85 0.92 1"/>'
    else:
        env = """<texture name="sky" type="skybox" builtin="gradient" rgb1="0.62 0.66 0.72" rgb2="0.30 0.33 0.38"
                   width="512" height="512"/>
        <material name="floor" rgba="0.50 0.53 0.57 1" reflectance="0.15"/>"""
        floor = '<geom name="floor" type="plane" pos="0 0 -0.35" size="0 0 1" material="floor" contype="0" conaffinity="0"/>'
        haze = '<rgba haze="0.45 0.48 0.53 1"/>'
    if not floor_on:
        floor = ""
        env = env.replace('builtin="gradient" rgb1="0.62 0.66 0.72" rgb2="0.30 0.33 0.38"',
                          'builtin="flat" rgb1="0.46 0.49 0.54" rgb2="0.46 0.49 0.54"')
    return f"""<mujoco model="osprey-recon">
  <visual>
    <global offwidth="{W}" offheight="{H}"/>
    <quality shadowsize="8192" offsamples="8"/>
    <map znear="0.01" zfar="400" haze="0.6"/>
    <headlight ambient="0.30 0.30 0.30" diffuse="0.25 0.25 0.25" specular="0.1 0.1 0.1"/>
    {haze}
  </visual>
  <asset>
    {env}
    <material name="shell" specular="0.35" shininess="0.6"/>
    {assets}
  </asset>
  <worldbody>
    <light directional="true" pos="0 0 50" dir="-0.35 0.25 -1" diffuse="0.80 0.78 0.72" castshadow="true"/>
    <light directional="true" pos="0 0 50" dir="0.5 -0.4 -0.6" diffuse="0.25 0.27 0.32" castshadow="false"/>
    {floor}
    {extra}
    {bodies}
    {cams}
  </worldbody>
</mujoco>"""


BOAT_YAW_DEG = 20.0                                          # the boat's heading in the hero scene, CCW from +x


def _boat_xml() -> tuple[str, str]:
    """The reference sailboat from the Nest scene, sails down, for scale below the drone."""
    from osprey.params import load
    from osprey.render import scene

    p = load("docking")
    b, m = p.boat, p.mast
    asset = scene._hull_mesh(b)
    body = (f'<body name="boat" pos="0 0 0" euler="0 0 {BOAT_YAW_DEG:g}">'
            f'<geom type="mesh" mesh="hull" rgba="0.95 0.95 0.93 1" contype="0" conaffinity="0"/>'
            f'<geom type="box" pos="-1.6 0 {b.freeboard_m + 0.3}" size="1.8 1.1 0.3" rgba="0.95 0.95 0.93 1" '
            f'contype="0" conaffinity="0"/>'
            f'<geom type="cylinder" fromto="0 0 {m.deck_z_m - 0.2} 0 0 {m.truck_z_m}" size="{m.radius_m}" '
            f'rgba="0.75 0.75 0.78 1" contype="0" conaffinity="0"/>'
            f'<geom type="capsule" fromto="-0.15 0 {p.sailplan.boom_z_m} {-p.sailplan.boom_length_m} 0 '
            f'{p.sailplan.boom_z_m}" size="0.07" rgba="0.75 0.75 0.78 1" contype="0" conaffinity="0"/>'
            f'</body>')
    return asset, body


def _shoot(xml: str, cams: list[str], W: int, H: int) -> dict[str, np.ndarray]:
    from osprey.render.scene import _backend

    _backend()
    import mujoco

    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    out = {}
    with mujoco.Renderer(model, H, W) as r:
        for c in cams:
            r.update_scene(data, camera=c)
            out[c] = r.render().copy()
    return out


def hero(p, d: dict, path: Path, W: int = 1600, H: int = 900):
    """Out ahead of the boat on its way to a job. The camera is further ahead
    still, above and to one side, looking back over the bird at the boat."""
    parts = geometry.build(p, d)
    R = frames.rot_z(math.radians(BOAT_YAW_DEG))              # boat axes: x the bow, y port
    pos = R @ np.array([40.0, 10.0, 30.0])                   # ahead of the bow, a little to port
    a, b = _drone_xml("bird", parts, pos, _quat(roll_deg=-15, pitch_deg=-2, yaw_deg=BOAT_YAW_DEG + 10))
    ba, bb = _boat_xml()
    s = max(d["span_m"], 1.3)
    eye = pos + R @ np.array([0.75, -0.55, 0.75]) * s
    to_drone, to_boat = pos - eye, -eye
    az = math.atan2(*(0.4 * to_drone[1::-1] / np.linalg.norm(to_drone[:2])
                      + 0.6 * to_boat[1::-1] / np.linalg.norm(to_boat[:2])))
    el = (0.4 * math.atan2(to_drone[2], np.linalg.norm(to_drone[:2]))
          + 0.6 * math.atan2(to_boat[2], np.linalg.norm(to_boat[:2])) + math.radians(8))
    cam = _cam("hero", eye, eye + frames.direction(az, el), fovy=48)
    img = _shoot(_world("sea", a + ba, bb + b, cam, W, H), ["hero"], W, H)["hero"]
    _save(img, path)


def threeview(p, d: dict, path: Path, W: int = 1800, H: int = 640):
    parts = geometry.build(p, d)
    lo, hi = geometry.bounds(parts)
    a, b = _drone_xml("bird", parts, np.zeros(3), _quat())
    L, Wd, Ht = hi - lo
    c = (lo + hi) / 2
    w3 = W // 3
    r = H / w3
    # Orthographic: fovy is the vertical extent in metres, the horizontal one is fovy * width / height.
    cams = (_cam("top", c + [0, 0, 5], c, ortho=1.12 * max(L, Wd * r))
            + _cam("front", c + [5, 0, 0], c, ortho=1.12 * max(Ht, Wd * r))
            + _cam("side", c + [0, 5, 0], c, ortho=1.12 * max(Ht, L * r)))
    imgs = _shoot(_world("studio", a, b, cams, w3, H, floor_on=False), ["top", "front", "side"], w3, H)
    _save(np.concatenate([imgs["top"], imgs["front"], imgs["side"]], 1), path,
          labels=[(14, f"top: {d['span_m']:.2f} m span"),
                  (w3 + 14, {"bwb": "front: winglets, payload, pusher prop",
                             "crescent": "front: upswept tips, nose pod, pusher prop",
                             "tandem": "front: two high wings, four props, a V-keel hull"}.get(
                      d.get("airframe"), "front: 3 deg dihedral, gimbal, pusher prop")),
                  (2 * w3 + 14, f"side: {L:.2f} m long")])


def exploded(p, d: dict, path: Path, W: int = 1600, H: int = 900):
    parts = geometry.build(p, d, explode=0.07)
    a, b = _drone_xml("bird", parts, np.zeros(3), _quat())
    span = d["span_m"]
    cam = _cam("x", np.array([1.1, 0.9, 0.75]) * span, [0.0, 0.0, 0.0], fovy=40)
    _save(_shoot(_world("studio", a, b, cam, W, H), ["x"], W, H)["x"], path)


def underside(p, d: dict, path: Path, W: int = 1400, H: int = 800):
    """A close look up at the pod from below and ahead: the gimbal, or the
    fore/aft pair and the belly fisheye."""
    parts = geometry.build(p, d)
    a, b = _drone_xml("bird", parts, np.zeros(3), _quat())
    g = p.geometry
    target = np.array([g.pod_nose_x_m - 0.35 * g.pod_length_m, 0.0, -0.06])
    cam = _cam("u", target + np.array([0.55, -0.45, -0.32]), target, fovy=34)
    _save(_shoot(_world("studio", a, b, cam, W, H, floor_on=False), ["u"], W, H)["u"], path)


def turntable(p, d: dict, path: Path, W: int = 900, H: int = 520, frames_n: int = 48):
    """An orbiting studio shot, saved as a looping GIF."""
    from PIL import Image

    parts = geometry.build(p, d)
    a, b = _drone_xml("bird", parts, np.zeros(3), _quat())
    r = 1.45 * max(d["span_m"], 1.2)
    cams = "".join(_cam(f"t{k}", [r * math.cos(th), r * math.sin(th), 0.55 * r], [-0.25, 0, 0], fovy=42)
                   for k, th in enumerate(np.linspace(0, 2 * math.pi, frames_n, endpoint=False) + 0.6))
    imgs = _shoot(_world("studio", a, b, cams, W, H), [f"t{k}" for k in range(frames_n)], W, H)
    first = Image.fromarray(imgs["t0"]).quantize(colors=160, method=Image.Quantize.MEDIANCUT)
    seq = [Image.fromarray(imgs[f"t{k}"]).quantize(palette=first, dither=Image.Dither.NONE) for k in range(frames_n)]
    path.parent.mkdir(parents=True, exist_ok=True)
    seq[0].save(path, save_all=True, append_images=seq[1:], duration=80, loop=0, optimize=True)


def lineup(designs: list[tuple[object, dict, str]], path: Path, W: int = 1800, H: int = 760):
    """Every mission's drone side by side, smallest on the left, in an
    orthographic view so they are truly to the same scale."""
    assets, bodies, ys = "", "", []
    y = 0.0
    gap = 0.35
    for i, (p, d, _) in enumerate(designs):
        y += d["span_m"] / 2
        ys.append(y)
        a, b = _drone_xml(f"bird{i}", geometry.build(p, d), np.array([0.0, y, 0.0]), _quat())
        y += d["span_m"] / 2 + gap
        assets += a
        bodies += b
    mid = (ys[0] - designs[0][1]["span_m"] / 2 + ys[-1] + designs[-1][1]["span_m"] / 2) / 2
    centre = np.array([-0.3, mid, 0.0])
    eye = centre + np.array([4.0, 0.0, 4.4])
    width = (y - gap) * 1.08
    fov = width * H / W
    cam = _cam("l", eye, centre, ortho=fov)
    img = _shoot(_world("studio", assets, bodies, cam, W, H), ["l"], W, H)["l"]
    px = lambda yy: int(W / 2 + (yy - mid) / width * W)
    labels = [(max(px(yy) - 150, 8), f"{name}: {d['span_m']:.2f} m, {d['mass_total_kg']:.2f} kg")
              for yy, (_, d, name) in zip(ys, designs)]
    _save(img, path, labels=labels, y=H - 60)


def _save(img: np.ndarray, path: Path, labels: list[tuple[int, str]] = (), y: int = 12):
    """Save an image with text labels: (x, text) pairs, stacked down from y when x repeats."""
    from PIL import Image, ImageDraw, ImageFont

    im = Image.fromarray(img)
    dr = ImageDraw.Draw(im)
    try:
        font = ImageFont.load_default(size=24)
    except TypeError:                      # Pillow < 10.1
        font = ImageFont.load_default()
    rows: dict[int, int] = {}
    for x, txt in labels:
        yy = y + 32 * rows.get(x, 0)
        rows[x] = rows.get(x, 0) + 1
        dr.text((x, yy), txt, fill=(245, 245, 245), font=font, stroke_width=2, stroke_fill=(40, 40, 45))
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)


def plugs(p, d: dict, path: Path, W: int = 1600, H: int = 900, margin_m: float = 0.025):
    """The two plug halves on a bench, parting faces down, in tooling-board
    colour, the upper one inside a ghost of the stock block it is cut from.
    The meshes are the ones `osprey recon-plug` writes as STL."""
    from osprey.recon import plug as bk

    parts = []
    upper = bk._meshes(geometry.bwb_surface(p, d, half="upper"))
    lower = bk._meshes(geometry.bwb_surface(p, d, half="lower"))
    allu = np.concatenate([v for v, _ in upper])
    span_x = float(allu[:, 0].max() - allu[:, 0].min())
    gap = 0.18
    for k, (v, f) in enumerate(upper):
        parts.append(geometry.Part(f"upper{k}", "plug", v.copy(), f))
    for k, (v, f) in enumerate(lower):
        v2 = v.copy()
        v2[:, 2] *= -1                                         # turned over: parting face down
        v2[:, 0] -= span_x + gap
        parts.append(geometry.Part(f"lower{k}", "plug", v2, f[:, ::-1].copy()))
    lo, hi = allu.min(0) - margin_m, allu.max(0) + margin_m
    lo[2] = 0.0
    corners = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    faces = np.array([[0, 1, 3], [0, 3, 2], [4, 6, 7], [4, 7, 5], [0, 4, 5], [0, 5, 1],
                      [2, 3, 7], [2, 7, 6], [0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3]])
    parts.append(geometry.Part("stock", "stock", corners, faces))
    a, b = _drone_xml("plugs", parts, np.zeros(3), _quat())
    bench = '<geom name="bench" type="box" pos="{} 0 -0.012" size="{} {} 0.012" rgba="0.36 0.37 0.40 1" ' \
            'contype="0" conaffinity="0"/>'.format(-(span_x + gap) / 2 + float(allu[:, 0].mean()) / 2,
                                                   span_x + 0.5, float(hi[1] - lo[1]) / 2 + 0.25)
    centre = np.array([float(allu[:, 0].mean()) - (span_x + gap) / 2, 0.0, 0.03])
    cam = _cam("b", centre + np.array([1.75, -0.45, 1.85]), centre + np.array([-0.05, 0, 0]), fovy=44)
    img = _shoot(_world("studio", a, b, cam, W, H, extra=bench, floor_on=False), ["b"], W, H)["b"]
    _save(img, path, labels=[(14, "front: the upper plug in its stock block   behind: the lower plug, turned over"),
                             (14, f"{d['span_m'] * 1000:.0f} mm span, parting faces down on the bench")])


def frame(p, d: dict, path: Path, W: int = 1600, H: int = 900, frames_: dict | None = None):
    """Both ladder frames assembled on their tables: the upper one in front,
    the lower one (turned over) behind it. Ribs in light ply, stringers darker."""
    from osprey.recon import frame as fm

    frames_ = frames_ or {s: fm.build(p, d, s)[0] for s in ("upper", "lower")}
    parts, tables = [], []
    ext = np.concatenate([fm.FramePart.to_3d(q, q.outline) for q in frames_["upper"]]) / 1000
    span_x = float(np.ptp(ext[:, 0]))
    gap = 0.25
    for k, (side, fp) in enumerate(frames_.items()):
        base = min(float(q.outline[:, 1].min()) for q in fp) / 1000
        dx = -k * (span_x + gap)
        for q in fp:
            v, f = fm.solid(q, p.frame.thickness_mm)
            v = v + np.array([dx, 0.0, -base])
            parts.append(geometry.Part(f"{side}_{q.name}", q.kind, v, f))
        lo = ext.min(0) - 0.04
        hi = ext.max(0) + 0.04
        tables.append('<geom type="box" pos="{:.4f} {:.4f} -0.009" size="{:.4f} {:.4f} 0.009" '
                      'rgba="0.86 0.86 0.84 1" contype="0" conaffinity="0"/>'.format(
                          (lo[0] + hi[0]) / 2 + dx, (lo[1] + hi[1]) / 2, (hi[0] - lo[0]) / 2, (hi[1] - lo[1]) / 2))
    a, b = _drone_xml("frame", parts, np.zeros(3), _quat())
    centre = np.array([float(ext[:, 0].mean()) - (span_x + gap) / 2, 0.0, 0.03])
    k_ = float(np.clip(np.ptp(ext[:, 1]) / 1.9, 0.75, 1.1))                # frame the smaller wings closer
    cam = _cam("f", centre + k_ * np.array([1.7, -0.55, 1.6]), centre + np.array([-0.05, 0, 0]), fovy=44)
    img = _shoot(_world("studio", a, b, cam, W, H, extra="".join(tables), floor_on=False), ["f"], W, H)["f"]
    n = {s: (sum(q.kind == "rib" for q in fp), sum(q.kind == "stringer" for q in fp)) for s, fp in frames_.items()}
    _save(img, path, labels=[(14, f"front: upper-surface frame, {n['upper'][0]} ribs and {n['upper'][1]} stringers"),
                             (14, "behind: lower-surface frame, turned over"),
                             (14, f"{p.frame.thickness_mm:g} mm sheet, half-depth slots, standing on flat tables")])


def afloat(birds: list[tuple[object, dict, dict, str]], path: Path, W: int = 1800, H: int = 760):
    """Birds floating side by side at the draft and trim recon/water.py finds,
    each pusher prop raised on the pylon the water needs (dashed in grey):
    (params, design, afloat result, label) for each."""
    from osprey.recon import water

    assets, bodies, labels = [], [], []
    y0 = 0.0
    spans = [d["span_m"] for _, d, _, _ in birds]
    gap = 0.5
    for k, ((p, d, fl, label), span) in enumerate(zip(birds, spans)):
        yc = y0 + span / 2
        y0 += span + gap
        th = math.radians(fl["trim_deg"])
        cg = np.array(fl["cg"])
        parts = geometry.build(p, d)
        hub = None
        for q in parts:
            if q.kind in ("disc", "prop") and fl["pylon_m"] > 0:
                if hub is None:
                    hub = q.verts.mean(0)
                q.verts = q.verts + [0, 0, fl["pylon_m"]]
        if hub is not None:
            v, f = geometry._tube(hub + [0.03, 0, -0.02], hub + [0.0, 0, fl["pylon_m"]], 0.008, 10)
            parts.append(geometry.Part("pylon", "carbon", v, f))
        for q in parts:
            v = water._pitch(q.verts, cg, th)
            v[:, 2] -= fl["waterline_z"]
            v[:, 1] += yc
            q.verts = v
        a, b = _drone_xml(f"b{k}", parts, np.zeros(3), _quat())
        assets.append(a)
        bodies.append(b)
        labels.append(label)
    width = y0 - gap
    centre = np.array([0.0, width / 2, 0.0])
    eye = centre + np.array([0.5 * width + 0.4, -0.05 * width, 0.14 * width + 0.1])
    cam = _cam("f", eye, centre + np.array([-0.3, 0, -0.02]), fovy=42)
    img = _shoot(_world("sea", "".join(assets), "".join(bodies), cam, W, H), ["f"], W, H)["f"]
    _save(img, path, labels=[(14, "afloat at the draft and trim the model finds; each prop raised on its pylon"),
                             (14, "left to right: " + ",  ".join(labels))])


def launch_sequence(p, d: dict, fl: dict, track: list, path: Path, W: int = 1800, H: int = 760):
    """A tailsitter's water launch in one picture: the same bird afloat upright on its pods, clear of the
    water, pitching over and wing-borne, posed from the launch track (recon/tailsitter.py)."""
    from osprey.recon import tailsitter as ts

    tr = np.array(track)
    t_end = tr[-1, 0]
    picks = [0.0, float(tr[np.argmax(tr[:, 2] > fl["draft_m"] + 1.2), 0])]
    pitch = tr[:, 3]
    picks += [float(tr[np.argmax(pitch < math.radians(55)), 0]), t_end]
    assets, bodies, labels = [], [], []
    cg = np.array(fl["cg"])
    for k, tk in enumerate(picks):
        i = int(np.argmin(np.abs(tr[:, 0] - tk)))
        _, x, rise, th = tr[i]
        R = ts._rot_y(-th)                                   # nose up by th: forward goes to (cos, 0, sin)
        parts = geometry.build(p, d)
        for q in parts:
            q.verts = (q.verts - cg) @ R.T + [x, 0.0, rise - fl["waterline_z"]]
        a, b = _drone_xml(f"s{k}", parts, np.zeros(3), _quat())
        assets.append(a)
        bodies.append(b)
        labels.append(f"{tr[i, 0]:.1f} s")
    sel = [int(np.argmin(np.abs(tr[:, 0] - tk))) for tk in picks]
    xs, zs = tr[sel, 1], tr[sel, 2] - fl["draft_m"]
    centre = np.array([float(xs.mean()), 0.0, float(zs.max()) / 2 + 0.4])
    span = max(float(np.ptp(xs)), 2.2 * float(zs.max())) + 4.0
    # From ahead and to one side: upright, the wing lies across the view, its face toward the camera.
    eye = centre + np.array([0.30 * span, -0.85 * span, 0.10 * span])
    eye[0] = max(eye[0], float(xs.max()) + 2.0)                        # stay ahead of the last pose
    cam = _cam("l", eye, centre, fovy=36)
    img = _shoot(_world("sea", "".join(assets), "".join(bodies), cam, W, H), ["l"], W, H)["l"]
    _save(img, path, labels=[(14, "tailsitter water launch: afloat on its pods, clear of the water, pitching over, "
                                  "wing-borne"),
                             (14, "at " + ",  ".join(labels) + f" after throttle-up; wing-borne {t_end:.1f} s, "
                                  f"{tr[-1, 1]:.0f} m downrange")])


def _posed_cyclone(parts, R: np.ndarray, at) -> list:
    for q in parts:
        q.verts = q.verts @ R.T + np.asarray(at, float)
    return parts


def cyclone_modes(p, d: dict, cy, phi_spin_deg: float, path: Path, W: int = 1800, H: int = 760):
    """The Cyclone in each mode, left to right over the sea: 1 B centred, A lifting; 2 spinning (its disc
    drawn); 3 the spinning disc tilted to travel; 4 wing-borne, two arms up as the dihedral wing and one
    down as the fin, flying toward the camera."""
    from osprey.recon import cyclone_water

    wt = cyclone_water.inputs()
    kw = {"axis_frac": wt.axis_frac, "mount_m": wt.mount_m, "gimbal_drop_m": wt.gimbal_drop_m}
    tilt = math.radians(10.0)
    roty = np.array([[math.cos(tilt), 0, math.sin(tilt)], [0, 1, 0], [-math.sin(tilt), 0, math.cos(tilt)]])
    wing = np.array([[0.0, 0.0, 1.0], [-1.0, 0.0, 0.0], [0.0, -1.0, 0.0]])   # x -> -y, y -> -z, z -> +x
    from osprey.recon import cyclone

    R = cyclone.geometry(p, d, cy)["R_m"]
    span = 2 * R + 0.6
    top = max(math.cos(math.radians(t)) for t in cyclone.layout(cy)["theta_deg"])     # mode 4's highest arm
    poses = [(0.0, np.eye(3), 2.2, False, "1 lift-off"), (phi_spin_deg, np.eye(3), 3.4, True, "2 spinning hover"),
             (phi_spin_deg, roty, 4.0, True, "3 spinning travel"),
             (0.0, wing, 4.4 + (0.5 - top) * R, False, "4 wing-borne")]
    assets, bodies = [], []
    for k, (phi, Rm, z, disc, _) in enumerate(poses):
        parts = _posed_cyclone(geometry.build_cyclone(p, d, cy, phi, spin_disc=disc, **kw), Rm, [0.0, k * span, z])
        a, b = _drone_xml(f"c{k}", parts, np.zeros(3), _quat())
        assets.append(a)
        bodies.append(b)
    centre = np.array([0.0, 1.5 * span, 3.4])
    eye = centre + np.array([3.6 * span, -0.1 * span, 0.55 * span])             # broadside to the line
    cam = _cam("m", eye, centre + np.array([0.0, 0.0, -0.3]), fovy=26)
    img = _shoot(_world("sea", "".join(assets), "".join(bodies), cam, W, H), ["m"], W, H)["m"]
    lay = cyclone.layout(cy)
    n_up = sum(1 for i in lay["lift"] if math.cos(math.radians(lay["theta_deg"][i])) > 0)
    four = (f"{n_up} arms up as the wing, one down as the fin" if cy.arms == 3 else
            f"{len(lay['lift'])} arms as the wing" + (f", {len(lay['fins'])} as fins" if lay["fins"] else ""))
    _save(img, path, labels=[(14, "the Cyclone's modes, left to right: " + ",  ".join(x[4] for x in poses)),
                             (14, f"B centred for 1 and 4; turned {phi_spin_deg:.0f}° off centre to spin; 4 flies toward "
                                  f"the camera, {four}")])


def cyclone_afloat(p, d: dict, cy, fl: dict, path: Path, W: int = 1600, H: int = 900):
    """The Cyclone afloat at the draft recon/cyclone_water.py finds, standing on its arms' trailing edges,
    A's props up."""
    from osprey.recon import cyclone_water

    wt = cyclone_water.inputs()
    parts = geometry.build_cyclone(p, d, cy, 0.0, axis_frac=wt.axis_frac, mount_m=wt.mount_m,
                                   gimbal_drop_m=wt.gimbal_drop_m)
    parts = _posed_cyclone(parts, np.eye(3), [0.0, 0.0, fl["z_hub_m"] - fl["draft_m"]])
    a, b = _drone_xml("cy", parts, np.zeros(3), _quat())
    R = fl["R_m"]
    centre = np.array([0.0, 0.0, 0.05])
    eye = centre + np.array([1.9 * R, -1.6 * R, 0.55 * R])
    cam = _cam("f", eye, centre, fovy=40)
    img = _shoot(_world("sea", a, b, cam, W, H), ["f"], W, H)["f"]
    _save(img, path, labels=[(14, f"afloat with B centred: standing on its three arms, {fl['draft_m'] * 100:.0f} cm deep, "
                                  f"A's props {fl['prop_height_m'] * 100:.0f} cm up"),
                             (14, f"metacentric height {fl['gm_m']:.1f} m: it rides the waves' slope")])
