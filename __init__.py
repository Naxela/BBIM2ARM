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
    "name" : "BIM2ARM",
    "author" : "Alexander Kleemann",    
    "description" : "BIM to Armory",
    "blender" : (2, 93, 0),
    "version" : (1, 0, 0),
    "location" : "View3D > Sidebar",
    "warning" : "",
    "support": "COMMUNITY",
    "category" : "3D View",
    "doc_url": "",
}

import bpy, blenderbim, ifcopenshell, os, csv, json, sys, importlib, shutil
import blenderbim.bim.module.root.prop as root_prop
from bpy.types import Panel
from blenderbim.bim.ifc import IfcStore
from blenderbim.bim.module.root.data import IfcClassData
import blenderbim.tool as tool

from mathutils import Euler

from bpy.utils import ( register_class, unregister_class )
from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    EnumProperty,
    PointerProperty,
)
from bpy.types import (
    Panel,
    AddonPreferences,
    Operator,
    PropertyGroup,
)

#Todo
ifc_loaded = False
ifc_configured = False
storeys = []
deployed = False

def getProjectFolder():

    if bpy.data.is_saved:

        return bpy.path.abspath("//")

    else:

        return

def getAddonFolder():

    context = bpy.context

    for mod_name in context.preferences.addons.keys():
        if mod_name == "bim2arm":
            mod = sys.modules[mod_name]
            file = mod.__file__
            path = os.path.dirname(os.path.realpath(file))
            return path

def getProperty(obj):
    
    IfcStore.get_file()
    
    if not IfcClassData.is_loaded:
        IfcClassData.load()
        
    element = tool.Ifc.get_entity(obj) #Product
    
    return(ifcopenshell.util.element.get_psets(element))

def getType():
    for obj in bpy.context.selected_objects:
        
        bpy.context.view_layer.objects.active = obj
        
        IfcStore.get_file()
        
        if not IfcClassData.is_loaded:
            IfcClassData.load()
            
        element = tool.Ifc.get_entity(obj) #Product
        
        print(element.is_a())

def getObjElement(obj):

    bpy.context.view_layer.objects.active = obj

    IfcStore.get_file()

    if not IfcClassData.is_loaded:
        IfcClassData.load()

    element = tool.Ifc.get_entity(obj)

    return element

def exposeProperties(obj):
    bpy.context.view_layer.objects.active = obj
    
    #If...blenderbim?
    
    print(obj.name)
    #print(bpy.context.active_object.BIMObjectProperties.ifc_definition_id)
    
    propsets = {}
    
    if not bpy.context.active_object:
        print("Failure 1")
        return False
    props = bpy.context.active_object.BIMObjectProperties
    #print(props.ifc_definition_id)
    
    if not props.ifc_definition_id:
        print("Failure 2")
        return False
    if not blenderbim.bim.ifc.IfcStore.get_element(props.ifc_definition_id):
        print("Failure 3")
        return False
    
    #return True
    blenderbim.bim.ifc.IfcStore.get_file()
    
    if not ifcopenshell.api.layer.data.Data.is_loaded:
        ifcopenshell.api.layer.data.Data.load(blenderbim.bim.ifc.IfcStore.get_file())
    
    #Ensure loaded attribute data
    blenderbim.bim.module.attribute.data.AttributesData.load()
        
    #Ensure loaded property set data
    blenderbim.bim.module.pset.data.ObjectPsetsData.load()
        
    #Ensure loaded quantity set data
    blenderbim.bim.module.pset.data.ObjectQtosData.load()
        
    #IFC Attributes
    for attribute in blenderbim.bim.module.attribute.data.AttributesData.data["attributes"]:
        if attribute:
            propsets[attribute["name"]] = attribute["value"]
        
    #IFC Layer !!OBS IF THERE IS NO LAYERS PRESENT???
    if obj.data.BIMMeshProperties.ifc_definition_id in ifcopenshell.api.layer.data.Data.items:
        layer_id = ifcopenshell.api.layer.data.Data.items[obj.data.BIMMeshProperties.ifc_definition_id]
        for layer in ifcopenshell.api.layer.data.Data.layers:
            if layer:
                layer_data = ifcopenshell.api.layer.data.Data.layers[layer]
                if layer_data['id'] == layer_id[0]:
                    propsets["Layer"] = layer_data['Name']
        
    for pset in blenderbim.bim.module.pset.data.ObjectPsetsData.data['psets']:
        spropsets = {}
        for subprop in pset['Properties']:
            spropsets[subprop["Name"]] = subprop 
        
        propsets[pset["Name"]] = spropsets
            
    for qto in blenderbim.bim.module.pset.data.ObjectQtosData.data["qtos"]:
        qpropsets = {}
        for qsubprop in pset['Properties']:
            qpropsets[qsubprop["Name"]] = qsubprop
        
        propsets[qto["Name"]] = qpropsets
            
    #print(propsets)
    
    propset = False
    
    for idx, prop in enumerate(obj.arm_propertylist):
        if prop.name_prop == "BIMDATA":
            obj.arm_propertylist.remove(idx)
            
    obj.arm_propertylist.add()
    obj.arm_propertylist[-1].name_prop = "BIMDATA"
    obj.arm_propertylist[-1].string_prop = json.dumps(propsets, ensure_ascii=False)

