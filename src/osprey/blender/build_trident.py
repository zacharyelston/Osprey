"""Build the Trident in Blender from the sizing model's meshes and numbers (run by Blender, not imported by osprey).

    blender --background --python build_trident.py -- <dir> <out.blend> [<render dir>]

<dir> holds what `osprey trident-blend` (trident_blend.export) wrote: meshes.npz, the sealed bodies exactly as
trident.meshes gives them, and trident.json, the parameters and layout. The pods, props, legs, pads, canopy and
root flanges are drawn here from those numbers; the sizes below that the model doesn't carry are for the drawing
only and feed no calculation. Z is the craft's axis, z = 0 the tail tip, module 1 along +X, metres.
"""
import json
import math
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

# Drawing only: the model carries the pods' and pads' weights, not their shapes.
POD_R, POD_L, POD_TAIL = 0.16, 0.45, 0.25
BLADE_W, BLADE_T, BLADES = 0.16, 0.025, 2
PAD_R, PAD_T, LEG_T = 0.125, 0.03, 0.045
FLANGE_W, FLANGE_T = 0.32, 0.04
CANOPY_H, CANOPY_Z, CANOPY_DEG = 0.55, 3.15, 100.0

argv = sys.argv[sys.argv.index("--") + 1:]
src, out = argv[0], argv[1]
renders = argv[2] if len(argv) > 2 else None
M = np.load(f"{src}/meshes.npz")
J = json.load(open(f"{src}/trident.json"))
c, lay = J["params"], J["layout"]

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"


