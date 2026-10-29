# 3ds Max parity status — dag4blend 2.14.0

The target includes core Dagor Max Tools, animation and the documented MaxScript
Toolbox. This build adds working Blender equivalents across those tool families.
It is **not yet certified as complete 3ds Max parity**. The table distinguishes
implemented behavior from remaining compatibility and workflow validation.

## Coverage

| Tool family | Implemented coverage | Evidence / remaining work |
| --- | --- | --- |
| Scene import | Related LOD/DP/DMG/destruction files, wildcard/regex batches, replacement collections, helpers/lights, skins, typed scripts, sparse/3D maps | Discovery tests; complete package DAG roundtrips. Native Max fixture comparisons remain. |
| Scene export | Per-type switches, hidden collection rules, joined/separate/collection modes, Empty groups, local pivots, named origins, material placeholders, normals, legacy variation collections, filename rules and matching colliders | Blender hierarchy and integration tests; actual engine skeleton compilation. Compare additional native Max scenes. |
| Lights | Point/Spot/Sun, legacy and extended packed layouts, scripts and children, preservation of source values clamped by Blender previews | Independent packed-format fixtures and DAG roundtrips. Numeric intensity does not establish renderer-equivalent lighting. |
| Splines | Bezier/Poly and Blender-evaluated NURBS centerlines, cyclic paths, scripts | Full add-on NURBS export/reimport and source-data preservation. Native curve approximation comparisons remain. |
| Skinning | Helper and mesh-bone imports, unweighted ancestors, preserved affine binds and bone scripts, normalized vertex-group weights, automatic skeleton inclusion and bone attachments | Roundtrip deformation with two weighted bones, nonuniform armature transforms and attachments; native-style mesh-bone fixture with nonuniform bind scale and evaluated posing. Production rest-scale/shear comparisons remain. |
| A2D animation | Evaluated object/pose-bone sampling, constraints, FPS/subframes, timeline labels, independent channel key reduction, shared motion origin, native velocity channels | Format/interpolation tests and compilation by the real A2D exporter. Full engine playback and Max clip comparisons remain. |
| Utility / materials | Existing material deduplication/optimization; diffuse standard/Dagor conversions; normal orientation and viewport texture controls | Full package material-conversion tests. Arbitrary shader network conversion is not provided. |
| UV utilities | Copy/swap/move/delete, topology-checked copy/paste buffer, sparse channel IDs and 3D maps | Actual Blender operator tests, atomic mismatch rejection and small/big mesh binary tests. |
| Unwrap Me workflow | Source/target channels, seam/angle cuts, normalized texel density, atlas packing and pixel gutters | Full package unwrap/repack tests. Blender algorithms differ from Max's unwrap engine. |
| AO baker | CPU hemisphere sampling, tints, channel masks, ground gradient, material exclusion, scene occluders, map-channel output and separate preview | Open/occluded surface tests, AO map-8 roundtrip and deformation-color preservation. Max's optional beautifier algorithm is not reproduced. |
| Custom groups export | Empty groups, local origins, filename prefix/suffix and matching collision objects | Export implementation present; broader group/preset comparison and interactive workflow checks remain. |
| Damage setup | Visible/collision property scripts, preservation, seeded rotation, postfix, box/sphere/capsule bounds, bounded convex geometry and offset | Real physObj and convex collision-resource builds pass. Public physObj supports three primitives; convex uses the collision-resource path. |
| LOD / collision generator | Hierarchical LOD collections, Decimate reductions, retained skin weights/armature modifiers, convex collisions, material filters and height cuts, rollback on batch failure | Actual Blender geometry/UV/skin tests. ProOptimizer/MultiRes-specific settings and topology equality are not reproduced. |
| Normal editing | Surface transfer, strength, puffiness, regex material exclusions, voxel volume and thickened polysurface alternatives, optional retained volumes | Geometry tests, exclusions and temporary-data cleanup. Exact native polysurface reconstruction differs. |
| Fast user properties | Typed property codec, text/preset editor, clipboard copy/paste/clear, selected-object display and viewport overlay | Codec tests and full package property roundtrip. Overlay needs manual GUI verification. |
| Illegal characters | Configurable characters/replacement, transliteration, case conversion, object/collection/material scopes and texture-path warnings | Naming checks; native Max transliteration/preset comparison remains. |
| Pivot Painter | Ordinary Blender branch hierarchy, four levels / 2048 nodes, combined wind mesh, UV lookup, half-float position DDS and direction DDS | DDS headers/values, parent indices, coordinates and UV addressing checked against bundled shader conventions. Direct GrowFX ingestion, automatic project-specific shader setup and in-game wind validation remain. |
| Vertex position to color | Matching-topology two-mesh deformation, source-space encoding, `DEFORM`, multiplier and optional shader setup; existing shape-key workflow | Full package color/multiplier tests. Native effect comparison remains. |
| Decal projector | Clipped rectangle/convex projection, JSON atlas libraries, UVs/normals/alpha, cursor and interactive placement with scale/rotation controls | Projection geometry and operator registration tests. Interactive placement and a visual bitmap-library editor remain to validate/implement. |
| Composite editor | Existing composite placement/import/export, random entities and node properties | Existing coverage retained; complete MaxScript CMP behavioral comparison remains. |