class B2A_LoadIFC(bpy.types.Operator):
    bl_idname = "b2a.load"
    bl_label = "Load IFC file"
    bl_description = "Load an IFC file"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene

        print("Load IFC")

        #bpy.ops.bim.load_project()
        bpy.ops.import_ifc.bim()

        return {'FINISHED'}

class B2A_Explore(bpy.types.Operator):
    bl_idname = "b2a.explore"
    bl_label = "Open deployment"
    bl_description = "Explore the deployed files"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene

        print("Load IFC")

        bpy.ops.arm.exporter_open_folder()

        return {'FINISHED'}

class B2A_Prepare(bpy.types.Operator):
    bl_idname = "b2a.prepare"
    bl_label = "Prepare IFC file"
    bl_description = "Prepare the IFC file with the assigned settings"
    bl_options = {'REGISTER', 'UNDO'}

    # @classmethod
    # def poll(self, context):
    #     return context.object is not None
    #     #return context.scene.BIMProperties.ifc_file is None

    def execute(self, context):

        scene = context.scene

        print("Prepare")

        if scene.remove_aux_collections:
            print("Remove collections")

            remove_collections = ["Collection", "Views", "Types", "IfcOpeningElements", "StructuralItems"]
            for col in remove_collections:
    
                collection = bpy.data.collections.get(col)
                
                if collection:
                
                    for obj in collection.objects:
                        
                        bpy.data.objects.remove(obj, do_unlink=True)
                        
                    bpy.data.collections.remove(collection)


        #Deselect all
        print("Deselecting all")
        bpy.ops.object.select_all(action='DESELECT')
        
        if scene.remove_annotations:
            print("Remove annotations")
                
            for obj in bpy.context.scene.objects:
                
                #print(obj.name)
                
                if "IfcAnnotation" in obj.name:
                    
                    print("Found in: " + obj.name)
                
                    obj.select_set(True)

            if len(bpy.context.selected_objects) > 0:
                    
                bpy.ops.object.delete()

        if scene.remove_grids:
            print("Remove grids")

            for obj in bpy.context.scene.objects:
                
                print(obj.name)
                
                if "IfcGrid" in obj.name:
                    
                    print("Found in: " + obj.name)
                
                    obj.select_set(True)
                    
            if len(bpy.context.selected_objects) > 0:
            
                bpy.ops.object.delete()

        if scene.remove_spaces:
            print("Remove spaces")

            for obj in bpy.context.scene.objects:
                
                print(obj.name)
                
                if "IfcSpace" in obj.name:
                    
                    print("Found in: " + obj.name)
                
                    obj.select_set(True)
                    
            if len(bpy.context.selected_objects) > 0:
            
                bpy.ops.object.delete()


        if scene.convert_materials:

            if scene.material_setup == "Grey":

                matName = "Grey"
                
                bpy.data.materials.new(name=matName)

                for obj in bpy.data.objects:

                    for slot in obj.material_slots:

                        slot.material = bpy.data.materials[matName]

            if scene.material_setup == "Native":

                for obj in bpy.data.objects:
                    
                    for slots in obj.material_slots:
                        
                        mat = slots.material

                        mat.use_nodes = True
                        
                        for node in mat.node_tree.nodes:
                            
                            if node.type == "BSDF_PRINCIPLED":
                                
                                #node.inputs.get("Base Color")
                                
                                node.inputs[0].default_value = mat.diffuse_color
                                
                                node.inputs[5].default_value = 0.0
                                
                                node.inputs[7].default_value = mat.roughness

                                if node.inputs[0].default_value[3] < 0.99:
                                    
                                    mat.blend_method = "BLEND"
                                    mat.arm_blending = False
                                    mat.arm_cast_shadow = False

                                    node.inputs[19].default_value = node.inputs[0].default_value[3]


            if scene.material_setup == "Replacement":
                
                pass


        if scene.mesh_grouping == "Performance":

            excluded_objects = []

            if not scene.group_exclusion:

                bpy.ops.text.new()
                bpy.data.texts[-1].name = "ExcludedIfcClasses"
                scene.group_exclusion = bpy.data.texts[-1]

            #exclusion_classes = ['IfcWindow', 'IfcWall', 'IfcWallStandardCase', 'IfcDoor']
            exclusion_string = scene.group_exclusion.as_string()
            exclusion_classes = exclusion_string.split(",")

            print("Performance grouping")

            for obj in bpy.context.scene.objects:
                if obj.type == "MESH":

                    ifcClass = getObjElement(obj).is_a()
                    print(ifcClass)

                    if ifcClass not in exclusion_classes:

                        obj.select_set(True)

                    else:

                        excluded_objects.append(obj)

            bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
                    
            bpy.ops.object.join()

            if scene.expose_excluded_properties:

                for obj in excluded_objects:

                    exposeProperties(obj)

                    #Add physics

            
            for obj in excluded_objects:

                print("Adding physics to: " + obj.name)

                bpy.context.view_layer.objects.active = obj

                bpy.ops.rigidbody.object_add()

                obj.rigid_body.type = "PASSIVE"
            
            #Turn off frustrum culling
            #bpy.context.scene.camera.arm_frustrum_culling = False

        else:

            if scene.expose_properties:

                print("Exposing properties")

                for obj in bpy.data.objects:
                    
                    if obj.type == "MESH":

                        exposeProperties(obj)

                        bpy.context.view_layer.objects.active = obj

                        bpy.ops.rigidbody.object_add()

                        obj.rigid_body.type = "PASSIVE"

        #Get storeys into array
        for obj in scene.objects:

            IfcStore.get_file()

            if not IfcClassData.is_loaded:
                IfcClassData.load()

            element = tool.Ifc.get_entity(obj) #Product

            if element.is_a() == "IfcBuildingStorey":

                storeys.append(obj)

        for index, storey in enumerate(storeys):
            #print(str(index) + " : " + storey.name)
            pass
            #bpy.types.Scene.storeys.append(bpy.props.StringProperty(name=storey.name, description="", default="", subtype="FILE_PATH"))

        for storey in bpy.types.Scene.storeys:
            print(storey)

        #TODO: Clean empty collections

        return {'FINISHED'}

