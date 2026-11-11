# Puffin at sea: markets for a craft that floats, flies and lands

This is a market study for a Puffin-derived electric tailsitter that lives on
the water. It floats tail-down, which is also its launch attitude. It rights
itself from any knockdown, lifts straight off, and transitions to wing-borne
flight. The design work is elsewhere; this note asks who would buy it, what it
would replace, and which market to design for first.

Two sizes are in scope:

| | **UAS** | **Single-seater** |
|---|---|---|
| Gross mass | 8–10 kg | about 600 lb (272 kg) |
| Payload | sensors, a flotation pack, a beacon, a 1–2 kg sample or part | 200 lb (91 kg): one person, or cargo when flown uncrewed |
| Crew | none | its occupant, or none (autonomous) |
| Afloat | 0.53 m draft, spar hull, battery and ballast low in the boom | the same layout, scaled |

The reference is NASA's Puffin (Moore, NASA Langley, 2010) [S1]. It is a
600 lb gross tailsitter with a prone pilot: 300 lb empty, 100 lb of batteries
and a 200 lb payload. It was sized for a 50 mile range at 200 Wh/kg and a
cruise of about 4× car speed, roughly 130 mph. Its prop-rotors have a 400 ft/s
tip speed, against 700–800 ft/s on conventional rotors, and its disc loading
is 6.8 lbf/ft², like a light helicopter's. Puffin was a technology
demonstrator, not a product. The paper does list "small search and rescue
UAVs" among the missions it could serve [S1]. With today's 300–400 Wh/kg
cells and the same 100 lb battery, the range scales to roughly 75–100 miles
before reserves (our first-order estimate, not a sizing result).

