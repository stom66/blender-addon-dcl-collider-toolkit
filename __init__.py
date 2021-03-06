# Blender Add-on Template
# Contributor(s): Aaron Powell (aaron@lunadigital.tv)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


bl_info = {
        "name"       : "DCL Collider Toolkit",
        "description": "Simple panel to assist creation and management of colliders for use in Decentraland",
        "author"     : "stom66",
        "version"    : (1, 0, 6),
        "blender"    : (3, 0, 0),
        "location"   : "View3D > Tools ",  
        "warning"    : "", # used for warning icon and text in add-ons panel
        "wiki_url"   : "https://github.com/stom66/blender-addon-dcl-collider-toolkit",
        #"tracker_url": "http://my.bugtracker.url",
        "support"    : "COMMUNITY",
        "category"   : "Scene"
        }

import bpy
from collections import defaultdict


class mainTask(bpy.types.Operator):
    """Removes all objects in the _colliders collection """
    bl_idname  = "collection.main_task"
    bl_label   = "DCT: Create Colliders"
    bl_options = { 'REGISTER', 'UNDO'}



    s_objSource: bpy.props.EnumProperty(
        name        = "Object source",
        description = "Which source to use to create colliders, sledted objects, or a collection",
        items       = [
            ("col", "Collection", "Use a named collection"),
            ("sel", "Selected objects", "Use the current object selection")
        ],
        default     = "col"
    )

    s_colSource: bpy.props.StringProperty(
        name        = "Source collection ",
        description = "The collection to be cloned as colliders",
        maxlen      = 128,
        default     = "_model"
    )





    s_moveCollider: bpy.props.BoolProperty(
        name        = "Move to collection", 
        description = "Should the new colliders be moved to the destination collections",
        default     = True)


    s_colDest: bpy.props.StringProperty(
        name        = "Destination collection name",
        description = "The name of the target collection to hold the colliders",
        maxlen      = 128,
        default     = "_colliders"
    )
    
    s_removeExisting: bpy.props.BoolProperty(
        name        = "Clear destination", 
        description = "Removes all existing objects from the destination collection",
        default     = True)





    s_suffix: bpy.props.StringProperty(
        name        = "Collider suffix",
        description = "The suffix to be appended to the newly cloned colliders, should be _collider for DCL",
        maxlen      = 128,
        default     = "_collider"
    )



    s_removeMaterials: bpy.props.BoolProperty(
        name        = "Remove materials", 
        description = "Removes all materials from the new colliders",
        default     = True)

    s_removeBevels: bpy.props.BoolProperty(
        name        = "Remove bevels", 
        description = "Removes any bevel modifiers from generated colliders",
        default     = True)

    s_addTriangulate: bpy.props.BoolProperty(
        name        = "Add triangulate", 
        description = "Adds a triangulate modifier to the new colliders",
        default     = True)  

    s_showBounds: bpy.props.BoolProperty(
        name        = "Show bounds", 
        description = "Enables the bounding box for all colliders",
        default     = True)  

    s_showWireframe: bpy.props.BoolProperty(
        name        = "Show wireframe", 
        description = "Changes the display type of colldiers to wireframe",
        default     = True)  

    def execute(self, context):
        scene = context.scene        

        # Deselect all the objects
        # bpy.ops.object.select_all(action='DESELECT')

        # Check for the source collection
        if self.s_objSource == "col":
            if not doesCollectionExist(self.s_colSource):
                self.report({"WARNING"}, self.s_colSource + " collection does not exist")
                return {'FINISHED'}    

            # Check for the destination collection
            if not doesCollectionExist(self.s_colDest):
                self.report({"WARNING"}, self.s_colDest + " collection does not exist")
                return {'FINISHED'}
        
        # Define the objects to be copied - from collection, or selection
        if self.s_objSource == "col":
            objects = bpy.data.collections[self.s_colSource].all_objects
        elif self.s_objSource == "sel":
            objects = bpy.context.selected_objects
        else:  
            self.report({"WARNING"}, "Internal error: s_objSource does not match")
            return {'FINISHED'}
        
        if self.s_moveCollider:
            # Remove all objects in the destination collection
            if self.s_removeExisting:
                for obj in bpy.data.collections[self.s_colDest].all_objects:
                    bpy.data.objects.remove(obj)

        # Define a blank set for the duplicated objects
        new_objects = set()

        # Loop though all the objects in col_source
        for obj in objects:

            # Skip unsuitable objects
            if obj.type != 'MESH' and obj.type != 'CURVE' and obj.type != 'FONT':
                continue

            # Copy the object
            new_obj = obj.copy()
            new_obj.data = obj.data.copy()
            #new_obj.animation_data_clear()

            # Add the new object to the set of new objects
            new_objects.add(new_obj)

            # Move the new object to the col_dest collection
            if self.s_moveCollider:
                bpy.data.collections[self.s_colDest].objects.link(new_obj)
            else:
                bpy.data.collections[obj.users_collection[0].name].objects.link(new_obj)

            #Show the bounding box
            if self.s_showBounds:
                new_obj.show_bounds = True

            #Enable wireframe
            if self.s_showWireframe:
                new_obj.display_type = 'WIRE'

            # Remove any materials
            if self.s_removeMaterials:
                new_obj.data.materials.clear()

            # Remove any unsuitable modifiers
            if self.s_removeBevels:
                if new_obj.modifiers.get("Bevel"):
                    new_obj.modifiers.remove(new_obj.modifiers.get("Bevel"))

            # Add a triangulate modifier
            if self.s_addTriangulate:
                addTriangulateModifier(new_obj)


        # Loop through the list of new objects and rename them
        # We can't rename them in the main loop due to edge cases where non-consecutive numbering
        # can result in the new object name being used
        
        for new_obj in new_objects:
            # Append the object name with name_suffix
            new_obj.name = new_obj.name + self.s_suffix
            
        return {'FINISHED'}


def doesCollectionExist(name):
    # Check that the specified collection exists
    coll = bpy.data.collections.get(name)
    if not coll:
        print("ERROR: Couldn't find a collection named " + name)
    return coll


def addTriangulateModifier(obj):
    modif_types = [ modifier.type for modifier in obj.modifiers ]
    if 'TRIANGULATE' not in modif_types:
        tri = obj.modifiers.new('Triangulate', 'TRIANGULATE')
        tri.keep_custom_normals = True

def menu_func(self, context):
    self.layout.operator(mainTask.bl_idname)


def register():
    bpy.utils.register_class(mainTask)
    bpy.types.VIEW3D_MT_object.append(menu_func)  # Adds the new operator to an existing menu.

def unregister():
    bpy.utils.unregister_class(mainTask)


# This allows you to run the script directly from Blender's Text editor
# to test the add-on without having to install it.
if __name__ == "__main__":
    register()