def material(name, rgba, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = rgba
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = rgba
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if rgba[3] < 1:
        b.inputs["Alpha"].default_value = rgba[3]
        m.surface_render_method = "BLENDED"
    return m


MAT = {
    "hull": material(f"hull ({c['skin']} skin)", (0.92, 0.92, 0.90, 1)),
    "wing": material("wing (sealed foam)", (0.30, 0.55, 0.85, 1)),
    "pod": material("pod", (0.20, 0.20, 0.22, 1), 0.4, 0.3),
    "prop": material("prop blade", (0.12, 0.12, 0.12, 1), 0.3),
    "disc": material("prop disc", (0.9, 0.5, 0.1, 0.12)),
    "leg": material("leg", (0.35, 0.35, 0.38, 1)),
    "flange": material("root flange", (0.75, 0.6, 0.2, 1), 0.3, 0.8),
    "window": material("canopy", (0.1, 0.15, 0.2, 1), 0.1),
}


def collection(name, parent=None):
    col = bpy.data.collections.new(name)
    (parent or scene.collection).children.link(col)
    return col


def from_arrays(name, v, f, mat, col):
    me = bpy.data.meshes.new(name)
    me.from_pydata(v.tolist(), [], f.tolist())
    me.validate()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    return ob


def prim(op, name, mat, col, **kw):
    getattr(bpy.ops.mesh, op)(**kw)
    ob = bpy.context.object
    ob.name = name
    ob.data.materials.append(mat)
    for cl in ob.users_collection:
        cl.objects.unlink(ob)
    col.objects.link(ob)
    return ob


root = collection(f"Trident ({J['layout_name']})")
root["mass_kg"] = round(J["mass_kg"], 1)
root["cg_z_m"] = round(J["zg_m"], 3)
core_col = collection("core", root)
mods = collection("modules", root)

# The sealed bodies straight from the sizing model: the envelope (core, bay and nose), the wings, and any feet.
names = sorted({k[:-2] for k in M.files})
for n in names:
    kind = n.split("_")[0]
    mat = {"envelope": MAT["hull"], "wing": MAT["wing"], "tail": MAT["wing"]}.get(kind, MAT["leg"])
    from_arrays(n.replace("_", " "), M[f"{n}_v"], M[f"{n}_f"], mat, core_col if kind == "envelope" else mods)

r_core, zp, arm = lay["r_core"], lay["z_prop"], lay["arm"]

# A canopy band on the core, facing the gap between modules 1 and 3.
win = prim("primitive_cylinder_add", "canopy", MAT["window"], core_col, vertices=64, radius=r_core + 0.005,
           depth=CANOPY_H, location=(0, 0, CANOPY_Z))
bm = bmesh.new()
bm.from_mesh(win.data)
half = math.radians(CANOPY_DEG / 2)
gone = [f for f in bm.faces if abs(f.normal.z) > 0.5
        or abs(math.atan2(f.calc_center_median().y, f.calc_center_median().x) + math.pi / 3) > half]
bmesh.ops.delete(bm, geom=gone, context="FACES")
bm.to_mesh(win.data)
bm.free()
win.modifiers.new("thickness", "SOLIDIFY").thickness = 0.01

R = c["prop_d_m"] / 2
for i in (1, 2, 3):
    th = math.radians(120 * (i - 1))
    rot = Matrix.Rotation(th, 4, "Z")
    hub = Vector((arm * math.cos(th), arm * math.sin(th), 0))
    m = collection(f"module {i}", mods)
    # Motor pod: a nacelle under the prop, a spinner on top and a tail cone below.
    prim("primitive_cylinder_add", f"pod {i}", MAT["pod"], m, vertices=32, radius=POD_R, depth=POD_L,
         location=hub + Vector((0, 0, zp - POD_L / 2)))
    sp = prim("primitive_uv_sphere_add", f"spinner {i}", MAT["pod"], m, radius=POD_R, location=hub + Vector((0, 0, zp)))
    sp.scale.z = 0.6
    prim("primitive_cone_add", f"pod tail {i}", MAT["pod"], m, vertices=32, radius1=POD_R, radius2=0.03,
         depth=POD_TAIL, location=hub + Vector((0, 0, zp - POD_L - POD_TAIL / 2)), rotation=(math.pi, 0, 0))
    # Prop: blades and a faint disc for the swept circle, just clear of the spinner.
    zb = zp + 0.06
    for b in range(BLADES):
        ang = th + math.radians(30) + 2 * math.pi * b / BLADES
        bl = prim("primitive_cube_add", f"prop {i} blade {b + 1}", MAT["prop"], m, size=1,
                  location=hub + Vector((R / 2 * math.cos(ang), R / 2 * math.sin(ang), zb)))
        bl.scale = (R, BLADE_W, BLADE_T)
        bl.rotation_euler = (0, 0, ang)
    prim("primitive_circle_add", f"prop {i} disc", MAT["disc"], m, vertices=96, radius=R, fill_type="NGON",
         location=hub + Vector((0, 0, zb)))
    # Leg: a thin fin in the module's radial plane (edge-on to the flow in cruise, nose first along +Z), from the
    # pod down to a flat pad at the model's foot_bottom_m. With float-feet the model's own feet are drawn instead.
    top, bottom = zp - POD_L, c["foot_bottom_m"] + PAD_T
    leg = prim("primitive_cube_add", f"leg {i}", MAT["leg"], m, size=1, location=hub + Vector((0, 0, (top + bottom) / 2)))
    leg.scale = (c["leg_chord_m"], LEG_T, top - bottom)
    leg.rotation_euler = (0, 0, th)
    leg.modifiers.new("round", "BEVEL").width = 0.02
    if not (c["foot_r_m"] > 0 and c["foot_l_m"] > 0):
        prim("primitive_cylinder_add", f"pad {i}", MAT["leg"], m, vertices=32, radius=PAD_R, depth=PAD_T,
             location=hub + Vector((0, 0, c["foot_bottom_m"] + PAD_T / 2)))
    # A bolted root flange on the core's skin round the wing root.
    zc = lay["z_wing_le"] - c["wing_chord_m"] / 2
    fl = prim("primitive_cube_add", f"root flange {i}", MAT["flange"], m, size=1,
              location=rot @ Vector((r_core + FLANGE_T / 2, 0, zc)))
    fl.scale = (FLANGE_T, FLANGE_W, c["wing_chord_m"] + 0.12)
    fl.rotation_euler = (0, 0, th)
    for zbolt in np.linspace(lay["z_wing_le"] + 0.02, lay["z_wing_le"] - c["wing_chord_m"] - 0.02, 4):
        for yb in (-0.11, 0.11):
            prim("primitive_cylinder_add", f"bolt {i}", MAT["pod"], m, vertices=12, radius=0.012, depth=0.03,
                 location=rot @ Vector((r_core + FLANGE_T + 0.005, yb, zbolt)), rotation=(0, math.pi / 2, th))

# Ground at the pads, a 1.8 m person for scale, the CG, a sun and three cameras.
ref = collection("reference", root)
prim("primitive_plane_add", "ground", material("ground", (0.55, 0.6, 0.5, 1)), ref, size=16,
     location=(0, 0, c["foot_bottom_m"]))
prim("primitive_cylinder_add", "person 1.8 m", material("person", (0.8, 0.3, 0.3, 1)), ref, vertices=16, radius=0.2,
     depth=1.8, location=(-2.2, -1.6, c["foot_bottom_m"] + 0.9))
cg = bpy.data.objects.new("CG", None)
cg.empty_display_type, cg.empty_display_size = "SPHERE", 0.15
cg.location = (0, 0, J["zg_m"])
ref.objects.link(cg)
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
sun.data.energy = 4
sun.rotation_euler = (math.radians(40), math.radians(10), math.radians(-30))
ref.objects.link(sun)


def camera(name, loc, look, ortho=None):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    cam.location = loc
    cam.rotation_euler = (Vector(look) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    if ortho:
        cam.data.type, cam.data.ortho_scale = "ORTHO", ortho
    else:
        cam.data.lens = 40
    ref.objects.link(cam)
    return cam


across = 2 * (arm + R)
camera("iso", (9.5, -11.0, 6.5), (0, 0, 1.6))
camera("side", (0.0, -30.0, lay["z_nose"] / 2), (0, 0, lay["z_nose"] / 2), ortho=1.2 * across)
camera("top", (0.0, 0.0, 30.0), (0, 0, 0), ortho=1.43 * across)
scene.camera = bpy.data.objects["iso"]
w = bpy.data.worlds.new("sky")
scene.world = w
w.use_nodes = True
w.node_tree.nodes["Background"].inputs[0].default_value = (0.75, 0.82, 0.9, 1)
w.node_tree.nodes["Background"].inputs[1].default_value = 0.8
bpy.ops.wm.save_as_mainfile(filepath=out)
print("BUILT", out, len(bpy.data.objects), "objects")

if renders:
    scene.render.engine = "BLENDER_EEVEE"
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = 1400, 1000
    for cam in ("iso", "side", "top"):
        scene.camera = bpy.data.objects[cam]
        bpy.data.objects["ground"].hide_render = cam == "top"
        scene.render.filepath = f"{renders}/trident_{cam}.png"
        bpy.ops.render.render(write_still=True)
        print("RENDERED", scene.render.filepath)
