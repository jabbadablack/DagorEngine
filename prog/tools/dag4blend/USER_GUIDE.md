# dag4blend 2.14 workflow guide

Install `dag4blend.zip` through Blender's **Edit > Preferences > Add-ons >
Install from Disk**, then enable **dag4blend**. Configure your project and asset
paths as described in the existing dag4blend documentation. The added tools live
in the **Dagor** sidebar of the 3D viewport. This build was tested on Blender
5.2.1 for Windows; the declared minimum remains Blender 4.5.

## Scene and asset export

- **Visible / Sel.Joined:** export one DAG. Select an optional **Export origin
  object** to use a shared asset origin.
- **Sel.Separated:** export each selected object around its own pivot. Select
  an Empty to export its supported descendants together, like a Max group.
  Filename prefixes/suffixes and matching `Cls_` collision objects are optional.
  For the Custom Groups Export naming convention, set the suffix to `.lod00`.
- **Col.Separated:** export leaf collections as DAGs. Select an asset's `.lods`
  collection to export its generated LOD collections. Hidden objects and
  collections are skipped unless **Include hidden** is enabled.
- **Col.Joined:** export one collection and its visible descendants together.
- **Legacy LOD Layers:** use collections named `LOD00`–`LOD15`,
  `DMG_LOD00`, `DMG2_LOD00`, `DESTR_LOD00`, `EXPL_LOD00`, `DESTR`, `DM`, or
  `XRAY`. Set the filename to `asset.lod00` to produce `asset.lod00.dag`,
  `asset_dmg.lod00.dag`, and the corresponding variations. Names are matched
  without regard to case. **Selected objects in legacy layers** limits output
  to selected objects within those collections.

The data-type switches control meshes, helpers/armatures, lights, splines,
camera helpers, and materials. Disabling materials writes placeholders.
Camera nodes retain transforms as helpers: DAG has no camera-object payload.
Geometry cleanup is disabled by default to retain imported vertices and faces.
Enable **Clean degenerate and loose geometry** when you explicitly want short
edges, degenerate faces and unused vertices removed from the export copy.
Point, Spot and Sun lights are supported. Max intensity maps numerically to
Blender energy; matching the numerical value does not establish identical
rendered brightness. Imported light values outside Blender's preview ranges
are retained for an unchanged round trip.

Bezier and Poly splines export directly. NURBS use Blender's evaluated
centerlines at their curve resolution and export as polylines. Bevel/extrusion
on the source remains unchanged. Export a converted mesh when the surface itself
is the desired asset.

Imports support related LOD/DP/DMG/destruction files and wildcard/regex batches.
Destruction variants use LOD00 independently of the selected ordinary LOD.
Wildcard filters accept filenames or extension-free asset names and only import
DAG files. Regex mode uses Python regular expressions.

## Skins and animation

1. Use unique object and bone names within an exported character.
2. Skin meshes with vertex groups and a linear Armature modifier. Disable
   Preserve Volume, bone envelopes and modifier vertex-group masks for DAG
   export. The exporter carries the required armature when only a skinned mesh
   is selected and writes rest geometry and normalized skin weights.
3. Export the static character as DAG. Imported supported skins become Blender
   armatures, vertex groups and Armature modifiers. Bone-parented attachments
   retain their parent bone and transform.
4. Export motion through **File > Export > Dagor Animation (.a2d)**. Choose the
   frame range and samples per frame. Constraints and pose bones are evaluated;
   timeline markers become animation labels. Increase sampling for fast motion
   or strongly curved interpolation between frames.
5. Enable key reduction and set position, rotation and scale tolerances as
   needed. Tolerances bound errors at sampled times. They do not replace adequate
   temporal sampling.
6. For origin-relative motion, choose the same origin object in DAG and A2D
   export. A2D then includes the native origin velocity channels. Enable **Loop
   origin velocity** when a looping clip needs matching initial/final linear
   velocity.

Leave **Cleanup Names** off for rig exports so animation and skeleton node names
agree. Zero-scale and sheared animation transforms are rejected. Native DAG
skins whose bone nodes contain renderable geometry retain that geometry as
bone-attached objects. Unweighted helper ancestors become bones, and original
affine bind matrices are preserved alongside Blender's editable rest bones.
Use the Bone Properties tab's Dagor panel to copy, paste, clear or edit bone
scripts through a Text Editor. Keep the stored bind metadata when editing an
imported rig; it adapts Blender's normalized rest transforms to the native binds.

## LODs, collisions and damage chunks

**Asset Authoring > Generate LODs and Collisions** creates an `.lods` group,
places the original in `.lod00`, and generates reduced meshes in `.lod01`, etc.
Source geometry/UVs are retained. Generated skinned LODs retain vertex groups and
their Armature modifier. The reduction uses Blender Decimate, so results differ
from Max's optimization algorithms.

