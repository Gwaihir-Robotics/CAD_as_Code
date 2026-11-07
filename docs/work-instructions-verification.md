# Illustrated work-instruction pilot verification

2026-11-06. Software/illustration verification only; no physical manufacturing
validation or release. Current draft artifact: fly `output/work-instructions/two-station-8110/r006/`.

## Scope and evidence

Reusable implementation: JSON Schema v1; read-only FreeCAD adapter; SVG/HTML/PDF
compiler; source fingerprints and immutable revisions; impact propagation; local
SQLite event outbox/mock receiver; explicit offline verifier. Consumer definitions
and rebuild commands: `stator-winder/fly/docs/work-instructions-pilot.md`.
Architecture: `docs/decisions/0001-illustrated-work-instructions.md`.
Skill workflow: `reference/work-instructions.md` (linked from SKILL.md).

Pilot covers 21 frame pieces, 14 identified tubes, 28 candidate tube-joint
interfaces, a true mid-post CAD section, one fly-drive subassembly and its
second-station reuse. There are 50 leaf/context instance IDs, 10 ordered
operations and three independently assignable work packages. CAD is opened
read-only and content hashes before/after extraction agree. The authoritative
assembly placements are never saved or modified.

## Automated checks

`python -m unittest discover -s tests -v`: **35 tests passed**, including missing
and duplicate IDs; missing references; dependency cycles/order; BOM quantities;
installation double-counting; missing hardware placements/specification; hardware
role/diameter/length and allocation against source; stale source hashes;
instance/geometry/datum/process impact and downstream invalidation; mandatory
holds blocking release; immutable revision refusal; event duplicate delivery,
conflicting UUID rejection, acknowledgments and retry retention; append-only
corrections; wrong instruction/part identity; rejection of implicit acceptance
on completion and acceptance against unapproved requirements.

`git diff --check` and Python compilation passed. The explicit browser verifier
loads the package via file:// with Chromium offline. It checks all operation and
BOM anchors, all images, image enlargement, browser errors and network requests,
then validates artifact hashes and PDF operation/figure references and page sizes.
Machine-readable results are in the consumer's `output/work-instructions/qa/`.

Historical r001 offline test: PASS, zero external requests, zero browser errors,
10 operations, 26 Letter pages. Print review found a trailing blank page in r001;
that artifact remains intact for the pinned sample build. r003 corrects print
pagination and adds hardware close-ups. Final r003 results accompany this report
in the consumer QA directory.

## Visual review

Rasterized every r001 page into a contact sheet and inspected enlarged cover,
M6 mounting page and servo page. This caught sheet occlusion, crowded leader
lines and a trailing blank page. The final draft uses the accessible camera side,
a front-mount-hidden M6 close-up, sorted callout positions, separate joint
leaders and servo-hidden M4 detail views. True section contours come from
FreeCAD slice operations rather than inferred rectangular envelopes. Final
r003 pages are inspected again after regeneration; QA PNGs are retained locally.

## Revision/feedback evidence

The simulated fit problem references `s1.hrp85`, `s1.P010`, work order DEMO-WO-001
and build DEMO-FLY-001 pinned to the r001 instruction digest. Engineering
assessment and rework request remain append-only events. A rejected inspection
and a completed operation coexist in the build summary, proving their separation.
r002 adds a fit-measurement instruction/check; affected steps are s1.P010,
s1.P020 and s1.P030. A revision-issued event references r002; original build
records are not replaced. r003 separately adds visual details. No simulated
measurement is represented as a real physical finding.

## Holds and practical limits

All pilot packages remain draft. Welding requirements, qualified sequence,
clamping, dimensional acceptance, torque/fit and received servo hardware need
engineering input. M6 cylinder axes match CAD; this verifies location only.
M4 placements are explicitly incomplete. Hardware graphics are nominal
specification envelopes without thread/socket detail. The pilot excludes the
known conflicting output-tube M5 pattern and the rest of the winding machine.

The 8110 S81/L10 study is not the paid S60/L20 structure baseline. Received blanks
still need secondary machining despite finished CAD features. Three upstream
current-worktree input hashes differ from the historical CAD manifest; see
`qa/upstream-lineage-audit.json`. This is not a claim that historical CAD was
rebuilt from those changed sources. Each package pins actual geometry and current
source bytes separately, and compatibility remains a release hold.

SVG uses depth-sorted CAD mesh triangles, not exact occlusion solving. Dedicated
cameras/details are required for ambiguous overlaps. Current hardware placement
adapter is scoped to the pilot's +X insertion axes. PDFs/SVGs are relatively
large because they preserve vector mesh geometry. The local mock is not a MES,
authenticated release system or full work-order state machine. Network delivery,
retry scheduling/backoff, real FactoryOS mapping and operational backup policy
remain future work. No motion or safety-control integration is included.

Final r004 also retains parent operation callout numbering in servo-hidden detail
views; the regression test checks the rendered numeric callouts against their
parent instance order. Earlier revisions and the original build stay intact.

## Final r004 result

