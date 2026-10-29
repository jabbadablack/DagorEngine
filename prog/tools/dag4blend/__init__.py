import bpy

from .                  import settings
from .                  import animation
from .popup             import popup_operators
from .projects          import project_manager_panel
from .exporter          import exporter
from .exporter          import export_panel
from .tools             import tools_panel, bake_panel, mesh_tools_panel, uv_tools, authoring, asset_utilities
from .tools             import decal_projector, pivot_painter, ao_baker, damage_tools
from .object_properties import object_properties
from .object_properties import viewport, bone_properties
from .dagormat          import dagormat_operators, dagormat
from .colprops          import colprops
from .importer          import importer
from .importer          import import_panel

from .cmp               import cmp_panels,cmp_import,cmp_export, node_properties
from .smooth_groups     import smooth_groups

modules=[settings,
        animation,
        popup_operators,
        project_manager_panel,
        smooth_groups,
        exporter,
        object_properties,
        viewport,
        bone_properties,
        export_panel,
        tools_panel,
        bake_panel,
        mesh_tools_panel,
        uv_tools,
        authoring,
        asset_utilities,
        decal_projector,
        pivot_painter,
        ao_baker,
        damage_tools,
        dagormat_operators,
        dagormat,
        node_properties,
        cmp_import,
        cmp_export,
        cmp_panels,
        colprops,
        importer,
        import_panel]

bl_info = {"name": "dag4blend",
           "description": "Tools for editing dag files",
           "author": "Gaijin Entertainment",
           "version": (2, 14, 0),#2026.10.29
           "blender": (4, 5, 0),
           "location": "File > Export",
           "wiki_url": "",
           "tracker_url": "",
           "category": "Import-Export"}

def register():
    for module in modules:
        module.register()
    return

def unregister():
    for module in modules[::-1]:
        module.unregister()
    return


if __name__ == "__main__":
    register()