class B2A_MakeLocal(bpy.types.Operator):
    bl_idname = "b2a.make_local"
    bl_label = "Make local"
    bl_description = "Make selection local"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene

        #TODO - Go through all the links: IFC Project Setup > IFC Links and remove links
        #Get the file location, append all objects, localize the objects and add it to a separate location
        #

        for obj in bpy.context.selected_objects:

            #Get linked filename and make collection

            bpy.context.view_layer.objects.active = obj
            obj.make_local()


        return {'FINISHED'}

class B2A_Play(bpy.types.Operator):
    bl_idname = "b2a.play"
    bl_label = "Start Armory3D"
    bl_description = "Start Armory3D"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene

        #Setup exporter
        bpy.ops.arm_exporterlist.new_item()

        bpy.ops.arm.play()

        return {'FINISHED'}

class B2A_Deploy(bpy.types.Operator):
    bl_idname = "b2a.deploy"
    bl_label = "Deploy Armory3D"
    bl_description = "Deploy Armory3D"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        wrd = bpy.data.worlds['Arm']
        return wrd.arm_exporterlist_index >= 0 and len(wrd.arm_exporterlist) > 0

    def execute(self, context):

        scene = context.scene

        if scene.platform == "Executable":
            print("Exporting executable")
            bpy.data.worlds['Arm'].arm_exporterlist[0].arm_project_target = "krom-windows"
        elif scene.platform == "HTML5":
            print("Exporting HTML5/Web")
            bpy.data.worlds['Arm'].arm_exporterlist[0].arm_project_target = "html5"

        bpy.ops.arm.publish_project()
        deployed = True

        return {'FINISHED'}


