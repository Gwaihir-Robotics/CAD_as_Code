# Industrial machine electrical visualization

Use this mode for a machine's power distribution, controller, drives, field I/O,
sensors, pneumatic controls and utility interfaces. It complements the mechanical
CAD/config workflow. It is not a PCB, circuit simulation or general electronics
design workflow. A 2D electrical review does not require running FreeCAD or
applying solid-geometry acceptance checks.

## Orient and establish the scope

Inspect the project's machine configuration, electrical references, BOM and
existing diagrams before choosing a layout. Extend the existing review and
preserve its schematics unless the user requests replacement. Define which
machine variant and subsystems are included; exclude adjacent equipment only
when the project's scope does so.

Use the actual machine architecture. Do not assume a particular PLC, computer,
fieldbus, drive brand, supply voltage, axis count or safety system. Distinguish
installed equipment, purchased-but-unverified equipment, proposed selections
and future allowances. Unknown vendor models, ratings and terminals remain
unknown. Read manufacturer documentation when the requested view depends on
specific electrical interfaces.

## Config, topology and identity

Keep component selections in the project's existing BOM/config. If a separate
visualization config is useful, reference those selections by stable tag instead
of copying vendor and procurement data. Store layout coordinates separately
from electrical relationships so rearranging a picture cannot rewire the model.

A useful model includes:

- Components: stable tag, function, quantity/instance, machine variant, device
  class, selected vendor model where known, evidence source and selection status.
- Interfaces: named functional ports; terminal/pin identifiers only when verified.
- Connections: source and destination component/port, circuit or function,
  connection layer and confirmed/provisional status.
- Presentation: component positions, optional enclosure/station grouping,
  wire routes, label positions, colors and legend.

Use the same tags in SVG groups, schematics, BOM links and component details.
Generate repeated drives, motors or station devices from machine quantities.
Draw multiple views from shared relationships rather than maintaining a second
hand-coded electrical topology in each view. Use the project's normal manifest
convention to record source revision/config hashes and unresolved interfaces.

## SVG and offline HTML

Generate a standalone SVG and an offline HTML review with the SVG embedded.
Keep the generator and config as the editable sources. Use the project's existing
artifact folders; do not impose the mechanical CAD output tree on its docs.

Use named component groups and separate connection-layer groups, for example
`data-component` and `data-layer`. Draw recognizable, simplified device faces
when useful: controller, terminal stack, disconnect, contactor, supply, drive,
motor or sensor. Keep actual device tags and readable port labels visible.
Illustrations are not dimensioned vendor geometry; label that distinction.
Do not use an invented terminal arrangement as a construction drawing.

Choose layers that match the machine. Typical categories include mains/feeder
power, motor power, DC control supply, protective earth, fieldbus/network,
feedback/encoders, ordinary sensor/actuator I/O and hardwired stop controls.
Separate additional heater/process-power or pneumatic connections when present.
These are optional categories, not a requirement to draw nonexistent circuits.

Layer switches hide connections while leaving components visible. Use labeled,
keyboard-accessible controls, retain selections across view changes, and avoid
relying only on color: add line styles, names and a legend. Keep existing
schematic tabs and any current training views. Avoid runtime CDN dependencies.
Make the all-layer standalone SVG useful without JavaScript; declare whether
printing the HTML uses the current layer selection or all connections.

Route connections through readable gaps, not device labels. Clearly distinguish
wire crossings from junctions. Show functional endpoints even in an illustrative
view. Define when a single line represents multiple conductors. Group physical
cabinet and field locations without implying that pictorial distances determine
cable lengths, conductor sizes or service clearances.

## Electrical meaning and limits

Keep these distinctions explicit where relevant:

- Contactor coil/control voltage versus the voltage switched by its power poles;
  series contactors versus parallel load branches.
- Control supply versus servo/VFD/heater power; a controller's own supply versus
  field sensor/valve voltage.
- Motor power versus encoder feedback; drive braking resistors versus mechanical
  holding brakes and STO.
- A fieldbus chain versus an ordinary switched LAN or an I/O terminal backplane.
- Ordinary I/O/enable commands versus verified safety functions and feedback.
- NPN/PNP sensor/common arrangements and independently controlled pneumatic
  actions; show exact harness connections only when supported by documentation.

Keep protective bonding explicit and independent of switching devices. Do not
silently invent resistor values, protection ratings, coil suppression, cable
ratings, terminal assignments, interlocks or a safety category. Explain pending
interfaces in the review and retain prototype/production distinctions in the
BOM. A component illustration or plausible topology does not establish a
released wiring design, panel rating or safe stop behavior.

## Verification

Verify the claims the artifact makes:

1. Unique component tags and valid connection endpoints; no orphan links or
   duplicate identities. Match variant quantities and repeated instances to the
   source config/BOM.
2. Consistent topology across component and schematic views. Check explicit
   series/parallel relationships, controller/network direction and supply domains
   where those relationships are asserted. Record unknowns instead of fabricating
   a passing result.
3. SVG parses, text/IDs are escaped, groups and export links resolve, and a
   rebuild reproduces the intended output from the recorded inputs.
4. In a browser, exercise each layer independently: only its connections hide,
   components remain visible, choices survive switching tabs, and existing views
   still work. Confirm the page works without external runtime requests.
5. Render and inspect label legibility, endpoint attachment, junction ambiguity,
   clipping and routing in both the full view and useful filtered combinations.
   When preserving existing artifacts, compare them before and after rebuilding.

Report what was checked and the remaining electrical unknowns. Do not equate a
successful SVG/browser check with engineering approval to wire the machine.

## Shared-skill boundary

Keep machine-specific code, dimensions, diagrams, BOMs, supplier selections and
procurement records in their project. Do not copy proprietary project artifacts
into this shared skill as examples or templates. Supporting examples, if ever
needed, must be independently authored, generic and explicitly non-project data.
