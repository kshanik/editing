import bpy
from .start_end import final
from .start_end import clear
from .start_end import clear_all

from bpy.props import (StringProperty,
                       PointerProperty,
                       )
from bpy.types import (Panel,
                       PropertyGroup,
                       )
                       
class RBClearOperator(bpy.types.Operator):
    bl_idname = "wm.clear"
    bl_label = "clear"
    def execute(self, context):
        clear()
        return {'FINISHED'}

class RBFinalOperator(bpy.types.Operator):
    bl_idname = "wm.final"
    bl_label = "final"
    def execute(self, context):
        final(bpy.context.scene.ritebite.excel, bpy.context.scene.ritebite.sheet)
        return {'FINISHED'}

class RBClearAllOperator(bpy.types.Operator):
    bl_idname = "wm.clearall"
    bl_label = "clearall"
    def execute(self, context):
        clear_all(bpy.context.scene.ritebite.excel, bpy.context.scene.ritebite.sheet)
        return {'FINISHED'}

class RiteBiteProperties(PropertyGroup):

    excel: StringProperty(
        name="Excel",
        description=":",
        default="ssss",
        maxlen=1024,
        )

    sheet: StringProperty(
        name="Sheet",
        description=":",
        default="sss",
        maxlen=1024,
        )


class VIEW3D_PT_my_custom_panel(bpy.types.Panel):  # class naming convention ‘CATEGORY_PT_name’

    # where to add the panel in the UI
    bl_space_type = "SEQUENCE_EDITOR"  # 3D Viewport area (find list of values here https://docs.blender.org/api/current/bpy_types_enum_items/space_type_items.html#rna-enum-space-type-items)
    bl_region_type = "UI"  # Sidebar region (find list of values here https://docs.blender.org/api/current/bpy_types_enum_items/region_type_items.html#rna-enum-region-type-items)

    bl_category = "RiteBite"  # found in the Sidebar
    bl_label = "RiteBite"  # found at the top of the Panel

    def draw(self, context):
        """define the layout of the panel"""
        scene = context.scene
        ritebite = scene.ritebite
        row = self.layout.row()
        row.prop(ritebite, "excel")
        row = self.layout.row()
        row.prop(ritebite, "sheet")

        row = self.layout.row()
        row.operator(RBFinalOperator.bl_idname, text="Create")

        layout = self.layout
        layout.row().separator()

        row = self.layout.row()
        row.operator(RBClearOperator.bl_idname, text="Clear")
        row = self.layout.row()
        row.operator(RBClearAllOperator.bl_idname, text="Clear All")

def register():
    bpy.utils.register_class(RBClearOperator)
    bpy.utils.register_class(RBClearAllOperator)
    bpy.utils.register_class(RBFinalOperator)
    bpy.utils.register_class(RiteBiteProperties)
    bpy.utils.register_class(VIEW3D_PT_my_custom_panel)
    bpy.types.Scene.ritebite = PointerProperty(type=RiteBiteProperties)

def unregister():
    bpy.utils.unregister_class(RBClearOperator)
    bpy.utils.unregister_class(RBClearAllOperator)
    bpy.utils.unregister_class(RBFinalOperator)
    bpy.utils.unregister_class(RiteBiteProperties)
    bpy.utils.unregister_class(VIEW3D_PT_my_custom_panel)
    del bpy.types.Scene.ritebite

if __name__ == "__main__":
    register()