## Validation performed

Test platform: **Blender 5.2.1 LTS, Windows**. Blender 4.5 remains the declared
minimum but was not available for this validation pass.

The scripts in `tests/` exercise real Blender data and operators. Key checks:

- Complete recursive installation archive, dependency bundling, enable/disable.
- Optional sample-content regression suite imports and re-exports Sponza,
  a sample tree, Outer Space station geometry, a tree collider and a rock.
  It compares mesh/vertex/triangle counts, world bounds and shader class names.
  These assets are native DAG fixtures; their exact authoring application is
  not established. Texture rendering is not checked by these geometry tests.
- DAG helper hierarchy and transform serialization; failure propagation.
- Two-bone skin and attachment roundtrip, with evaluated deformation comparison.
- Mesh-bone geometry, unweighted ancestors, affine bind adapters and bone scripts.
- Skinned LOD generation without posing/baking away its armature binding.
- Light layout fixtures, legacy records and clamped preview-value retention.
- A2D pools, polynomial/quaternion interpolation, native signed scales, sampling,
  markers, key reduction, origin-relative transforms and velocity channels.
- Sparse UV and three-component mapping with both small/big mesh index widths.
- AO preservation of deformation colors; three-component map-8 export/reimport.
- NURBS evaluation with bevel retained on the original source object.
- Legacy variation naming, hidden layer behavior and joined collection paths.
- LOD/collision geometry, height cuts, normal transfer, masks and volume cleanup.
- Material conversion, deformation colors, atlas unwrap/pack, decal clipping,
  Pivot Painter DDS content and lookup conventions.
- Typed property quoting, case, whitespace, escapes, vectors and matrices;
  import pattern escaping and destruction-LOD rules.

The repository's **actual daBuild exporters** successfully compile generated
fixtures for **A2D animation, skeleton, physObj and convex collision**. This checks
format consumption and asset compilation, not visual playback equivalence.

Local sample content was found under `samples/` and `outerSpace/develop/assets/`
(283 DAG files in this checkout; ignored files require an inclusive search).
Outer Space's shader sources are in `outerSpace/prog/shaders/`, with compiled
tool shaders in `outerSpace/tools/`. No A2D sources were found in either sample
tree, so animation comparisons still use generated fixtures and the native
compiler rather than recorded sample animation clips.

## Remaining acceptance work

1. Run a native Max/Blender fixture suite covering production characters,
   lights, materials, damage assets, LODs and composites.
2. Validate complete animated character and Pivot Painter playback in a game.
3. Perform GUI checks for modal decal placement, overlays, dialogs and previews.
4. Compare additional native rest-scale/shear cases against production Max files.
5. Compare advanced Max-specific optimization, beautifier and procedural settings;
   add a visual bitmap-library editor if that exact authoring interaction is needed.
6. Validate Blender 4.5 and other supported host platforms.

`USER_GUIDE.md` describes the implemented Blender workflows and their limits.
The installable build uses the standard `dag4blend.zip` filename and the original
`dag4blend/` archive root.