class B2A_Configure(bpy.types.Operator):
    bl_idname = "b2a.configure"
    bl_label = "Configure Armory"
    bl_description = "Configure Armory"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self,context):
        return context.object is not None and bpy.data.is_saved

    def execute(self, context):

        scene = context.scene

        #Create BIM2ARM Collection
        BIM2ARM_Collection = bpy.data.collections.new("BIM2ARM")
        bpy.context.scene.collection.children.link(BIM2ARM_Collection)

        if scene.setup_camera:

            #Create a new main camera
            mainCamData = bpy.data.cameras.new(name="Cam-BIM2ARM")
            mainCam = bpy.data.objects.new('Cam-BIM2ARM', mainCamData)
            BIM2ARM_Collection.objects.link(mainCam)


            #////////////////////////////////////////////////////////////////////////


            #If plan exists, align to camera to plan and provide a WalkNavigation trait
            camPlanAlignment = "Plan 01"

            storeyLocation = (0,0,0)

            for obj in bpy.context.scene.objects:
                
                IfcStore.get_file()
                    
                if not IfcClassData.is_loaded:
                    IfcClassData.load()
                    
                element = tool.Ifc.get_entity(obj) #Product
                
                if element:
                
                    if element.is_a() == "IfcBuildingStorey":
                        
                        print(obj.name)
                        
                        if "Plan 01" in obj.name:
                            
                            print("Found plan 01")
                    
                            storeyLocation = obj.location
                
            if storeyLocation:

                mainCam.location = storeyLocation
                mainCam.rotation_euler = (1.57,0,0)
                
            mainCam.arm_traitlist.add()
            
            #Copy FlyNavigation trait
            flyNavFile = getAddonFolder() + "/scripts/FlyNavigation.hx"



            armSourcesFolder = getProjectFolder() + "/Sources/arm/"

            #Make folder is it doesn't exist
            os.makedirs(os.path.dirname(armSourcesFolder), exist_ok=True)

            shutil.copy(flyNavFile, armSourcesFolder)

            mainCam.arm_traitlist[0].type_prop = "Haxe Script"
            mainCam.arm_traitlist[0].class_name_prop = "FlyNavigation"

            mainCam.select_set(True)
            bpy.context.view_layer.objects.active = mainCam

            bpy.ops.arm.refresh_scripts()
            context.area.tag_redraw()

            #mainCam.arm_traitlist[0].arm_traitpropslist[0].value_float = 5.0 #Speed
            #mainCam.arm_traitlist[0].arm_traitpropslist[0].value_float = 1.0 #Ease

            mainCam.data.lens = 18.0
            bpy.context.scene.camera = mainCam

            if scene.align_camera:
                bpy.ops.view3d.camera_to_view()

            bpy.data.cameras["Cam-BIM2ARM"].arm_frustum_culling = False
        
        #Setup sun
        if scene.setup_sun:
            bpy.ops.object.light_add(type='SUN', radius=1, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))

            if scene.world_type == "Dynamic":
                bpy.data.objects["Sun"].rotation_euler = (0.69, 0, -0.52)
            if scene.world_type == "Sunrise":
                bpy.data.objects["Sun"].rotation_euler = (1.57, -0.02, 0.96)
            if scene.world_type == "Sunny":
                bpy.data.objects["Sun"].rotation_euler = (0.825, 0.0092, 0.96)
            if scene.world_type == "Cloudy":
                bpy.data.objects["Sun"].rotation_euler = (0.53, -0.21, 0.855)

            bpy.data.lights["Sun"].energy = scene.sun_strength

        #Setup world
        if scene.setup_world:
            bpy.context.scene.world.use_nodes = True

            if scene.world_type == "Dynamic":

                skytex = bpy.context.scene.world.node_tree.nodes.new("ShaderNodeTexSky")
                bg = bpy.context.scene.world.node_tree.nodes["Background"]
                bpy.context.scene.world.node_tree.links.new(bg.inputs[0], skytex.outputs[0])
                skytex.sun_size = 0.01 # + (scene.sun_strength/10)

            else:

                skytex = bpy.context.scene.world.node_tree.nodes.new("ShaderNodeTexEnvironment")
                bg = bpy.context.scene.world.node_tree.nodes["Background"]
                bpy.context.scene.world.node_tree.links.new(bg.inputs[0], skytex.outputs[0])

                if scene.world_type == "Sunrise":
                    envFile = getAddonFolder() + "/environments/Sunrise.hdr"
                if scene.world_type == "Sunny":
                    envFile = getAddonFolder() + "/environments/Sunny.hdr"
                if scene.world_type == "Cloudy":
                    envFile = getAddonFolder() + "/environments/Cloudy.hdr"

                skytexImage = bpy.data.images.load(envFile)

                skytex.image = skytexImage

        #Setup EEVEE View
        scene.eevee.use_gtao = True
        scene.eevee.use_bloom = True
        scene.eevee.gtao_distance = 1
        scene.eevee.gtao_factor = 3


        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas: # iterate through areas in current screen
                if area.type == 'VIEW_3D':
                    for space in area.spaces: # iterate through spaces in current VIEW_3D area
                        if space.type == 'VIEW_3D': # check if space is a 3D view
                            space.shading.type = 'MATERIAL'
                            space.shading.use_scene_world = True
                            space.shading.use_scene_lights = True

        #Setup renderpath
        bpy.ops.arm_rplist.new_item()
        rp = bpy.data.worlds["Arm"].arm_rplist[-1]
        bpy.data.worlds["Arm"].arm_ui = "Enabled"

        if scene.render_path_type == "Low":

            rp.name = "Low"

            rp.rp_shadows = False
            rp.rp_antialiasing = 'Off'
            rp.rp_ssgi = 'Off'

        if scene.render_path_type == "Default":

            rp.name = "Default"

        if scene.render_path_type == "High":

            rp.name = "High"

            rp.rp_shadowmap_cube = '2048'
            rp.rp_shadowmap_cascade = '2048'

            rp.rp_antialiasing = 'TAA'
            rp.rp_supersampling = '1.5'
            rp.rp_ssgi = 'SSAO'
            rp.arm_ssgi_max_steps = 8
            rp.rp_bloom = True
            rp.rp_chromatic_aberration = True
            rp.arm_chromatic_aberration_type = 'Spectral'
            rp.arm_chromatic_aberration_strength = 0.08
            rp.arm_tonemap = 'Reinhard'

        if scene.render_path_type == "Max":

            rp.name = "Max"

            rp.rp_shadowmap_cube = '2048'
            rp.rp_shadowmap_cascade = '2048'

            rp.rp_antialiasing = 'TAA'
            rp.rp_supersampling = '2.0'
            rp.rp_ssgi = 'SSAO'
            rp.arm_ssgi_max_steps = 16
            rp.rp_bloom = True
            rp.rp_chromatic_aberration = True
            rp.arm_chromatic_aberration_type = 'Spectral'
            rp.arm_chromatic_aberration_strength = 0.08
            rp.arm_tonemap = 'Reinhard'
        #Todo

        #Setup resolution
        if scene.resolution == '720':
            scene.render.resolution_x = 1280
            scene.render.resolution_y = 720
        else:
            scene.render.resolution_x = 1920
            scene.render.resolution_y = 1080

        return {'FINISHED'}