**The short answer:** design the UAS first, for search and rescue from boats
and rescue stations, with port and ship inspection as its second payload.
Build the full-size airframe uncrewed before anyone rides in it, as a two-way
shuttle: parts out to turbines and ships, provisions out to yachts at anchor,
and something back on every leg. The first person aboard should be a yacht
owner flying their own craft. The crewed pilot-transfer craft is the biggest
prize per flight, but it has the longest road (see
[Recommendation](#recommendation)).

## What being at home on the water buys

Most of what follows rests on four things this vehicle can do that today's
drones and small aircraft can't do together:

1. **It survives a ditching and waits.** A multirotor that ditches is lost; a
   fixed-wing that belly-lands is swamped by the first breaking sea. This
   craft floats upright and is still flyable. That turns "where do we land?"
   from a risk case into a non-question over open water.
2. **It loiters on the surface for almost nothing.** Afloat, it draws only
   avionics power. It can sit at a datum, a casualty, an anchorage or a
   turbine, and fly when it's needed.
3. **It touches the water.** It can mark a person in the water, drop or *be* a
   flotation aid, take a water sample, or sit beside a ship.
4. **It needs no deck.** It can launch from, and be recovered to, any boat that
   can reach it with a boathook, and doesn't need a landing pad or a net.

A market that values none of these is a market where an ordinary VTOL drone or
a helicopter will win.

## 1. Maritime pilot transfer

**The job.** A marine pilot boards every large ship entering or leaving a
compulsory-pilotage port, usually several miles offshore, day and night, in
most weather. They ride a pilot boat out and climb a rope ladder up the ship's
side, or a helicopter lowers them by hoist or lands them on deck.

**How big.**
- The International Maritime Pilots' Association represents more than 8,200
  pilots in 53 countries. That is about 70% of licensed pilots, and between
  them they carry out over two million acts of pilotage a year [S2].
- The Netherlands alone pilots about 90,000 seagoing ships a year [S12].
  Norway carried out 38,200 pilot assignments in 2024 [S9].
- The UK's harbour authorities reported 96,000 pilot transfers in 2022 [S3].

**What it costs today.**
- **Pilot boats.**
  - New ones cost about $2.5–8 M each. A standard design runs $2–3 M and a
    custom offshore boat $5–8 M [S13]. San Francisco's three boats cost about
    $6 M each over 2010–14 [S15].
  - Houston paid $31 M for two SWATH boats [S14].
  - Crews and maintenance come on top, and a station runs several boats for
    24/7 cover.
- **Helicopters.**
  - The Pacific Pilotage Authority's northern BC helicopter service charges
    **$16,900 per transfer, inbound or outbound** [S5]. The fee recovers a
    fixed standby charge, flight hours, training and overhead, spread over the
    LNG carrier traffic it expects. The 2021 tender estimated 500 flight hours
    a year in daylight and 700 for 24/7 [S7].
  - The same authority runs a 24/7 hoist contract at Vancouver with an AS365
    Dauphin [S6].
- **Where helicopters are used.** Helicopters are the exception, used where
  the bar or boarding ground is too rough or too far.
  - Norway flies about 1,100 helicopter assignments a year, all for tankers
    and gas carriers calling at five oil and gas terminals, and the users pay
    for it [S8].
  - The Columbia River bar pilots use the helicopter as their primary boarding
    method, with a pilot boat on standby, across about 3,500 ship moves a year
    [S10]. Oregon funds it through per-transit surcharges [S11].

**Why it's a market.** Transfer is the dangerous part of the job.
- The UK's 96,000 transfers in 2022 produced over 400 incidents and accidents,
  and a pilot was killed transferring in the Humber in January 2023 [S3].
- IMPA's own survey found 13% of ladders non-compliant in 2024 [S4].
- IMO has rewritten SOLAS regulation V/23 on pilot transfer arrangements:
  resolution MSC.572(110) takes effect on 1 January 2028 and bans mechanical
  pilot hoists [S16][S17].

**Who decides.** Pilots' associations, which are often self-governing and
licensed by a state commission, decide alongside port or pilotage authorities
and tariff regulators. Shipowners pay through the tariff. Decision-makers care
about:
- the transfer safety record;
- availability round the clock and in rough seas;
- cost per transfer, which a regulator has to approve;
- acceptance by the pilots themselves and their unions;
- how the method fits ship-side rules: the SOLAS boarding arrangements and the
  industry guide to helicopter-ship operations.

**Fit.**
- **Crewed single-seater: the obvious target, with one hard catch.** The
  hazard is the ladder, not the ride out. A craft that lands *in the water
  alongside* still leaves the pilot climbing the same ladder from a smaller,
  livelier platform than a pilot boat. That is worse, not better. The value
  appears only if it lands **on deck**, on hatch covers or a marked
  helicopter area, the way helicopters already do. That puts the design up
  against:
  - wind shear around the superstructure and cranes;
  - a moving deck;
  - a prone occupant getting out on a rolling ship.

  Flotation and self-righting then become ditching safety, not the operating
  mode.
- **Price ceiling.** Between $16,900 per helicopter transfer and a few hundred
  dollars per pilot-boat transit [S5][S11], a one-seat electric craft could
  win where helicopters are used today (terminals, bars, remote ports) if it
  could do several transfers per charge for under a few thousand dollars
  each. Volumes there are thousands of transfers a year, not millions.
- **UAS: none for carrying people.** It could carry the pilot's documents,
  portable pilot units or small parts out to a ship at anchor. Wilhelmsen and
  Airbus trialled shore-to-ship drone deliveries at Singapore's anchorages
  [S40].

## 2. Search and rescue at sea

**The job.** Find a person or craft in the water, keep them in sight, keep
them afloat, and get them out. Finding them, and the minutes before a lifeboat
or helicopter arrives, is where a small aircraft helps. Recovery needs a boat
or a hoist.

**Who buys, and what they use now.**

| Buyer | Today | Scale and cost |
|---|---|---|
| National coast guards | Helicopters, fixed-wing, cutters; increasingly drones | USCG flies 98 MH-65s from 14 air stations [S20] and reports more than 14,000 rescues and 6,000 lives saved in FY2024 [S19]. The UK's 2nd-generation SAR aviation contract is £1.6 bn over 10 years. The award notice is worth about £1.96 bn through 2036, and the contract includes Schiebel S-100 drones [S21]. USCG pays up to $198 M over 5 years for contractor-operated V-BAT drones on its cutters, at least 12 h of flying a day [S22]. |
| Lifeboat services | Inshore and all-weather lifeboats, volunteer crews | RNLI lifeboats launched 9,141 times in 2024 and saved 352 lives [S18]. The Swedish Sea Rescue Society has applied for SORA 2.5 approval of coastal BVLOS drone operations [S24]. |
| Offshore oil and gas standby | Emergency Response and Rescue Vessels (ERRVs) with daughter craft | One operator runs 37 ERRVs covering about 50 North Sea installations [S25]. Another won £36 M of ERRV contract awards and extensions [S26]. No public day rate. |
| Offshore wind | ERRVs during construction; CTV and SOV crews for operations and maintenance | CTVs charter for about €4,000–8,000 a day [S27] and SOVs for about $30,000–60,000 a day [S28] (generic estimate). |
| Local and beach rescue | Lifeguards, sheriffs' offices, drones with drop pods | Drones already drop flotation to swimmers in rip currents [S54]. Tekever's AR5 dropped a life raft in an Italian Coast Guard and EMSA exercise [S23]. |

**What decision-makers care about:**
- time to the casualty;
- seeing in the dark and in spray (thermal imaging);
- operating in the weather when people actually get into trouble;
- regulatory approval to fly beyond line of sight near helicopters;
- crew workload;
- the cost of a capability that sits idle most of the time.

Coast guards increasingly buy *services*, flight hours or hours of coverage,
rather than aircraft [S21][S22].

**Fit.**
- **UAS: strong.** It launches from a lifeboat, ERRV, CTV or yacht in seconds
  and flies a search pattern. Then it **lands beside the casualty and stays
  there**: a strobe, a radio beacon and a thermal hot-spot marking the datum
  while the boat comes. It needs no deck to get back. It can carry a 1–2 kg
  self-inflating aid, or be the aid itself as something to hold onto. Ditching
  costs nothing, so it can fly in weather that would ground a multirotor
  whose loss is final. This is also Osprey Recon's man-overboard mission (see
  [recon.md](../recon.md)), so the mission models already exist.
- **Single-seater: weak.** Its 200 lb payload is its occupant, so it can't
  bring a casualty back. It could put a rescue swimmer or paramedic beside a
  casualty fast, or go out uncrewed with a liferaft and pumps. Coast guards
  buy hoisting helicopters, and that's hard to displace.

## 3. Ship and port inspection

**The job.** Ports and authorities watch and check ships:
- customs and security sweeps of hulls, waterlines and cargo;
- port-state control and draft-mark checks;
- emissions enforcement under sulphur and NOx caps;
- spill and ballast-water checks;
- surveillance of a busy, closed area.

**What's there now.**
- **Emissions sniffing.**
  - EMSA runs a remotely piloted aircraft service for the Danish authorities.
    A Skeldar V-200 flies through ships' exhaust plumes in the Great Belt and
    estimates their fuel sulphur content, which tells the authorities whether
    each ship is compliant.
  - Results go in real time into THETIS-EU, the EU's port-state control
    database, for follow-up. The flights run under a waiver for 50 km beyond
    line of sight [S36].
- **Port security networks.** Antwerp-Bruges runs six drones from docking
  boxes over its 120 km² port, operated as a service. They flew 1,099
  autonomous flights in the first months of 2025 [S37].
- **Hulls below the waterline.** Divers and ROVs do this work. Customs and
  border agencies use ROVs on hulls, and a diver team is typically 3–4 people.
  One shipowner put diver inspections at over $2,000 a day [S38]. Those
  figures come from an ROV vendor's materials.
- **Volume.** Container ships alone made almost 250,000 port calls in the
  second half of 2023 [S39], and tankers and bulkers add more.

**Who decides.** Port authorities, customs and border agencies, environmental
agencies and EMSA-type bodies decide, as do terminal operators. They care
about:
- evidence that stands up in enforcement;
- coverage of a crowded, controlled airspace and seaway;
- reliability and drone-in-a-box automation;
- the cost per flight hour or per ship checked;
- not getting in the way of ship traffic.

**Fit.**
- **UAS: good as a second payload, but not on its own.** Docked multirotors
  already cover port surveillance well. The float-and-fly airframe adds three
  things:
  - It **samples water**: sheen, ballast discharge, grey water.
  - It **waits on the surface** at an anchorage or a sniffing station without
    a box or mast.
  - It reaches anchorages and approaches that a dock-based drone can't cover
    in one flight.
- **It doesn't replace hull inspection.** Under the waterline is ROV work.
- **Single-seater: none.** A crewed craft adds nothing over a launch here.

## 4. Offshore crew and parts transfer, and other missions

**Parts and tools to turbines and platforms.** This is the most active
uncrewed-cargo market at sea right now:
- **RWE, at its German wind farms:**
  - Skyways fixed-wings carried up to 10 kg 40 km from port to the Arkona
    wind farm in under 30 minutes, against over an hour by boat.
  - Short flights from a service vessel at Nordsee Ost carried up to 30 kg.
  - More than 250 flights moved over nine tonnes of tools and parts at Triton
    Knoll [S29].
- **Ørsted:**
  - It frames the case as boat-to-nacelle delivery [S30].
  - It reports that a crane lift to a nacelle took two lifts and up to a
    six-hour shutdown, against about five minutes by drone, using DJI FlyCart
    100s with Skyports at Hornsea 2 [S31]. That figure is self-reported.
- **Add2Wind:** a Danish project with Ørsted, Vattenfall, Siemens Gamesa and
  Vestas delivered parts of up to 40 kg to offshore turbines [S32].
- **Equinor:** a Schiebel S-100 flew a 3D-printed part to the Troll A platform
  in 2020. A contract with Nordic Unmanned followed, for cargo flights to
  Gullfaks, 170 km offshore, and daily flights between installations and
  vessels [S33].
- **Navies:**
  - The US Navy's Blue Water logistics UAS programme is paying PteroDynamics
    over $7 M to develop a folding-wing VTOL for ship-to-ship and ship-to-shore
    parts delivery [S41]. Australia has also ordered it.
  - The Royal Navy has moved packages between ships by quadcopter [S42].
- **Market size.** Offshore wind passed 92.5 GW at the end of 2025 [S34]. At
  5–10 MW per turbine, that is roughly 10,000–15,000 turbines (our estimate),
  each visited for maintenance several times a year.

**Crew transfer is a shipping system.** Judged one seat at a time, it looks
hopeless:
- Offshore crews move by CTV and SOV in wind, and by helicopter in oil and
  gas. The North Sea flies almost two million offshore helicopter passengers a
  year, on aircraft rented at up to £4,500 an hour [S35]. Those figures are
  from older sources.
- A one-seat craft competes with a 16–19-seat helicopter or a 12–24-person
  CTV, and loses on cost per seat.

That's the wrong comparison. A crew boat carries crew out and comes back
empty or half empty. This craft's 200 lb payload works either way, so every
leg can carry something:
- a technician out, the failed part back;
- a person ashore, groceries or spares back out;
- a part out, a water sample or the mail back.

What it competes on is **trips per hour and the load on each leg**, not seats.
It wins where the loads are small, urgent and frequent, and where a boat would
go out mostly empty.

A rough energy check (our estimate, not a sizing result): Puffin needs about
60 hp (45 kW) to hover [S1]. Half a minute of hover at each end of a short hop
is about 0.75 kWh, and a few minutes of cruise adds a similar amount. A 100 lb
pack at 300–400 Wh/kg holds 13–18 kWh, so a charge covers something like
8–10 short legs with reserve. That means the energy goes into the hovers, not
the distance. A short-hop shuttle wants a quick water start and landing more
than it wants range.

**Fit.**
- **Single-seater, uncrewed, as a 200 lb two-way cargo shuttle: good.** It
  replaces a CTV run or a crane lift for a single part, and brings something
  back. If it goes in the water short of the turbine, it floats and is
  recovered, where a ditched multirotor sinks. It is also the honest first
  step to the crewed version: the same airframe, proven without anyone aboard.
- **Single-seater, crewed: good only as part of the shuttle.** On its own it
  loses on cost per seat. It makes sense for urgent single trips, with
  something carried back on the return leg. Those trips include a technician
  to a fault, a medic, or a person brought off with a minor injury.
- **UAS: limited.** It carries 1–2 kg, so it suits tools, samples and
  documents. FlyCart-class multirotors already carry 30–80 kg.

**Other float/fly/land missions worth noting:**
- **Marine mammal watch for offshore construction.** Pile driving and seismic
  surveys need observers. A drone that sits afloat and flies circuits is a
  natural platform.
- **Sea-ice, met-ocean and spill sampling** from ships that have no flight
  deck.
- **Fisheries and border enforcement** at the edge of a cutter's range. V-BAT
  is the incumbent on cutters [S22].
- **Yacht and expedition tenders.** A drone that scouts the anchorage and goes
  back aboard by boathook is Osprey Recon's own mission.

## 5. The anchorage shuttle: people ashore, provisions back

**The job.** Watch a busy anchorage or mooring field at eight in the morning.
Dozens of tenders and dinghies run between the boats and one dinghy dock,
carrying:
- crew and guests going ashore;
- groceries, ice, fuel cans, laundry and rubbish;
- parts for whatever broke overnight.

Each trip is short, light and urgent. Most legs run half empty, and they all
converge on the same few metres of dock. It is the offshore shuttle in
miniature, with many more operators.

**Who and how many.**
- **Superyachts.** Yachts over 30 m are a fleet of about 6,200: 6,174 in
  service in August 2025, 63% of them 30–40 m long [S55]. These yachts run
  their own tenders all day, crewed by paid crew.
- **Private yachts at anchor or on moorings.** There are many more of these,
  in every cruising ground. The owners run their own dinghies.
- **Harbour launches.** These carry people between moorings and the shore.
  - Vineyard Haven lists $5 per person per trip [S58].
  - Annapolis's water taxi charges $7–8 one way [S58].
  - Some harbours fold the launch into the mooring fee [S58].
- **Drone delivery to yachts is starting.**
  - A drone carried Champagne and caviar to a superyacht off Monaco in 2023,
    with the aviation authority's backing. Its operators talked of a next
    phase delivering up to 40 kg on demand [S57].
  - A Riviera start-up began commercial drone deliveries to yachts anchored
    off Juan-les-Pins in August 2026 [S56]. Provisioning agents book the
    flight, and the drone flies only the last leg from the port to the yacht.
  - Wilhelmsen and Airbus did the same for supply vessels at anchor in
    Singapore [S40].

**Who decides, and what they care about.**
- **Yacht owners and captains** care about convenience, time, how the craft
  looks and sounds at anchor, and the safety of guests and crew.
- **Provisioning agents and marinas** care about cost per delivery, how many
  days the weather allows them to fly, and the noise complaints they would get.
- **Harbourmasters** care about traffic over moorings, swimmers and the dinghy
  dock. They will decide where it may land.

**Fit.**
- **People are the wrong cargo to start with.** A $5–8 launch ride [S58] sets
  the price, and a dinghy is cheaper still. A flying shuttle only beats them
  for distance or time: an anchorage miles from town, an island with no
  launch, or a superyacht whose owner values the minutes.
- **Provisions and parts are the right cargo.** They are the load that drones
  have started to carry [S56][S57], and every leg has a return load.
- **Uncrewed full-size: good.** Its 200 lb payload is a week's provisions or a
  heavy part in one trip, which multirotors carrying 10–40 kg can't match.
  Floating means a missed delivery lands in the water instead of sinking.
- **Crewed: plausible as the owner's own aircraft.** An owner flying their own
  craft between their yacht and the shore is personal flying. That is what
  light-sport covers [S44], and it avoids the for-hire problem that blocks
  pilot transfer. Paid crew flying the owner is a different case and needs
  the legal opinion noted under [Regulation](#regulation).
- **The hard part is the landing.** The madness is at the dinghy dock: swimmers,
  paddleboards, children and moving boats. A craft that lands on the water
  near that, with props turning, needs:
  - its own landing patch at the edge of the anchorage, away from swimmers;
  - very low noise, which low-tip-speed props help with [S1];
  - a way to come alongside a dock or a swim platform after landing, which a
    spar hull floating tail-down doesn't do well yet.

## Regulation

### UAS (8–10 kg)

- **United States.**
  - **Part 107 (below 55 lb).** Beyond-line-of-sight flight needs a waiver
    today.
  - **Part 108.** This is the BVLOS rule. The FAA sent the final rule to the
    White House for review on 10 July 2026, and it was still unpublished in
    mid-September [S45]. The 2025 proposal set weight tiers of 55, 110 and
    1,320 lb, and limited package delivery under a permit to 55 lb [S45].
  - **Over water.** Ground risk at sea is low, but air risk near ports,
    helicopter routes and SAR traffic is not.
- **EU (2019/947) and the UK.**
  - The Open category stops at 25 kg and visual line of sight. Maritime BVLOS
    work is in the Specific category, under a SORA risk assessment or a
    predefined scenario (PDRA) [S46].
  - **Moving boats.** The PDRA-S01 scenario says the remote pilot should not
    operate from a moving vehicle [S46]. Launching from a moving lifeboat
    therefore likely needs a full SORA.
  - **Precedents.** V-BAT holds a SORA SAIL III maritime authorisation from a
    Frontex project in Italy [S46]. The Swedish Sea Rescue Society is seeking
    coastal BVLOS under SORA 2.5 [S24]. The UK has flown BVLOS across the
    Solent inside a temporary danger area [S53].
- **Marine side.** A small drone afloat isn't registered as a vessel anywhere
  we found. In practice it is an object in the water near traffic, so it
  should carry a light and be easy to see and recover.

### Single-seater (600 lb gross)

- **US Part 103 ultralight: not an option.**
  - Part 103 requires an empty weight below 254 lb, excluding floats and
    emergency parachutes, with a single occupant. Recreation and sport only
    [S43].
  - Floats are excluded; secondary sources cite about 30 lb per float under
    AC 103-7, and the FAA has been read as counting batteries in the empty
    weight [S43]. Puffin's empty weight alone is 300 lb, before 100 lb of
    batteries [S1].
  - A UAS-scale or half-scale recreational derivative could fit, the way LIFT
    Hexa's float allowance did [S43]. A pilot-transfer craft can't.
- **US light-sport under MOSAIC (Part 22): the plausible personal path.**
  - Since 24 July 2026, light-sport aircraft can be powered-lift and
    multicopters [S44].
  - ASTM F3840-26, accepted on 16 July 2026, is the first light-sport
    standard for them [S44].
  - The fixed weight cap is gone [S44]; a 61 kt stall limit is cited [S44].
  - Light-sport covers personal flying, not carrying people for hire [S44].
  - **Business use:** a pilots' association flying its own members to work is
    neither plainly personal nor plainly for hire. It needs a legal opinion
    before any design commitment.
- **Autonomous, carrying a person.** No light path exists. That means
  certification as a powered-lift special class under Part 21, as the air
  taxi companies are doing [S44].
- **Uncrewed with cargo.** This falls under the UAS rules at the 1,320 lb
  tier: Part 108 when final, or exemptions until then [S45]. That is a far
  shorter path than carrying a person.
- **Europe.** Microlights up to 600 kg are left to national rules: member
  states may opt out of EASA for them [S47]. Rules differ by country, and few
  cover powered-lift. EASA's eVTOL rules address air taxis, not one-seat
  personal aircraft.
- **Marine side.**
  - Under the collision regulations (COLREGs), "vessel" includes seaplanes,
    meaning any aircraft designed to manoeuvre on the water (Rule 3; US Inland
    Rules 33 CFR 83.03) [S48].
  - On the water a seaplane must keep well clear of all vessels but follow the
    steering rules when risk of collision exists (Rule 18(e)) [S48]. It shows
    seaplane lights (Rule 31) [S48].
  - The FAA separately requires an aircraft on the water to keep clear of
    vessels (14 CFR 91.115) [S48].
  - So this craft is an aircraft that obeys the COLREGs while afloat. It is
    not a registered vessel.
  - **The precedent if that changes.** REGENT's seagliders are wing-in-ground
    craft that never leave ground effect, and they are being certified by the
    US Coast Guard under vessel rules, not by the FAA [S49]. A Puffin that
    climbs out of ground effect stays an aircraft.
- **Ship side (pilot transfer).** Deck landing comes under SOLAS boarding
  arrangements, as revised from 2028 [S16]. It also comes under the
  shipping-industry guide to helicopter-ship operations: marked landing and
  winching areas, deck crews, firefighting. A ship will treat a one-seat
  aircraft as a helicopter until a standard says otherwise.

## Competitors and prior art

| Craft | What it is | Relevance |
|---|---|---|
| NASA Puffin (2010) [S1] | 600 lb electric tailsitter, prone pilot, low-tip-speed props | The reference design; never built full size |
| Shield AI V-BAT [S22][S46] | Ducted-fan tailsitter UAS, 125 lb class, launched from and recovered to cutters | The incumbent tailsitter at sea. It needs a deck or a net and doesn't float. USCG contract up to $198 M [S22] |
| Schiebel Camcopter S-100 [S21][S33] | Rotary UAS, about 200 kg | UK coastguard SAR and Equinor logistics; needs a deck |
| Tekever AR5 [S23] | Fixed-wing UAS with radar and liferaft drop | EMSA and coast guard maritime surveillance |
| Skeldar V-200 [S36] | Rotary UAS with a sniffer | EMSA emissions monitoring |
| PteroDynamics Transwing [S41] | Folding-wing VTOL cargo UAS | US and Australian navies' ship logistics; the closest analogue for the uncrewed cargo version |
| DJI FlyCart, Skyways [S29][S31] | Multirotor and fixed-wing cargo | Offshore wind parts delivery; neither floats |
| Aeromao VT-Naut [S51] | Small tailsitter VTOL with salt-resistant parts | Takes off vertically, then *belly-lands* on water. The closest small prior art |
| Aeromapper Talon Amphibious [S51] | Fixed-wing that belly-lands on water | Recovery on water, but not VTOL |
| SwellPro SplashDrone and Spry; HoverAir Aqua [S51] | Waterproof multirotors that float. SwellPro's "Powerflip" flips them upright | Floating and self-righting is proven at consumer scale, with no range or endurance |
| LIFT Hexa [S50] | Part 103 single-seat multicopter with floats | Has taken off from and landed on water; uses the float exemption |
| Pivotal BlackFly and Helix [S50] | Part 103 single-seat tilt-wing eVTOL, keel hull | Repeated fresh-water landings; recreational |
| REGENT seaglider [S49] | Electric wing-in-ground craft on a hydrofoil | Coast Guard-regulated sea mobility; aimed at passenger and defence markets |
| Inflatable ducts and wings [S52] | A patent for a collapsible ducted-fan UAS with an inflatable duct; ILC Dover's inflatable wings; a drone with an inflatable wing | Prior art for inflatable shrouds and bladders. None we found is aimed at water landing |

We found no one building a floating, self-righting VTOL tailsitter, or any
eVTOL for pilot transfer. A 2024 international study is looking instead at
*remote* pilotage, which would take the pilot off the ship altogether [S2].

## Recommendation

Ranked by which market to design for first:

1. **UAS for search and rescue from boats and rescue stations**, including
   offshore wind and oil-and-gas standby.
   - Every float/fly/land ability is used: launch from any boat, ditch without
     loss, mark the casualty afloat, get back aboard by boathook.
   - The rules exist today: Part 107 with waivers, SORA in Europe, over
     low-risk water.
   - Buyers exist and are buying drones and services now [S21][S22][S24].
   - It extends Osprey Recon's man-overboard mission, which is already
     modelled.
   - Risk is low and units are many, so it is the place to prove the spar
     hull, the righting and the water start.
2. **The same UAS with an inspection payload for ports and approaches.**
   - Payloads: emissions sniffing, water sampling, anchorage watch.
   - It adds sales to the first airframe, but alone it would lose to docked
     multirotors. Sell it as the payload that comes second.
3. **The full-size airframe flown uncrewed as a two-way shuttle.** It would
   carry parts to turbines, platforms and ships, and provisions to yachts at
   anchor, with something back on every leg.
   - Demand is proven offshore by RWE, Ørsted, Equinor and the navies
     [S29][S31][S33][S41]. In anchorages, drone delivery to yachts has started
     [S56][S57].
   - The regulatory path is a drone path, not a manned one.
   - Floating is a real advantage over multirotors.
   - Its 200 lb payload outcarries the 10–40 kg drones now in service.
   - It flies the exact airframe the crewed version needs, without a person
     aboard.
4. **The crewed single-seater as a yacht owner's own shuttle.**
   - It carries the owner ashore and brings provisions back.
   - Owner-flown is personal flying, so light-sport covers it [S44]. That is
     the shortest road to a person aboard.
   - The superyacht fleet alone is about 6,200 boats [S55], and those buyers
     pay for time.
   - Landing near a crowded dinghy dock is the hardest safety and noise case
     in this study. It needs a landing patch away from swimmers and a way to
     come alongside after landing.
5. **The crewed single-seater for pilot transfer.**
   - It is the highest value per flight, with helicopter transfers at up to
     $16,900 each [S5], and the strongest safety story [S3].
   - It only pays if it lands on deck, because a water landing alongside keeps
     the ladder.
   - It needs a business-use certification path that light-sport doesn't give
     [S44].
   - Pilots' associations and tariff regulators are rightly conservative.
   - Keep it as the long-term goal. Steps 1–4 should prove the airframe, the
     floating safety case and an operating record first.
6. **The crewed single-seater for SAR.** It can't bring a casualty back. Leave
   it until the craft exists for other reasons.

## Sources

Figures are as reported by the sources. Several are vendor or trade-press
claims, or older figures, and are marked as such in the text. Accessed
November 2026.

- [S1] Moore, M. D., *NASA Puffin Electric Tailsitter VTOL Concept*, AIAA ATIO 2010. <https://ntrs.nasa.gov/citations/20110011311>
- [S2] IMPA, *About IMPA*. <https://www.impahq.org/about-impa>; remote pilotage study: <https://cyprusshippingnews.com/2024/08/29/international-study-on-remote-pilotage-to-be-undertaken-by-maritime-pilots/>
- [S3] MarineLink, *MAIB concerned at pilot ladder incidents*. <https://www.marinelink.com/news/maib-concerned-pilot-ladder-incidents-506637>
- [S4] IMPA, *Safety Campaign Results 2024*. <https://safety4sea.com/wp-content/uploads/2024/11/IMPA-Safety-Campaign-Results-2024_11.pdf>
- [S5] Pacific Pilotage Authority, *Announcement of Revised Service Charges (North Helicopter)*, Sept 2026. <https://www.ppa.gc.ca/standard/pilotage/2026-09/Announcement%20of%20Revised%20Service%20Charges%20%28North%20Helicopter%29%20Sept%201%2C%202026_1.pdf>
- [S6] HeliHub, *Talon Helicopters awarded helicopter hoisting contract from Pacific Pilotage*, 2024. <https://www.helihub.com/2024/05/15/talon-helicopters-awarded-helicopter-hoisting-contract-from-pacific-pilotage/>
- [S7] PPA helicopter RFP 2021, answers to proponents. <https://canadabuys.canada.ca/documents/pub/att/2021/07/30/d4c6a4471bf4a792a047bcc0808d795f/ppa_helicopter_rfps_2021_-answers_to_questions_from_proponents.pdf>
- [S8] Kystverket, *Pilot transport*. <https://kystverket.no/en/navigation-and-monitoring/pilotage/pilot-transport>
- [S9] Kystverket, *Fees 2025*. <https://www.kystverket.no/en/news/fees-2025>
- [S10] Professional Mariner, *Helicopter or boat – for bar pilots it's all about safe transfers*. <https://professionalmariner.com/helicopter-or-boat-for-bar-pilots-its-all-about-safe-transfers/>
- [S11] Oregon Board of Maritime Pilots, tariff (July 2026). <https://www.oregon.gov/puc/bmp/Forms/Tariff%207-15-2026.pdf>
- [S12] CGI, *Dutch Pilots' Organization case study*. <https://www.cgi.com/en/case-study/transportation-and-logistics/dutch-pilots-organization-facilitating-safe-and-efficient-pilotage>
- [S13] Sea to Summit, Grays Harbor pilot boat *Vega*. <https://sea-to-summit.net/astoria-yard-upgrades-former-l-a-pilot-boat-for-grays-harbor/>
- [S14] Houston Chronicle, *Christening a new era*, 2017. <https://www.pressreader.com/usa/houston-chronicle/20171021/281934543189218>
- [S15] California Board of Pilot Commissioners, SF Bar Pilots vessel cost comparison, 2020. <https://bopc.ca.gov/wp-content/uploads/sites/41/2020/11/4-6-2020-11-09-SFBP-Similar-PV-Cost-Comparisons-R.pdf>
- [S16] ABS, *Amendments to SOLAS Regulation V/23 – Pilot Transfer Arrangements*. <https://ww2.eagle.org/en/rules-and-resources/regulatory-updates/SOLAS-Pilot-Transfer-Arrangements.html>
- [S17] UK P&I, *Enhancing the safety of pilot transfer arrangements*. <https://www.ukpandi.com/news-and-resources/news/article/enhancing-the-safety-of-pilot-transfer-arrangements/>
- [S18] RNLI, *Data reveals RNLI lifeboat crews launched over 9,000 times last year*, April 2025. <https://rnli.org/news-and-media/2025/april/02/data-reveals-rnli-lifeboat-crews-launched-over-9000-times-last-year>
- [S19] DHS Office of Homeland Security Statistics, *Maritime response*. <https://ohss.dhs.gov/topics/maritime/maritime-response>; FY2024 figures as reported in <https://www.yahoo.com/news/surviving-seas-coast-guard-prepares-220000791.html>
- [S20] Airbus, *MH-65*. <https://us.airbus.com/en/helicopters/products-and-services/military-helicopters/mh-65>
- [S21] Vertical, *Bristow wins £1.6B UKSAR2G contract*. <https://verticalmag.com/news/bristow-wins-1-6b-uksar2g-contract/>; UK government, *Government contract uses the latest technology for search and rescue*. <https://www.gov.uk/government/news/government-contract-uses-the-latest-technology-for-search-and-rescue>
- [S22] Naval News, *USCG awards contract to procure cutter-based UAS capability*, 2024. <https://www.navalnews.com/naval-news/2024/06/uscg-awards-contract-to-procure-cutter-based-uas-capability/>
- [S23] DroneLife, *Tekever AR5 demonstrates lifeboat deployment in Italian Coast Guard SAR exercise*, 2024. <https://dronelife.com/2024/02/02/tekever-ar5-drone-successfully-demonstrates-lifeboat-deployment-in-italian-coast-guard-search-and-rescue-exercise/>
- [S24] Unmanned Airspace, *Swedish Sea Rescue Society submits SORA 2.5 application*. <https://www.unmannedairspace.info/uncategorized/swedish-sea-rescue-society-submits-sora-2-5-application-for-bvlos-drone-operations/>
- [S25] MarineLink, *North Star nets multi-year North Sea safety vessel contracts*. <https://www.marinelink.com/news/north-star-nets-multiyear-north-sea-539071>
- [S26] Baird Maritime, *Sentinel Marine bags £36 million in new contracts, extensions*. <https://www.bairdmaritime.com/work-boat-world/offshore-world/offshore-operations-maintenance/standby-rescue-emergency-services/sentinel-marine-bags-36-million-in-new-contracts-extensions>
- [S27] Clarksons, *Essential vessels for offshore windfarm construction and operations*, 2023. <https://www.clarksons.com/home/news-and-insights/2023/essential-vessels-for-offshore-windfarm-construction-and-operations/>
- [S28] ShipUniverse, *The offshore wind boom* (generic rate estimates). <https://www.shipuniverse.com/the-offshore-wind-boom-what-shipowners-need-to-know/>
- [S29] RWE, *RWE successfully pioneers cargo drone operations at offshore wind farms*, Oct 2025. <https://www.rwe.com/en/press/rwe-offshore-wind-gmbh/2025-10-15-rwe-successfully-pioneers-cargo-drone-operations-at-offshore-wind-farms/>
- [S30] Ørsted, *How Ørsted uses drones in offshore wind*. <https://orsted.com/en/offshore-wind/innovation/drones-to-save-time-and-money-in-offshore-wind>
- [S31] DroneXL, *Ørsted, Skyports and DJI FlyCart 100 at Hornsea 2*, Oct 2026. <https://dronexl.co/2026/10/19/orsted-skyports-dji-flycart-100-hornsea-2-toolkits/>
- [S32] Energy Cluster Denmark, *Drone project demonstrates airborne delivery of spare parts to wind turbines*. <https://energycluster.dk/en/projects/results/drone-project-demonstrates-airborne-delivery-of-spare-parts-to-wind-turbines>
- [S33] Offshore Technology, *Equinor completes drone operation to Troll platform*. <https://www.offshore-technology.com/news/equinor-completes-drone-operation-troll-platform/>; MarketScreener, *Nordic Unmanned wins offshore logistics contract with Equinor*. <https://www.marketscreener.com/quote/stock/NORDIC-UNMANNED-AS-116611571/news/Nordic-Unmanned-Wins-Offshore-Logistics-Contract-with-Equinor-37405524/>
- [S34] GWEC, *Global Offshore Wind Report 2025*. <https://gwec.net/news/offshore-wind-installed-capacity-reaches-83-gw-as-new-report-finds-2024-a-record-year-for-construction-and-auctions>; 2026 edition as reported by Modern Power Systems. <https://www.modernpowersystems.com/news/gwec-unveils-offshore-wind-plan-as-global-capacity-hits-92-5-gw/>
- [S35] NS Energy, *Transport logistics: personnel* (older figures). <https://www.nsenergybusiness.com/features/featuretransport-logistics-personnel/>
- [S36] EMSA, *RPAS drones monitored ship emissions in Danish waters*. <https://www.emsa.europa.eu/newsroom/latest-news/item/3513-rpas-drones-now-monitoring-ship-emissions-in-danish-waters.html>
- [S37] Port of Antwerp-Bruges, *Drone network officially launched*. <https://newsroom.portofantwerpbruges.com/world-first-in-antwerp-port-area-drone-network-officially-launched>; DroneMatrix, 2025 milestone. <https://www.dronematrix.eu/news/dronematrix-hits-new-milestone-in-autonomous-operations-at-port-of-antwerp-bruges>
- [S38] Deep Trekker (ROV vendor), *ROVs in customs and border protection*. <https://www.deeptrekker.com/resources/rovs-in-customs-and-border-protection>; Chugoku Paints customer story. <https://www.deeptrekker.com/learn/customer-story-chugoku-paints>
- [S39] UNCTAD, *Review of Maritime Transport 2024*, ch. 4. <https://unctad.org/system/files/official-document/rmt2024ch4_en.pdf>
- [S40] Maritime Executive, *Wilhelmsen and Airbus trial drone deliveries to Singapore anchorage*. <https://maritime-executive.com/article/wilhelmsen-and-airbus-trial-drone-deliveries-to-singapore-anchorage>
- [S41] sUAS News, *PteroDynamics awarded US Navy contract for Transwing VTOL UAS*, 2025. <https://www.suasnews.com/2025/02/pterodynamics-awarded-u-s-navy-contract-to-develop-next-gen-autonomous-transwing-vtol-uas-2/>; Defence Blog, *Australia selects Transwing for ship logistics*. <https://defence-blog.com/australia-orders-u-s-made-transwing-vtol-drones-for-ship-logistics/>
- [S42] Brookes Bell, *HMS Prince of Wales conducts Royal Navy's first ship-to-ship cargo drone transfer*. <https://www.brookesbell.com/news-and-knowledge/hms-prince-of-wales-conducts-royal-navys-first-ship-to-ship-cargo-drone-transfer-159600/>
- [S43] 14 CFR 103.1. <https://www.ecfr.gov/current/title-14/chapter-I/subchapter-F/part-103/subpart-A/section-103.1>; migflug, *Part 103 eVTOL: the 254-pound limit includes your batteries* (secondary). <https://migflug.com/afterburner/?p=31823712>; Plane & Pilot, *LIFT Hexa* (float allowance). <https://planeandpilotmag.com/a-multicopter-for-the-rest-of-us-part-103-evtol-hexa-is-preparing-for-a-u-s-tour/>
- [S44] FAA, *MOSAIC*. <https://www.faa.gov/aircraft/MOSAIC>; Federal Register 2025-13972. <https://www.govinfo.gov/content/pkg/FR-2025-07-24/html/2025-13972.htm>; AeroCorner, *The FAA's MOSAIC rules take effect*, July 2026. <https://aerocorner.com/news/faa-mosaic-light-sport-evtol-rule/>
- [S45] UAV Coach, *Part 108 stuck at the White House*, 2026. <https://uavcoach.com/part-108-stuck/>; DLA Piper, *FAA proposes comprehensive BVLOS framework*, 2025. <https://www.dlapiper.com/en/insights/publications/2025/08/faa-proposes-comprehensive-bvlos-uas-regulatory-framework>
- [S46] EASA, *Guidelines on the open and specific categories*, Issue 03. <https://www.easa.europa.eu/en/downloads/139435/en>; EASA, *PDRA-S01*. <https://www.easa.europa.eu/en/downloads/137221/en>; ASD News, *V-BAT achieves SORA SAIL III authorisation*, July 2026. <https://asdnews.com/news/defense/2026/07/21/vbat-achieves-sora-sail-iii-operational-authorization-completes-frontex-maritime-pilot-project-italy>
- [S47] EASA FAQ, *How does EASA treat my uncertificated ultralight/microlight aircraft?* <https://www.easa.europa.eu/en/faq/19385>
- [S48] 33 CFR 83.03 (Rule 3, definitions). <https://www.ecfr.gov/current/title-33/section-83.03>; 33 CFR 83.18 (Rule 18). <https://codes.findlaw.com/cfr/title-33-navigation-and-navigable-waters/cfr-sect-33-83-18/>; COLREG Rule 31. <https://cultofsea.com/colregs/part-c-lights-and-shapes-rules-20-31/rule-31-seaplanes>; 14 CFR 91.115. <https://www.ecfr.gov/current/title-14/section-91.115>
- [S49] AIN, *Regent submits seaglider approval plan to US Coast Guard*, 2025. <https://www.ainonline.com/aviation-news/futureflight/2025-03-21/regent-submits-seaglider-approval-plan-us-coast-guard>; gCaptain, *US Coast Guard approves seaglider testing in Rhode Island waters*. <https://gcaptain.com/u-s-coast-guard-approves-seaglider-testing-in-rhode-island-waters/>
- [S50] DroneLife, *LIFT Aircraft's HEXA capable of water takeoff and landing*. <https://dronelife.com/?p=95384>; Wikipedia, *Opener BlackFly*. <https://en.wikipedia.org/wiki/Opener_BlackFly>
- [S51] DroneLife, *First of its kind, fixed wing VTOL water landing drone* (VT-Naut). <https://dronelife.com/?p=99464>; DroneDJ, *Aeromapper Talon amphibious drone*. <https://dronedj.com/2018/10/19/aeromapper-talon-amphibious-drone/>; Shotkit, *Best waterproof drones* (SwellPro). <https://shotkit.com/best-waterproof-drone/>; DroneDJ, *HoverAir Aqua*. <https://dronedj.com/2025/08/05/hoverair-aqua-waterproof-drone-features/>
- [S52] US Patent 9,975,633, *Collapsible ducted fan unmanned aerial system*. <https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9975633>; Scientific American, *Pumped-up performance* (ILC Dover inflatable wings). <https://www.scientificamerican.com/article/pumped-up-performance/>; ASME, *Drone deploys in just minutes but flies for hours*. <https://www.asme.org/topics-resources/content/drone-deploys-just-minutes-but-flies-hours>
- [S53] DroneLife, *Skylift achieves UK aviation first with BVLOS drone operations in the Solent*, Jan 2026. <https://dronelife.com/2026/01/27/skylift-achieves-uk-aviation-first-with-bvlos-drone-operations-in-the-solent/>
- [S54] DroneXL, *Ocean County drone rescue in Surf City*, July 2026. <https://dronexl.co/2026/07/25/ocean-county-drone-surf-city-rescue/>
- [S55] SuperYacht Times, *Monaco Yacht Show Market Report 2025*. <https://issuu.com/superyachttimes/docs/monaco_yacht_show_market_report_2025>
- [S56] DroneXL, *Flyde drone deliveries to yachts on the French Riviera*, July 2026. <https://dronexl.co/2026/07/30/flyde-beluga-drone-delivery-yachts-french-riviera/>
- [S57] DroneDJ, *Monaco drone start-up delivers luxury goods to superyacht*, Oct 2023. <https://dronedj.com/2023/10/10/monaco-drone-startup-delivers-luxury-goods-to-super-yacht-partiers-then-admits-it/>
- [S58] Launch fares: Vineyard Haven, G and B Moorings and Launch. <https://marinas.com/view/marina/vgc57q_Vineyard_Haven_-_G_and_B_Moorings_and_Launch__Vineyard_Haven_MA_United_States>; Annapolis water taxi fares, 2026. <https://watermarkjourney.com/wp-content/uploads/2026/04/Water-Taxi-Map-and-Fare-2026-updated.pdf>; Port Jefferson Harborwalk (launch included in mooring fee). <https://dockwa.com/explore/destination/63c42en>
