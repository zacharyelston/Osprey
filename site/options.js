// The option pickers. Every number is from a kept run in the repo's runs/ folder.

const RIGS = {
  mast5: {
    label: "mast5",
    name: "mast5: five cameras on mast brackets",
    what: "One PTZ at the masthead and four round the mast on brackets, one camera kept in reserve for the watch.",
    img: "img/coverage-mast5.png",
    stats: [
      ["Whole horizon swept under sail", "0% of the time"],
      ["Coastal watch: kayak / ferry / sloop", "57 / 0 / 96%"],
      ["During a MOB, buoy 900 m ahead kept in view", "99%"],
      ["Docking: water within 3 m seen by 2+ cameras", "94.3%"],
      ["Hull edge with a stereo pair", "80%"],
      ["Masthead-equivalent mass aloft", "5.0 kg (cameras only)"],
    ],
    take: "Simple, but heeled under sail the main and jib hide the lee side: without the masthead camera only 68% of the horizon is seen, and the ferry is never served.",
  },
  "mast5-spreaders": {
    label: "mast5-spreaders",
    name: "mast5-spreaders: side cameras out on the spreaders",
    what: "The same five PTZs, with the side cameras moved out to the spreader tips.",
    img: "img/rig-compare.png",
    dark: "img/rig-compare-dark.png",
    stats: [
      ["Whole horizon swept under sail", "0% of the time"],
      ["Coastal watch: kayak / ferry / sloop", "84 / 86 / 88%"],
      ["During a MOB, buoy 900 m ahead kept in view", "0%"],
      ["Docking: water within 3 m seen by 2+ cameras", "94.6%"],
      ["Hull edge with a stereo pair", "88%"],
      ["Masthead-equivalent mass aloft", "5.1 kg (cameras only)"],
    ],
    take: "Better coastal coverage, but a man-overboard search takes every camera except the reserve, so a buoy off the bow gets none for the whole five minutes.",
  },
  gecko5: {
    label: "gecko5",
    name: "gecko5: five gecko pods",
    what: "Five pods with two PTZ eyes each, one up and one hung below, and a computer, IMU and PoE in every pod. Each pod watches a sector that overlaps its neighbours'.",
    img: "img/nest-layout.png",
    dark: "img/nest-layout-dark.png",
    stats: [
      ["Whole horizon swept under sail", "100%, 8 s worst revisit"],
      ["Coastal watch: kayak / ferry / sloop", "88 / 84 / 99%"],
      ["During a MOB, buoy 900 m ahead kept in view", "99%, with 4 eyes on the person"],
      ["Docking: water within 3 m seen by 2+ cameras", "96.5%"],
      ["Hull edge with a stereo pair", "89%, 4.6 cm depth (p95)"],
      ["Masthead-equivalent mass aloft", "11.9 kg, against a 4 kg budget"],
      ["Energy per day underway", "381 Ah, against 120 Ah"],
    ],
    take: "Watches everything and docks well, but it is about three times over the mass and energy budgets. That is the next design problem.",
  },
  "spreader-pairs": {
    label: "spreader-pairs",
    name: "spreader-pairs: stereo pairs across the boat",
    what: "A back-to-back mount at each spreader tip, one fixed camera forward and one aft, so the two tips make stereo pairs ahead and astern. The masthead keeps its gecko pod.",
    img: "img/pairs-layout.png",
    dark: "img/pairs-layout-dark.png",
    stats: [
      ["Whole horizon swept under sail", "100%, 7 s worst revisit"],
      ["Coastal watch, boat alone: kayak / ferry / sloop", "23 / 11 / 0%"],
      ["During a MOB, buoy 900 m ahead kept in view", "18%"],
      ["Docking: water within 3 m seen by 2+ cameras", "44% (bow and stern)"],
      ["Hull edge with a stereo pair", "35%, 1.3 cm depth (p95)"],
      ["Masthead-equivalent mass aloft", "7.7 kg"],
      ["Energy per day underway", "259 Ah"],
    ],
    take: "Lighter, with centimetre stereo at the bow and stern, but it can't identify at range or see the beams on its own. It hands that work to Recon flying escort.",
  },
};

