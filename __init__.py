bl_info = {
    "name": "RiteBite",
    "author": "Manish Sharma",
    "version": (0, 0, 1),
    "blender": (3, 5, 0),
    "location": "VSE > Sidebar > RiteBite",
    "description": "Rite Bite tools for custom video editing",
    "category": "Development",
}

import bpy


# IMPORT SPECIFICS
##################################

from . import   (
    ritebite,
    cut,
    start_end
)


# register
##################################


def register():
    ritebite.register()

def unregister():
    ritebite.unregister()