PASS: 10 operations, 27 Letter pages, all 38 manifest artifact hashes verified,
zero network requests and zero browser errors in explicit file:// offline mode.
The unchanged-input compiler invocation returned the existing r004 directory;
no existing revision was replaced. A fresh FreeCAD extraction reproduced the
cached geometry byte-for-byte (SHA-256
`80787f6364f6fff6ef9edff9c0de9ff0179cfdd81f16f7bc0ac436278eaeca2b`).
Inspected the final servo detail and last PDF page: callout numbers match the
parent key, hardware is visible, text remains within the page, and there is no
trailing blank page. The r003 all-page contact sheet covers the otherwise
unchanged page layout; r004 changes detail numbering and captions only.

## r005 contrast refinement

User review found that the context models were too pale. Compiler 0.2.0 uses
medium-grey context, directional face shading and thin mesh-derived feature and
silhouette outlines, shared by offline SVG/HTML and the PDF. Blue current parts
and amber hardware remain distinct. Closed-solid tessellation seams are omitted;
feature edges are depth sorted with their owning surfaces. This is still an
approximate mesh projection, not exact hidden-line CAD rendering.

28 unit checks pass, including two added geometric drawing checks: adjacent
coplanar faces with duplicate tessellation vertices do not expose their shared
diagonal, and perpendicular faces retain their common feature edge once.
Model contrast was measured at corresponding grey-context pixel positions in
the old and revised HRP85 illustration; the new median contrast against white
exceeds the prior value by at least 50%. See the consumer QA directory
`output/work-instructions/qa/r005/contrast-measurement.json` and comparison PNGs.

The authored r005 process differs from r004 only in instruction revision.
Geometry, placements, operations and requirements are unchanged. All operations
are marked for visual review because the compiler changed. r004 and the earlier
instruction packages/build records are preserved.


r005 final verification: PASS, 27 Letter pages, all 38 manifest artifact hashes
verified, zero network requests and zero browser errors in offline file:// mode.
Inspected the cover, exploded M6 mounting step and M4 detail in the rendered PDF,
plus the M6 step in greyscale. Shading, holes, hardware, leaders and text remain
readable at print scale. Unchanged-input regeneration reused r005. Every artifact
hash in r001 through r004 still matches its original manifest.


## r006: common-part callouts and dogbone connection details

Common part numbers share a bubble number with individual location suffixes:
`2a–2d` map to four distinct M6 x 20 installation instances. The callout key shows
quantity four; the full BOM still counts eight such screws across both stations.
M4 screws and washers form different groups. Grouping is by exact part ID, so
another screw length is not merged. Suffixes follow authored instance order,
independent of camera/leader placement. Detail views retain parent labels, and
second-station reuse preserves its own installed IDs. `callouts.json` exports
the same grouped labels, quantities and instance mappings as HTML/PDF.

Seven additional checks bring the total to 35: common screw grouping and unique
instances; different lengths staying separate; parent/detail label consistency;
second-station identity; suffixes past z; review invalidation without changing
BOM accounting; and stale cropped detail cache rejection.

F020 adds three actual CAD close-ups: the J03 receiving slots before post
installation, the J01 lower-ring corner pulled apart, and the J11 lower spanner
pulled apart. The adapter clips copied solids to authored world-space boxes and
tessellates at 0.05 mm deflection. The dogbone reliefs were inspected in enlarged
renders. The R1 note comes from the pinned frame config; no weld requirement is
inferred. Crop boundaries are presentation aids, not additional fabrication cuts.

The base instance geometry records compare equal to r005, and the source FCStd
hash remains unchanged before/after extraction. All new graphics retain the
existing high-contrast style. Manufacturing holds and build-execution identities
are unchanged. The new instruction revision requires visual review.

r006 final result: PASS. The 30-page Letter PDF and offline file:// HTML verify
all 42 artifact hashes with zero external requests or browser errors. The verifier
checks every grouped quantity in HTML, every rendered bubble label in primary
and detail SVGs, the exported callout registry, and the matching PDF location
ranges. All 35 unit checks pass. All 30 PDF pages were rasterized into a contact
sheet; enlarged receiver/corner dogbone, M6 mounting and grouped callout-key
pages were inspected. No blank tail page or clipped key was found. The old
r001–r005 artifact hashes remain intact, and unchanged-input regeneration reused
r006 without replacing an existing revision.


## Publication and lightweight sharing

The separate sharing exporter retains instruction/figure text and rasterizes
only figure graphics at approximately 220 dpi. Its output is outside the pinned
package and has a derivative manifest recording source/output hashes. The real
r006 export is 1,656,733 bytes, has the same 30 pages and identical extracted text.
Enlarged mounting and dogbone print pages were inspected. Three exporter guard
checks bring the suite to 38: immutable-package protection, existing-output
protection and rejection of a PDF that does not match its source manifest.

The blog uses four responsive WebP screenshots with explicit dimensions, lazy
loading and asynchronous decoding. The large-image set totals 76,652 bytes;
the mobile set totals 36,384 bytes. Desktop and 390 px mobile rendering were
checked for image loading, selected source size, horizontal overflow and browser
errors. The PDF is not embedded or automatically downloaded by the article.