Convex collision generation can keep/exclude comma-separated material names or
wildcards, cut at a local height, and apply typed collision properties. The
operation rolls back generated data if a batch fails.

**Damage Setup** creates parented collision bounds and assigns visible/collision
properties. Box, Sphere and Capsule use the public engine's primitive fitters.
Convex generates bounded hull geometry for a **collision** asset. The public
**physObj** exporter does not accept convex primitives, so the convex option
does not falsely label a physObj primitive as supported. Rotation limits, seed,
postfix, hull vertex limit, surface offset and property preservation are
configurable. Properties use ordinary typed BLK syntax, separated by semicolons.

## Vegetation normals and Pivot Painter

**Asset Authoring** provides normal transfer from the active source mesh,
puffiness, voxel volume normals and a thickened voxel polysurface alternative.
Set strength and a regular expression for materials whose normals should remain
unchanged. Generated normal volumes can be retained; they are hidden initially
and can be revealed in the Outliner for inspection.

**Pivot Painter** accepts an ordinary Blender hierarchy of Empty/mesh branches.
Local +Z is each branch's growth direction. The generator supports the shader's
four-level/2048-node limit and writes `pivot_pos.dds` and `pivot_dir.dds`, plus a
combined wind mesh. The default pivot UV channel is 4. Use a matching project
shader and assign the textures to slots 7 and 8. Export the wind mesh with
**Sel.Separated** to preserve its pivot convention. The extent limit is 20.48
local units, matching the bundled shader. GrowFX objects must first be converted
to a Blender branch hierarchy; direct GrowFX ingestion is not provided.

## AO, deformation colors and UVs

**Vertex AO** bakes deterministic hemisphere occlusion without a special render
engine or material. Choose sample count, occlusion distance, colors, gradient,
channel mask and optional scene occluders. The default writes engine map channel
8 and an `AO` preview color layer, preserving existing deformation/wind colors.
Choose **Vertex Colors** or **Engine Map and Vertex Colors** only when replacing
the first color layer is intended. **Fast User Properties > Show Vertex Colors**
displays the active preview layer.

**Asset Utilities > Vertex Position to Color:** select two meshes with matching
indexed topology and make the base active. The other mesh supplies the deformed
positions. The operation writes `DEFORM`, records `max_height`, and can configure
`dynamic_deformed` materials. The base must not contain other color attributes,
because the DAG exporter uses its first color layer for deformation data.

**UV Channels** provides copy, swap, move, delete and a cross-object copy buffer.
Buffer paste requires identical indexed topology and validates the full
selection before changing it. Channel numbers in these operators refer to
Blender's UV-layer order. A move removes the source, shifting later indices.

**Asset Utilities** also offers unwrap/repack with source/target channels,
marked seams, angle cuts, texel normalization and pixel gutter settings. Export
channel IDs follow canonical `UVMap`, `UVMap.001`, etc. Three-component engine
maps are retained as `dagor_map_N` vector attributes, including sparse channels
and AO colors.

## Decals, materials and object properties

**Decal Projector** clips projected triangles to a cursor-aligned volume. Enable
interactive placement in its dialog to place with LMB, scale with Shift + mouse
movement, rotate with Ctrl + movement, and finish with RMB/Esc. Existing rectangle
and convex JSON libraries use the documented MaxScript schema. Texture alpha is
connected in the generated standard material. Convert to a project Dagor shader
through the material conversion tool when preparing the asset for export.

**Asset Utilities** converts standard/Dagor materials by copying diffuse color
and a directly connected diffuse texture. Complex shader networks require manual
material setup, as with the documented Max conversion utility.

**Fast User Properties** offers copy/paste/clear, a viewport property overlay and
color/texture display controls. Typed scripts preserve case, spaces, quoted
strings and Dagor tilde escapes. Malformed legacy fields are retained in
`broken_properties:t` for review. Existing property presets and the full property
editor remain available.

**Fix Illegal Asset Names** can operate on selected objects, their collections
and materials. Configure illegal/replacement characters, Russian transliteration,
ASCII compatibility and lowercase conversion. Texture names/paths are reported
for review without renaming files on disk.

## Validation limits

See `PARITY.md` for verified coverage and outstanding comparisons. The A2D,
skeleton, physObj and convex collision fixtures compile through the repository's
actual Dagor exporters. Automated checks also cover package registration,
skin deformation after reimport, mapping, curves, AO and authoring workflows.
Interactive mouse placement and viewport overlays still need a manual GUI pass.
No side-by-side Max scene suite or full in-game playback certification has been
completed; this build should not be represented as proven complete Max parity.