const AIRFRAMES = {
  twinboom: {
    label: "Twin-boom",
    name: "Twin-boom, printed",
    what: "The reference bird: a printed wing in ten panels on a carbon spar, twin carbon booms, an H-tail and a pusher prop.",
    img: { gimbal: "img/bird-hero.png", dual: "img/bird-dual-underside.png" },
  },
  bwb: {
    label: "Blended wing",
    name: "Blended wing, moulded",
    what: "A tailless blended wing body, laid up in moulds taken from CNC-cut plugs.",
    img: { gimbal: "img/bird-bwb-hero.png", dual: "img/bird-bwb-hero.png" },
  },
  crescent: {
    label: "Crescent",
    name: "Crescent flying wing, printed",
    what: "A printed tailless crescent wing, after the NX-2: the cleanest of the three in the air.",
    img: { gimbal: "img/bird-crescent-hero.png", dual: "img/bird-crescent-hero.png" },
  },
  tailsitter: {
    label: "Tailsitter",
    name: "Tailsitter blended wing",
    what: "The blended wing with two tractor props for hovering and four float pods on struts. It stands on its tail on deck, floats upright on the pods at sea, and takes off and lands vertically.",
    img: { gimbal: "img/bird-tailsitter-hero.png", dual: "img/bird-tailsitter-hero.png" },
  },
};

const PAYLOADS = {
  gimbal: { label: "One gimbal", name: "one gimbal", stat: ["Cameras", "One gimbal, 0.35 kg, 6 W"] },
  dual: { label: "A PTZ eye each side", name: "a PTZ eye each side", stat: ["Cameras", "Side PTZs and a belly fisheye, 0.51 kg, 10 W"] },
};

const RECOVERY = {
  deck: { label: "Deck" },
  water: { label: "Float kit" },
  vertical: { label: "Vertical" },
};

// [mass kg, span m, extra stats]
const BIRDS = {
  "twinboom/gimbal/deck": [2.73, 2.02, [["Lift-to-drag", "10.1"]]],
  "twinboom/dual/deck": [2.13, 1.54, [["Lift-to-drag", "8.1"]]],
  "bwb/gimbal/deck": [2.11, 1.32, [["Lift-to-drag", "11.6"]]],
  "bwb/dual/deck": [1.80, 1.15, [["Lift-to-drag", "10.0"]]],
  "crescent/gimbal/deck": [2.18, 1.98, [["Lift-to-drag", "12.6"]]],
  "crescent/dual/deck": [1.83, 1.69, [["Lift-to-drag", "11.3"]]],

  "twinboom/gimbal/water": [3.01, 2.27, [["Reserve buoyancy, trim afloat", "2.5×, level"], ["Prop pylon", "18 cm"], ["Take-off run on the water", "18 m"], ["Landing load", "6.3 g"]]],
  "twinboom/dual/water": [2.33, 1.69, [["Reserve buoyancy, trim afloat", "2.7×, level"], ["Prop pylon", "18 cm"], ["Take-off run on the water", "15 m"], ["Landing load", "7.4 g"]]],
  "bwb/gimbal/water": [2.38, 1.48, [["Reserve buoyancy, trim afloat", "2.9×, level"], ["Prop pylon", "17 cm"], ["Take-off run on the water", "15 m"], ["Landing load", "7.4 g"]]],
  "bwb/dual/water": [1.97, 1.25, [["Reserve buoyancy, trim afloat", "2.9×, level"], ["Prop pylon", "17 cm"], ["Take-off run on the water", "12 m"], ["Landing load", "7.9 g"]]],
  "crescent/gimbal/water": [2.51, 2.20, [["Reserve buoyancy, trim afloat", "1.6×, 12° nose up"], ["Prop pylon", "19 cm"], ["Take-off run on the water", "16 m"], ["Landing load", "7.2 g"]]],
  "crescent/dual/water": [2.05, 1.87, [["Reserve buoyancy, trim afloat", "1.7×, 16° nose up"], ["Prop pylon", "24 cm"], ["Take-off run on the water", "13 m"], ["Landing load", "7.7 g"]]],

  "tailsitter/gimbal/vertical": [2.96, 1.81, [["Hover motors", "828 W peak, 0.22 kg"], ["Hover energy per sortie", "6.0 Wh"], ["Props above the water, afloat", "56 cm"], ["Throttle-up to wing-borne", "4.3 s"], ["Launches from the sea up to", "Sea state 3"], ["Landing onto the pods", "2.0 g"]]],
  "tailsitter/dual/vertical": [2.22, 1.40, [["Hover motors", "537 W peak, 0.16 kg"], ["Hover energy per sortie", "3.9 Wh"], ["Props above the water, afloat", "56 cm"], ["Throttle-up to wing-borne", "4.3 s"], ["Launches from the sea up to", "Sea state 4"], ["Landing onto the pods", "2.0 g"]]],
};