class SCENE_PT_B2A_panel (Panel):
    """Main UI panel"""


    bl_idname = "SCENE_PT_B2A_panel"
    bl_label = "BIM2ARM"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BIM2ARM"

    @classmethod
    def poll(self,context):
        return context.object is not None

    def draw(self, context):
        """Draw the UI."""

        layout = self.layout
        scene = context.scene

        #row = layout.row(align=True)

        box = layout.box()
        row = box.row(align=True)
        row.label(text="UI Mode", icon="UV_DATA")
        row = box.row(align=True)
        row.prop(scene, "ui_mode", expand=False)

        box = layout.box()
        row = box.row(align=True)

        row.label(text="Load IFC", icon="UV_DATA")
        row = box.row(align=True)
        if scene.BIMProperties.ifc_file == "":
            row.operator("b2a.load")
        else:
            row.label(text="IFC File: ")
            row.label(text=os.path.basename(scene.BIMProperties.ifc_file))
        
        box = layout.box()
        row = box.row(align=True)
        row.label(text="Prepare IFC", icon="UV_DATA")
        row = box.row(align=True)
        row.prop(scene, "remove_aux_collections")
        row = box.row(align=True)
        row.prop(scene, "remove_annotations")
        row = box.row(align=True)
        row.prop(scene, "remove_grids")
        row = box.row(align=True)
        row.prop(scene, "remove_spaces")
        
        row = box.row(align=True)
        row.prop(scene, "convert_materials")

        if scene.convert_materials:
            row = box.row(align=True)
            row.label(text="Material setup:")
            row = box.row(align=True)
            row.prop(scene, "material_setup")

        row = box.row(align=True)
        row.prop(scene, "mesh_grouping")

        if scene.mesh_grouping == "None":
            row = box.row(align=True)
            row.prop(scene, "expose_properties")

        if scene.mesh_grouping == "Performance":
            row = box.row(align=True)
            row.prop_search(scene, 'group_exclusion', bpy.data, 'texts', text='Group exclusion')
            row = box.row(align=True)
            row.prop(scene, "expose_excluded_properties")

        row = box.row(align=True)
        row.operator("b2a.prepare")

        box = layout.box()
        row = box.row(align=True)
        row.label(text="Configure Armory", icon="FILE_CACHE")

        #W
        row = box.row(align=True)
        row.prop(scene, "setup_camera")
        if scene.setup_camera and scene.ui_mode == "Advanced":
            row = box.row(align=True)
            row.prop(scene, "align_camera")
            row = box.row(align=True)
            row.prop(scene, "camera_fov")

        row = box.row(align=True)
        row.prop(scene, "setup_sun")

        if scene.setup_sun and scene.ui_mode == "Advanced":
            row = box.row(align=True)
            row.prop(scene, "sun_strength")

        row = box.row(align=True)
        row.prop(scene, "setup_world")

        if scene.setup_world:
            row = box.row(align=True)
            row.prop(scene, "world_type")

        row = box.row(align=True)
        row.label(text="Resolution:")
        row = box.row(align=True)
        row.prop(scene, "resolution")
        row = box.row(align=True)
        row.label(text="Graphics Settings:")
        row = box.row(align=True)
        row.prop(scene, "render_path_type")
        row = box.row(align=True)

        row.operator("b2a.configure")


        #Make links local
        if scene.ui_mode == "Advanced":
            box = layout.box()
            row = box.row(align=True)
            row.label(text="Localize linked files", icon="FILE_CACHE")
            row = box.row(align=True)
            row.operator("b2a.make_local")

        #Plan alignment tool
        if scene.ui_mode == "Advanced":
            box = layout.box()
            row = box.row(align=True)
            row.label(text="Plan alignment tool", icon="FILE_CACHE")

            for idx, storey in enumerate(storeys):
                row = box.row(align=True)
                row.label(text=storey.name)
                #row.prop(scene, "storeys")
                row.prop(scene, "storeys['" + str(idx) + "']")

                #col.prop(context.active_object, '["' + MinkoScript.format_property_name(i, key) + '"]',text='')


            #if 
            
            # for obj in scene.objects:

            #     IfcStore.get_file()
    
            #     if not IfcClassData.is_loaded:
            #         IfcClassData.load()
                    
            #     element = tool.Ifc.get_entity(obj) #Product

            #     if element.is_a() == "IfcBuildingStorey":

            #         row.label(text="Plan: " + obj.name)

        box = layout.box()
        row = box.row(align=True)
        row.label(text="Start Armory", icon="FILE_CACHE")
        row = box.row(align=True)
        row.operator("b2a.play")

        box = layout.box()
        row = box.row(align=True)
        row.label(text="Deploy Armory", icon="FILE_CACHE")
        row = box.row(align=True)
        row.label(text="Platform:")
        row = box.row(align=True)
        row.prop(scene, "platform")
        row = box.row(align=True)
        row.operator("b2a.deploy")
        if deployed == True:
            row = box.row(align=True)
            row.operator("b2a.explore")