const TAKES = {
  "twinboom/deck": "Prints on a 220 mm bed and is the easiest to build, but it is the heaviest wing and the least efficient.",
  "bwb/deck": "The lightest bird for each camera choice. It needs moulds: the repo writes the plug files and a CNC ladder frame for them.",
  "crescent/deck": "The best lift-to-drag, printed like the twin-boom, at a wider span.",
  "twinboom/water": "Floats level, but its pusher prop needs an 18 cm pylon and it takes off from the water only in a flat calm.",
  "bwb/water": "Floats level with plenty of reserve. Taking off from the water still needs waves of no more than a few centimetres.",
  "crescent/water": "Barely enough reserve buoyancy, and it floats nose up: the weakest float plane of the three.",
  "tailsitter/vertical": "Heavier than the float plane, but it launches from the sea in real waves and lands at 2 g. Wind heeling it afloat, not the waves, is the limit.",
};

const state = { rig: "gecko5", airframe: "bwb", payload: "dual", recovery: "deck" };

const OPTIONS = {
  rig: RIGS, airframe: AIRFRAMES, payload: PAYLOADS, recovery: RECOVERY,
};

const $ = (id) => document.getElementById(id);

function kv(el, rows) {
  el.replaceChildren(...rows.flatMap(([k, v]) => {
    const dt = document.createElement("dt"); dt.textContent = k;
    const dd = document.createElement("dd"); dd.textContent = v;
    return [dt, dd];
  }));
}

function buildSegs() {
  document.querySelectorAll(".seg[data-group]").forEach((seg) => {
    const group = seg.dataset.group;
    for (const [key, opt] of Object.entries(OPTIONS[group])) {
      const b = document.createElement("button");
      b.type = "button";
      b.role = "tab";
      b.dataset.key = key;
      b.textContent = opt.label;
      b.addEventListener("click", () => {
        if (b.disabled) return;
        state[group] = key;
        render();
      });
      seg.append(b);
    }
  });
}

function syncSegs() {
  const vtol = state.airframe === "tailsitter";
  if (vtol) state.recovery = "vertical";
  else if (state.recovery === "vertical") state.recovery = "deck";
  document.querySelectorAll(".seg[data-group]").forEach((seg) => {
    const group = seg.dataset.group;
    seg.querySelectorAll("button").forEach((b) => {
      const on = state[group] === b.dataset.key;
      b.setAttribute("aria-selected", on);
      if (group === "recovery") {
        const offer = vtol ? b.dataset.key === "vertical" : b.dataset.key !== "vertical";
        b.hidden = !offer;
      }
    });
  });
}

function renderRig() {
  const r = RIGS[state.rig];
  $("rig-name").textContent = r.name;
  $("rig-what").textContent = r.what;
  $("rig-img").src = r.img;
  $("rig-img").alt = r.name;
  const dark = $("rig-dark");
  if (r.dark) { dark.media = "(prefers-color-scheme: dark)"; dark.srcset = r.dark; }
  else { dark.removeAttribute("media"); dark.srcset = r.img; }
  kv($("rig-stats"), r.stats);
  $("rig-take").textContent = r.take;
}

function renderBird() {
  const { airframe, payload, recovery } = state;
  const af = AIRFRAMES[airframe];
  const [mass, span, extra] = BIRDS[`${airframe}/${payload}/${recovery}`];
  $("bird-name").textContent = `${af.name}, ${PAYLOADS[payload].name}`;
  $("bird-what").textContent = af.what;
  $("bird-img").src = af.img[payload];
  $("bird-img").alt = af.name;
  $("bird-mass").textContent = `${mass.toFixed(2)} kg`;
  $("bird-span").textContent = `${span.toFixed(2)} m`;
  const rows = [PAYLOADS[payload].stat, ...extra];
  if (recovery === "water") {
    const [deck] = BIRDS[`${airframe}/${payload}/deck`];
    rows.unshift(["Cost of the float kit, sized in", `+${(mass - deck).toFixed(2)} kg`]);
  }
  if (recovery === "vertical") {
    const [deck] = BIRDS[`bwb/${payload}/deck`];
    rows.unshift(["Against the plain blended wing", `+${(mass - deck).toFixed(2)} kg`]);
  }
  kv($("bird-stats"), rows);
  $("bird-take").textContent = TAKES[`${airframe}/${recovery}`];
}

function render() {
  syncSegs();
  renderRig();
  renderBird();
}

buildSegs();
render();