classes = [SCENE_PT_B2A_panel, B2A_Prepare, B2A_Configure, B2A_Play, B2A_Deploy, B2A_LoadIFC, B2A_Explore, B2A_MakeLocal]

def register():
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.ui_mode = EnumProperty(
        items = [('Easy', 'Easy', 'The UI is minimized to be as simple as possible'),
                 ('Advanced', 'Advanced', 'The UI exposes all available options, but can be more complex and time-consuming to setup')],
                name = "", description="UI mode for the addon", default='Easy')

    bpy.types.Scene.remove_aux_collections = bpy.props.BoolProperty(name="Remove Auxillary Collections", default=True, description="Remove the extra collections that are linked internally. Might break if not toggled or prepared manually")
    bpy.types.Scene.remove_annotations = bpy.props.BoolProperty(name="Remove annotations", default=True, description="Remove all 2D annotations from the file")
    bpy.types.Scene.remove_spaces = bpy.props.BoolProperty(name="Remove spaces", default=True, description="Remove all spaces from the file")
    
    bpy.types.Scene.space_setup = EnumProperty(
        items = [('None', 'None', 'None'),
                 ('Spatial', 'Spatial Volumes', '')],
                name = "", description="Method for assigning IFC materials", default='None')
    
    bpy.types.Scene.remove_grids = bpy.props.BoolProperty(name="Remove grids", default=True, description="Remove all grids from the file")
    bpy.types.Scene.convert_materials = bpy.props.BoolProperty(name="Convert materials", default=True, description="Converts IFC materials")
    bpy.types.Scene.material_setup = EnumProperty(
        items = [('Grey', 'Grey', 'Default to grey material'),
                 ('Native', 'Native', 'Convert IFC colors to materials'),
                 ('Replacement', 'Replacement Schema', 'Use a replacement schema to assign materials')],
                name = "", description="Method for assigning IFC materials", default='Grey')
    bpy.types.Scene.mesh_grouping = EnumProperty(
        items = [('None', 'None', ''),
                 ('Performance', 'Performance Grouping', 'Join the individual object meshes into one object for improved performance, but looses properties. Best just for visualizing information')],
                name = "", description="Mesh grouping", default='None')
    bpy.types.Scene.group_exclusion = bpy.props.PointerProperty(name="Group exclusion", description="List of IFC classes to exclude from the grouping, for instance 'IfcWindow, IfcDoor', etc", type=bpy.types.Text)
    bpy.types.Scene.expose_properties = bpy.props.BoolProperty(name="Expose IFC property sets", default=False, description="")
    bpy.types.Scene.expose_excluded_properties = bpy.props.BoolProperty(name="Expose IFC property sets for excluded", default=False, description="Expose IFC property sets for excluded")

    bpy.types.Scene.setup_camera = bpy.props.BoolProperty(name="Setup camera", default=True, description="Setup camera")
    bpy.types.Scene.camera_fov = bpy.props.FloatProperty(name="Camera FOV", description="Set the camera field of view in degrees", default=90.0)
    bpy.types.Scene.camera_speed = bpy.props.FloatProperty(name="Camera speed", description="Set the camera speed", default=5.0)
    bpy.types.Scene.camera_easing = bpy.props.FloatProperty(name="Camera easing", description="Set the camera movement easing", default=1.0)
    
    #bpy.types.Scene.camera_easing = bpy.props.StringProperty(name="OIDN Path", description="The path to the OIDN binaries", default="", subtype="FILE_PATH")
    
    bpy.types.Scene.align_camera = bpy.props.BoolProperty(name="Align camera to view", default=False, description="Align the camera to the active view")
    bpy.types.Scene.setup_sun = bpy.props.BoolProperty(name="Setup sun", default=True, description="Setup sun")
    bpy.types.Scene.sun_strength = bpy.props.FloatProperty(name="Sun strength", description="Set sun strength", default=3.0)
    bpy.types.Scene.sun_volumetric = bpy.props.BoolProperty(name="Volumetric Lighting", default=False, description="Add volumetric lighting (God rays)")
    
    bpy.types.Scene.setup_world = bpy.props.BoolProperty(name="Setup world", default=True, description="Setup world")
    bpy.types.Scene.world_type = EnumProperty(
        items = [('Dynamic', 'Dynamic built-in', ''),
                 ('Sunrise', 'Sunrise', ''),
                 ('Sunny', 'Sunny', ''),
                 ('Cloudy', 'Cloudy', '')],
                name = "", description="Set world environment type", default='Dynamic')
    bpy.types.Scene.render_path_type = EnumProperty(
        items = [('Low', 'Low', ''),
                 ('Default', 'Default', ''),
                 ('High', 'High', ''),
                 ('Max', 'Max', '')],
                name = "", description="Default renderpath type", default='Default')
    bpy.types.Scene.resolution = EnumProperty(
        items = [('720', '720p', '720p. Equals 1280x720 resolution.'),
                 ('1080', '1080p', '1080p. Equals 1920x1080 resolution.')],
                name = "", description="Default resolution", default='720')

    bpy.types.Scene.platform = EnumProperty(
        items = [('Executable', 'Executable', 'Create a platform specific executable, ie. ".exe" file for Windows'),
                 ('HTML5', 'HTML5', 'Create a web export file. You need a server to view the file')],
                name = "", description="Select platform to deploy to", default='Executable')

    bpy.types.Scene.storeys = []
    

def unregister():
    for cls in reversed(classes):
        unregister_class(cls)







'''
I've been working a bit on an addon to create an interface between BlenderBIM and Armory3D, which will make it easy to communicate and visualize designs from IFC files.

In case you don't know about Armory3D - It's essentially a game engine that works as an integrated addon for Blender, similar to BlenderBIM. One of the pros of using Armory3D is it's versatile deployment options, where you can deploy to the web through HTML5, but also allows for binaries for every almost platform, including Android and iOS.

I don't know if anyone else would find this useful, but if anything I'll keep developing for my own needs. If anyone is interested it's available here *Github*:


It's of course free and open-source.



TODO:
- Links not yet working (Append for now)
- comma separated exclusion of IFC classes
- Door / Window tool
- Prepare: Grid
- Spaces to Volumes
'''