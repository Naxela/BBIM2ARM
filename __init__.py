
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
    "blender" : (3, 3, 0),
    "version" : (0, 1, 5),
    "location" : "View3D > Sidebar",
    "warning" : "",
    "support": "COMMUNITY",
    "category" : "3D View",
    "doc_url": "",
}

import bpy, blenderbim, ifcopenshell, os, csv, json, sys, importlib, shutil, platform, webbrowser, math
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

class B2A_Props(): #scene.b2a_props
    ifc_loaded = False
    ifc_configured = False
    ifc_prepared = False
    storeys = []
    deployed = False

def getProjectFolder():

    if bpy.data.is_saved:

        return bpy.path.abspath("//")

    else:

        return

def getScript(scriptInt, properties):

    if scriptInt == 0: #FlyNavigation.hx

        sScript = """
package arm;

import iron.Trait;
import iron.system.Input;
import iron.system.Time;
import iron.object.CameraObject;
import iron.math.Vec4;

class FlyNavigation extends Trait {

	@prop
	public var speed:Float = """ + properties[0] + """;
	@prop
	public var ease:Float = """ + properties[1] + """;

	public static var enabled = true;
	var dir = new Vec4();
	var xvec = new Vec4();
	var yvec = new Vec4();

	var camera: CameraObject;

	var keyboard: Keyboard;
	var gamepad: Gamepad;
	var mouse: Mouse;

	public function new() {
		super();
		notifyOnInit(init);
	}

	function init() {
		keyboard = Input.getKeyboard();
		gamepad = Input.getGamepad();
		mouse = Input.getMouse();

		try {
			camera = cast(object, CameraObject);
		}
		catch (msg: String) {
			trace("Error occurred: " + msg + "\nWalkNavigation trait should be used with a camera object.");
		}

		if (camera != null){
			notifyOnUpdate(update);
		}
	}

	function update() {
		if (!enabled || Input.occupied) return;

		var moveForward = keyboard.down(keyUp) || keyboard.down("up");
		var moveBackward = keyboard.down(keyDown) || keyboard.down("down");
		var strafeLeft = keyboard.down(keyLeft) || keyboard.down("left");
		var strafeRight = keyboard.down(keyRight) || keyboard.down("right");
		var strafeUp = keyboard.down(keyStrafeUp);
		var strafeDown = keyboard.down(keyStrafeDown);
		var fast = keyboard.down("shift") ? 2.0 : (keyboard.down("alt") ? 0.5 : 1.0);

		if (gamepad != null) {
			var leftStickY = Math.abs(gamepad.leftStick.y) > 0.05;
			var leftStickX = Math.abs(gamepad.leftStick.x) > 0.05;
			var r1 = gamepad.down("r1") > 0.0;
			var l1 = gamepad.down("l1") > 0.0;
			var rightStickX = Math.abs(gamepad.rightStick.x) > 0.1;
			var rightStickY = Math.abs(gamepad.rightStick.y) > 0.1;

			if (leftStickY || leftStickX || r1 || l1 || rightStickX || rightStickY) {
				dir.set(0, 0, 0);

				if (leftStickY) {
					yvec.setFrom(camera.look());
					yvec.mult(gamepad.leftStick.y);
					dir.add(yvec);
				}
				if (leftStickX) {
					xvec.setFrom(camera.right());
					xvec.mult(gamepad.leftStick.x);
					dir.add(xvec);
				}
				if (r1) dir.addf(0, 0, 1);
				if (l1) dir.addf(0, 0, -1);

				var d = Time.delta * speed * fast;
				camera.transform.move(dir, d);

				if (rightStickX) {
					camera.transform.rotate(Vec4.zAxis(), -gamepad.rightStick.x / 15.0);
				}
				if (rightStickY) {
					camera.transform.rotate(camera.right(), gamepad.rightStick.y / 15.0);
				}
			}
		}

		if (moveForward || moveBackward || strafeRight || strafeLeft || strafeUp || strafeDown) {
			ease += Time.delta * 15;
			if (ease > 1.0) ease = 1.0;
			dir.set(0, 0, 0);
			if (moveForward) dir.addf(camera.look().x, camera.look().y, camera.look().z);
			if (moveBackward) dir.addf(-camera.look().x, -camera.look().y, -camera.look().z);
			if (strafeRight) dir.addf(camera.right().x, camera.right().y, camera.right().z);
			if (strafeLeft) dir.addf(-camera.right().x, -camera.right().y, -camera.right().z);
			#if arm_yaxisup
			if (strafeUp) dir.addf(0, 1, 0);
			if (strafeDown) dir.addf(0, -1, 0);
			#else
			if (strafeUp) dir.addf(0, 0, 1);
			if (strafeDown) dir.addf(0, 0, -1);
			#end
		}
		else {
			ease -= Time.delta * 20.0 * ease;
			if (ease < 0.0) ease = 0.0;
		}

		if (mouse.wheelDelta < 0) {
			speed *= 1.1;
		} else if (mouse.wheelDelta > 0) {
			speed *= 0.9;
			if (speed < 0.5) speed = 0.5;
		}

		var d = Time.delta * speed * fast * ease;
		if (d > 0.0) camera.transform.move(dir, d);

		if (mouse.down('right')) {
			#if arm_yaxisup
			camera.transform.rotate(Vec4.yAxis(), 0.45 * -mouse.movementX / 200);
			#else
			camera.transform.rotate(Vec4.zAxis(), 0.45 * -mouse.movementX / 200);
			#end
			camera.transform.rotate(camera.right(), 0.45 * -mouse.movementY / 200);
		}
	}

	#if arm_azerty
	static inline var keyUp = "z";
	static inline var keyDown = "s";
	static inline var keyLeft = "q";
	static inline var keyRight = "d";
	static inline var keyStrafeUp = "e";
	static inline var keyStrafeDown = "a";
	#else
	static inline var keyUp = "w";
	static inline var keyDown = "s";
	static inline var keyLeft = "a";
	static inline var keyRight = "d";
	static inline var keyStrafeUp = "e";
	static inline var keyStrafeDown = "q";
	#end
}
        
        """

        pass

    return sScript

def getAddonFolder():

    context = bpy.context

    script_file = os.path.realpath(__file__)
    directory = os.path.dirname(script_file)

    return directory

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

def getparentCollectionNames(collection, parent_names):
    for parent_collection in bpy.data.collections:
        if collection.name in parent_collection.children.keys():
        
            if "/" in parent_collection.name:
                
                ifcClass = parent_collection.name.split("/")[0]
                ifcName = parent_collection.name.split("/")[1]
                
                #print(ifcClass)
                #print(ifcName)
                
                if ifcName == "":
                    parent_names.append(ifcClass)
                else:
                    parent_names.append(ifcName)
      
            getparentCollectionNames(parent_collection, parent_names)
        
            return

def getParentHierarchy(obj):
    parent_collection = obj.users_collection[0]
    parent_names      = []
    
    if "/" in parent_collection.name:
        ifcClass = parent_collection.name.split("/")[0]
        ifcName = parent_collection.name.split("/")[1]
        
        if ifcName == "":
            parent_names.append(ifcClass)
        else:
            parent_names.append(ifcName)
    
    getparentCollectionNames(parent_collection, parent_names)
    parent_names.reverse()
    return '\\'.join(parent_names)

def exposeProperties(obj):
    bpy.context.view_layer.objects.active = obj
    
    #If...blenderbim?
    
    print("Exposing properties: " + obj.name)
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
    
    # if not ifcopenshell.api.layer.data.Data.is_loaded:
    #     ifcopenshell.api.layer.data.Data.load(blenderbim.bim.ifc.IfcStore.get_file())
    
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
        
    # #IFC Layer !!OBS IF THERE IS NO LAYERS PRESENT???
    # if obj.data.BIMMeshProperties.ifc_definition_id in ifcopenshell.api.layer.data.Data.items:
    #     layer_id = ifcopenshell.api.layer.data.Data.items[obj.data.BIMMeshProperties.ifc_definition_id]
    #     for layer in ifcopenshell.api.layer.data.Data.layers:
    #         if layer:
    #             layer_data = ifcopenshell.api.layer.data.Data.layers[layer]
    #             if layer_data['id'] == layer_id[0]:
    #                 propsets["Layer"] = layer_data['Name']
        
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

    obj.arm_propertylist.add()
    obj.arm_propertylist[-1].name_prop = "IFCCLASS"
    obj.arm_propertylist[-1].string_prop = getObjElement(obj).is_a() 

    obj.arm_propertylist.add()
    obj.arm_propertylist[-1].name_prop = "BIMHIERARCHY"
    obj.arm_propertylist[-1].string_prop = getParentHierarchy(obj)

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

        scene.b2a_props.ifc_loaded = True

        return {'FINISHED'}

class B2A_Explore(bpy.types.Operator):
    bl_idname = "b2a.explore"
    bl_label = "Open deployment"
    bl_description = "Explore the deployed files"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene

        print("Load IFC")

        if not bpy.data.is_saved:
            self.report({'INFO'}, "Please save your file first")
            return {"CANCELLED"}

        filepath = bpy.data.filepath
        filename = os.path.splitext(os.path.basename(filepath))[0]
        #dirpath = os.path.join(os.path.dirname(bpy.data.filepath), scene.TLM_EngineProperties.tlm_lightmap_savedir)
        dirpath = os.path.join(os.path.dirname(filepath), ("build_" + filename), "debug")
        
        if platform.system() != "Linux":

            if os.path.isdir(dirpath):
                webbrowser.open('file://' + dirpath)
            else:
                os.mkdir(dirpath)
                webbrowser.open('file://' + dirpath)
        else:

            if os.path.isdir(dirpath):
                os.system('xdg-open "%s"' % dirpath)
                #webbrowser.open('file://' + dirpath)
            else:
                os.mkdir(dirpath)
                os.system('xdg-open "%s"' % dirpath)
                #webbrowser.open('file://' + dirpath)

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

        print("Prepare IFC Started")

        #Name original scene
        bpy.context.scene.name = "BIM_MainScene"

        #Set no armory export
        bpy.data.scenes["BIM_MainScene"].arm_export = False

        #Create a new scene
        bpy.data.scenes.new(name='BIM2ARM')

        #Set active scene
        bpy.context.window.scene = bpy.data.scenes["BIM2ARM"]

        for obj in bpy.data.scenes["BIM_MainScene"].objects:
            
            bpy.data.scenes["BIM2ARM"].collection.objects.link(obj)

        if scene.BIMProperties.ifc_file != "":
            scene.b2a_props.ifc_loaded = True

        if scene.remove_aux_collections:
            print("Removing collections")

            remove_collections = ["Collection", "Views", "Types", "IfcOpeningElements", "StructuralItems"]
            for col in remove_collections:
    
                collection = bpy.data.collections.get(col)
                
                if collection:
                
                    for obj in collection.objects:
                        
                        bpy.data.objects.remove(obj, do_unlink=True)
                        
                    print("Removing collection: " + collection.name)
                    bpy.data.collections.remove(collection)

        #Make single-user
        bpy.data.worlds["Arm"].arm_batch_meshes = True
        bpy.data.worlds["Arm"].arm_batch_materials = False

        print("Making objects to single user: Selecting")

        for obj in bpy.context.scene.objects:

            if obj.type == "MESH":
            
                obj.select_set(True)

        print("Making objects to single user: Apply Single User")
        
        bpy.ops.object.make_single_user(object=True, obdata=True, material=False, animation=False, obdata_animation=False)

        #Deselect all
        print("Deselecting all")
        bpy.ops.object.select_all(action='DESELECT')
        
        if scene.remove_annotations:
            print("Removing annotations")
                
            for obj in bpy.context.scene.objects:
                
                #print(obj.name)
                
                if "IfcAnnotation" in obj.name:
                    
                    print("Found in: " + obj.name)
                
                    obj.select_set(True)

            if len(bpy.context.selected_objects) > 0:
                    
                bpy.ops.object.delete()

        if scene.remove_grids:
            print("Removing grids")

            for obj in bpy.context.scene.objects:
                
                print("Grid removed: " + obj.name)
                
                if "IfcGrid" in obj.name:
                    
                    print("Found in: " + obj.name)
                
                    obj.select_set(True)
                    
            if len(bpy.context.selected_objects) > 0:
            
                bpy.ops.object.delete()

        if scene.remove_spaces:
            print("Removing spaces")

            for obj in bpy.context.scene.objects:
                
                print("Space removed: " + obj.name)
                
                if "IfcSpace" in obj.name:
                    
                    print("Found in: " + obj.name)
                
                    obj.select_set(True)
                    
            if len(bpy.context.selected_objects) > 0:
            
                bpy.ops.object.delete()

        if scene.add_b2a_lib:

            b2a_asset_path = os.path.join(getAddonFolder(),"assets")

            lib_found = False
            for alib in bpy.context.preferences.filepaths.asset_libraries:
                
                if alib.name == "B2A_Library":
                    lib_found = True
                    
            if not lib_found:
                bpy.ops.preferences.asset_library_add(directory=b2a_asset_path)
                bpy.context.preferences.filepaths.asset_libraries[-1].name = "B2A_Library"

        if scene.convert_materials:

            print("Converting materials")

            bpy.data.materials.new(name="B2AGrey")

            if scene.material_setup == "Grey":

                matName = "Grey"
                
                bpy.data.materials.new(name=matName)

                for obj in bpy.context.scene.objects:

                    for slot in obj.material_slots:

                        slot.material = bpy.data.materials[matName]

            if scene.material_setup == "Native":

                for obj in bpy.context.scene.objects:

                    if obj.type == "MESH":

                        print("Replacing for object: " + obj.name)

                        if len(obj.material_slots) < 1:

                            print("Object has no material")
                            obj.data.materials.append(bpy.data.materials["B2AGrey"])

                        else:
                        
                            for slots in obj.material_slots:

                                mat = slots.material

                                mat.use_nodes = True
                                mat.arm_ignore_irradiance = True
                                mat.arm_two_sided = False
                                
                                for node in mat.node_tree.nodes:
                                    
                                    if node.type == "BSDF_PRINCIPLED":
                                        
                                        #node.inputs.get("Base Color")
                                        
                                        node.inputs.get("Base Color").default_value = mat.diffuse_color
                                        
                                        node.inputs.get("Specular").default_value = 0.0
                                        
                                        node.inputs.get("Roughness").default_value = mat.roughness

                                        if node.inputs.get("Base Color").default_value[3] < 0.99:
                                            
                                            mat.blend_method = "BLEND"
                                            mat.shadow_method = "CLIP"
                                            mat.arm_blending = False
                                            mat.arm_cast_shadow = False
                                            mat.arm_ignore_irradiance = True

                                            node.inputs.get("Alpha").default_value = node.inputs.get("Base Color").default_value[3]


            if scene.material_setup == "Replacement":

                if not bpy.data.scenes["Scene"].replacement_file:
                    pass

                #    print(x)

                if not bpy.data.scenes["Scene"].replacement_schema:
                    pass

                #    print(y)
                
                materialFile = bpy.path.abspath(bpy.data.scenes["Scene"].replacement_file)

                with bpy.data.libraries.load(materialFile) as (data_from, data_to):
                    data_to.materials = data_from.materials

                replacementList = bpy.path.abspath(bpy.data.scenes["Scene"].replacement_schema)

                csv_dict = {}

                with open(replacementList, mode='r') as inp:
                    csv_reader = csv.reader(inp)
                    for row in csv_reader:
                        if row:
                            if row[1] != 'None':
                                omat = row[0]
                                rmat = row[1]
                                mscale = row[2]
                                uvscale = row[3]

                                csv_dict[omat] = [rmat, mscale, uvscale]

                for obj in bpy.context.scene.objects:

                    for slot in obj.material_slots:

                        slot_mat = slot.material.name

                        if slot_mat != "":

                            if slot_mat in csv_dict:

                                slot.material = bpy.data.materials[csv_dict[slot_mat][0]]

                                print("FOUND!")
                                print(csv_dict[slot_mat])

                                nodes = slot.material.node_tree.nodes

                                for node in nodes:

                                    if node.type == "MAPPING":

                                        mscale = float(csv_dict[slot_mat][1])

                                        node.inputs.get('Scale').default_value = (mscale,mscale,mscale) 
                                        #csv_dict[slot_mat][1]
                                        #node.inputs.get('Scale').default_value.y = csv_dict[slot_mat][1]
                                        #node.inputs.get('Scale').default_value.z = csv_dict[slot_mat][1]

                            else:

                                print("UNKNOWN! Skip: " + slot_mat)
            

        if scene.mesh_grouping == "Performance":

            excluded_objects = []

            if not scene.group_exclusion:

                bpy.ops.text.new()
                bpy.data.texts[-1].name = "ExcludedIfcClasses"
                scene.group_exclusion = bpy.data.texts[-1]

            #exclusion_classes = ['IfcWindow', 'IfcWall', 'IfcWallStandardCase', 'IfcDoor']
            #TODO CHECK LINES COMMENTED OUT

            #exclusion_string = scene.group_exclusion.as_string()

            #lined_exclusion_string = exclusion_string.split('\n')

            #for line in lined_exclusion_string:
            #    if line.startswith("#"):
            #        lined_exclusion_string.remove(line)
            #        pass
            #        #print(line)
            #        

            #print(lined_exclusion_string)

            #exclusion_classes = exclusion_string.split(",")


            exclusion_string = scene.group_exclusion.as_string()
            exclusion_classes = exclusion_string.split(",")

            print("Performance grouping")

            for obj in bpy.context.scene.objects:
                if obj.type == "MESH":

                    ifcClass = getObjElement(obj).is_a()
                    print("Obj is a: " + ifcClass)

                    if ifcClass not in exclusion_classes:

                        obj.select_set(True)

                    else:

                        excluded_objects.append(obj)

            bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
            
            print("Joining objects for performance")

            bpy.ops.object.join()

            print("Joining complete")

            print("Cube projecting")
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            angle = math.radians(45.0)
            bpy.ops.uv.cube_project()
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')

            bpy.context.selected_objects[0].name = "B2AGroup"

            if scene.expose_excluded_properties:

                for obj in excluded_objects:

                    exposeProperties(obj)
            
            for obj in excluded_objects:

                print("Adding physics to: " + obj.name)

                bpy.context.view_layer.objects.active = obj

                bpy.ops.rigidbody.object_add()
                obj.rigid_body.type = "PASSIVE"
                obj.rigid_body.collision_shape = 'MESH'
                obj.rigid_body.mesh_source = 'BASE'

        else:

            print("No performance grouping")

            if not bpy.context.scene.rigidbody_world:
                bpy.ops.rigidbody.world_add()
                
            bpy.context.scene.rigidbody_world.enabled = True

            for obj in bpy.context.scene.objects:

                if obj.type == "MESH":

                    obj.select_set(True)
                    bpy.context.view_layer.objects.active = obj

            bpy.ops.rigidbody.objects_add(type='ACTIVE')

            for obj in bpy.context.scene.objects:

                if obj.type == "MESH":
            

                    #print("Adding physics to: " + obj.name)

                    #bpy.context.view_layer.objects.active = obj
                    #bpy.ops.rigidbody.object_add()
                    obj.rigid_body.type = "PASSIVE"
                    obj.rigid_body.collision_shape = 'MESH'
                    obj.rigid_body.mesh_source = 'BASE'

                #TODO - Select joined

                #bpy.context.view_layer.objects.active = obj
                #bpy.ops.object.make_single_user(type='ALL', object=True, obdata=True)

            if scene.expose_properties:

                print("Exposing properties")

                for obj in bpy.context.scene.objects:
                    
                    if obj.type == "MESH":

                        exposeProperties(obj)

        #Get storeys into array
        for obj in scene.objects:

            print("Getting IFC File")
            IfcStore.get_file()

            if not IfcClassData.is_loaded:
                IfcClassData.load()

            print("Getting Entity for: " + obj.name)
            element = tool.Ifc.get_entity(obj) #Product

            if element.is_a() == "IfcBuildingStorey":

                print("Entity: " + obj.name)

                scene.b2a_props.storeys.append(obj)

                #bpy.app.driver_namespace['b2a_storeys'].append(obj.name)

        #for index, storey in enumerate(scene.b2a_props.storeys):
            #print(str(index) + " : " + storey.name)
            #pass
            #bpy.types.Scene.storeys.append(bpy.props.StringProperty(name=storey.name, description="", default="", subtype="FILE_PATH"))

        #for storey in bpy.app.driver_namespace['b2a_storeys']:
            #print(storey)

        #TODO: Clean empty collections

        scene.b2a_props.ifc_prepared = True

        print("Project prepared")

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

class B2A_ImportPlan(bpy.types.Operator):
    bl_idname = "b2a.import_plan"
    bl_label = "Import Plan"
    bl_description = "Import the selected plan"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        selectedPlan = bpy.data.scenes["Scene"].levels

        selectedPlanStorey = bpy.context.scene.objects[selectedPlan]

        PlanHeight = selectedPlanStorey.location.z
        PlanRotation = selectedPlanStorey.rotation_euler.z

        selectedFile = bpy.path.abspath(bpy.data.scenes["Scene"].levelPlan)

        #projectedFolder = os.path.abspath(getProjectFolder())

        fileLocation = selectedFile

        fileName = os.path.basename(fileLocation)

        baseName = fileName.split(".")[0]

        fileExtension = fileName.split(".")[-1]

        #if fileExtension == "pdf":
        #    pass

        if fileExtension in ["jpg","jpeg","png","tiff","bmp"]:

            print("File found")

            loaded_file = bpy.data.images.load(fileLocation, check_existing=False)

        fsize_x = loaded_file.size[0]
        fsize_y = loaded_file.size[1]

        if bpy.data.scenes["Scene"].levelPlanDPI == "Low":
            dpi = 72
        elif bpy.data.scenes["Scene"].levelPlanDPI == "Medium":
            dpi = 150
        elif bpy.data.scenes["Scene"].levelPlanDPI == "High":
            dpi = 300
        elif bpy.data.scenes["Scene"].levelPlanDPI == "Presentation":
            dpi = 600
        else: #Custom
            dpi = 1


        if bpy.data.scenes["Scene"].levelScale == "a":
            paperScale = 5
        elif bpy.data.scenes["Scene"].levelScale == "b":
            paperScale = 10
        elif bpy.data.scenes["Scene"].levelScale == "c":
            paperScale = 20
        elif bpy.data.scenes["Scene"].levelScale == "d":
            paperScale = 50
        elif bpy.data.scenes["Scene"].levelScale == "e":
            paperScale = 100
        elif bpy.data.scenes["Scene"].levelScale == "f":
            paperScale = 200
        else:
            paperScale = 50

        #Units?
        rsize_x = 2.54 * fsize_x / dpi
        rsize_y = 2.54 * fsize_y / dpi

        #Scale
        ssize_x = rsize_x / 100
        ssize_y = rsize_y / 100

        material = bpy.data.materials.new(name=baseName)
        material.use_nodes = True

        outputNode = material.node_tree.nodes[0] #Presumed to be material output node

        if(outputNode.type != "OUTPUT_MATERIAL"):
            for node in material.node_tree.nodes:
                if node.type == "OUTPUT_MATERIAL":
                    outputNode = node
                    break

        mainNode = outputNode.inputs[0].links[0].from_node
        imgNode = material.node_tree.nodes.new("ShaderNodeTexImage")
        imgNode.location.x = -450
        imgNode.location.y = 200
        imgNode.image = loaded_file

        material.node_tree.links.new(mainNode.inputs.get("Base Color"), imgNode.outputs.get("Color"))

        bpy.ops.mesh.primitive_plane_add(size=1, align='WORLD', location=(0,0,PlanHeight), rotation=(0,0,PlanRotation), scale=(1,1,1))
        #bpy.ops.mesh.primitive_plane_add(size=1, align='WORLD', location=(0,0,PlanHeight), rotation=(0,0,0), scale=(1,1,1))
        imgPlane = bpy.context.scene.objects["Plane"]
        imgPlane.scale.x = ssize_x * paperScale
        imgPlane.scale.y = ssize_y * paperScale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        imgPlane.data.materials.append(material)

        imgPlane.location.x = (bpy.data.scenes["Scene"].offsetPlanX / 1000)
        imgPlane.location.y = (bpy.data.scenes["Scene"].offsetPlanY / 1000)

        #print("Size: " + str(rsize_x))

        return {'FINISHED'}

class B2A_CreateCSVTemplate(bpy.types.Operator):
    bl_idname = "b2a.create_csv"
    bl_label = "Create CSV Template"
    bl_description = "Create a CSV template file with all the materials listed"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene

        #List all materials
        materials = []

        for mat in bpy.data.materials:

            if mat.users > 0:

                materials.append(mat.name)

        csv_header = ['Material', 'Replacement', 'Material Scale', 'UV Scale']

        csv_data = []

        for m in materials:
            csv_data.append({'Material':m, 'Replacement':'None', 'Material Scale':1, 'UV Scale':1})

        print(csv_data)

        csv_path = os.path.join(getProjectFolder(), "replacement_schema.csv")

        with open(csv_path, 'w', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=csv_header)
            writer.writeheader()
            writer.writerows(csv_data)

        print(materials)

        return {'FINISHED'}

class B2A_Play(bpy.types.Operator):
    bl_idname = "b2a.play"
    bl_label = "Start Armory3D"
    bl_description = "Start Armory3D"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene

        #Setup exporter

        if "BIM2ARM_Exporter" in bpy.data.worlds["Arm"].arm_exporterlist:

            pass

        else:

            bpy.ops.arm_exporterlist.new_item()

            bpy.data.worlds["Arm"].arm_exporterlist[-1].name = "BIM2ARM_Exporter"

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

            if platform.system() == "Windows":

                bpy.data.worlds['Arm'].arm_exporterlist["BIM2ARM_Exporter"].arm_project_target = "krom-windows"

            elif scene.platform == "Linux":

                bpy.data.worlds['Arm'].arm_exporterlist["BIM2ARM_Exporter"].arm_project_target = "krom-linux"

            else:

                bpy.data.worlds['Arm'].arm_exporterlist["BIM2ARM_Exporter"].arm_project_target = "krom-macos"

        elif scene.platform == "HTML5":
            print("Exporting HTML5/Web")
            bpy.data.worlds['Arm'].arm_exporterlist["BIM2ARM_Exporter"].arm_project_target = "html5"

        bpy.ops.arm.publish_project()
        deployed = True

        return {'FINISHED'}

class B2A_LightmapObjects(bpy.types.Operator):
    bl_idname = "b2a.lightmap"
    bl_label = "Lightmap Objects"
    bl_description = "Lightmap available objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene

        print("Coming soon")

        return {'FINISHED'}

class B2A_CreateTemplateGroup(bpy.types.Operator):
    bl_idname = "b2a.templategroup"
    bl_label = "Add example file"
    bl_description = "Add empty IFC Grouping template file"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self,context):
        return context.object is not None and bpy.data.is_saved

    def execute(self, context):

        bpy.ops.text.new()
        bpy.data.texts[-1].name = "ExcludedIfcClasses"
        scene.group_exclusion = bpy.data.texts[-1]

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

        if scene.BIMProperties.ifc_file != "":
            scene.b2a_props.ifc_loaded = True


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
            #flyNavFile = getAddonFolder() + "/scripts/FlyNavigation.hx"

            #armSourcesFolder = getProjectFolder() + "/Sources/arm/"

            armSourcesFolder = getProjectFolder() + "/Sources/arm"
            armCanvasFolder = getProjectFolder() + "/Bundled/canvas"

            flvScript = getScript(0,[str(scene.camera_speed), str(scene.camera_easing)])
            #print(flvScript)

            #Make folder is it doesn't exist
            os.makedirs(armSourcesFolder, exist_ok=True)
            os.makedirs(armCanvasFolder, exist_ok=True)

            #os.path.join(getAddonFolder,"assets/canvas")
            #if not os.path.isdir(os.path.join(getAddonFolder(),"assets","canvas")): getProjectFolder() + "/Bundled/canvas"
            shutil.copytree(os.path.join(getAddonFolder(),"assets","canvas"), os.path.join(getProjectFolder(),'Bundled','canvas'), dirs_exist_ok=True)

            shutil.copy(os.path.join(getAddonFolder(),"scripts","BIMInspector.hx"), os.path.join(armSourcesFolder,"BIMInspector.hx"))

            with open(armSourcesFolder + "/FlyNavigation.hx","w") as f:
                f.write(flvScript)

            #shutil.copy(flyNavFile, armSourcesFolder)

            mainCam.arm_traitlist[-1].type_prop = "Haxe Script"
            mainCam.arm_traitlist[-1].class_name_prop = "FlyNavigation"

            mainCam.select_set(True)
            bpy.context.view_layer.objects.active = mainCam

            #BIMInspector
            mainCam.arm_traitlist.add()
            mainCam.arm_traitlist[-1].type_prop = "Haxe Script"
            mainCam.arm_traitlist[-1].class_name_prop = "BIMInspector"

            #Setup UI
            mainCam.arm_traitlist.add()
            mainCam.arm_traitlist[-1].type_prop = "UI Canvas"
            mainCam.arm_traitlist[-1].canvas_name_prop = "HD-Canvas"

            bpy.ops.arm.refresh_scripts()
            context.area.tag_redraw()

            #mainCam.arm_traitlist[0].arm_traitpropslist[0].value_float = 5.0 #Speed
            #mainCam.arm_traitlist[0].arm_traitpropslist[0].value_float = 1.0 #Ease

            mainCam.data.lens = 25.0
            bpy.context.scene.camera = mainCam

            if scene.align_camera:
                bpy.ops.view3d.camera_to_view()

            bpy.data.cameras["Cam-BIM2ARM"].arm_frustum_culling = False
        
        #Setup sun
        if scene.setup_sun:
            bpy.ops.object.light_add(type='SUN', radius=1, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))

            if scene.world_type == "Dynamic":
                bpy.context.scene.objects["Sun"].rotation_euler = (0.69, 0, -0.52)
            if scene.world_type == "Sunrise":
                bpy.context.scene.objects["Sun"].rotation_euler = (1.57, -0.02, 0.96)
            if scene.world_type == "Sunny":
                bpy.context.scene.objects["Sun"].rotation_euler = (0.825, 0.0092, 0.96)
            if scene.world_type == "Cloudy":
                bpy.context.scene.objects["Sun"].rotation_euler = (0.53, -0.21, 0.855)

            bpy.data.lights["Sun"].energy = scene.sun_strength

        #Setup world
        if scene.world is None:

            new_world = bpy.data.worlds.new("BIM2ARM-Environment")
            scene.world = new_world

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
                if scene.world_type == "Snowy":
                    envFile = getAddonFolder() + "/environments/Snowy.hdr"
                if scene.world_type == "Snowy2":
                    envFile = getAddonFolder() + "/environments/Snowy2.hdr"
                if scene.world_type == "UrbanEvening":
                    envFile = getAddonFolder() + "/environments/UrbanEvening.hdr"

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
            rp.rp_supersampling = '2'
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

        scene.b2a_props.ifc_configured = True

        bpy.data.worlds["Arm"].arm_physics = 'Enabled'
        #Find a way to create LOD for physics
        #Collision mesh (Invisible) => Parent => Real mesh (Visible)

        #Mat Selector
        bpy.data.materials.new(name="B2A_SelectorMat")
        bpy.data.materials["B2A_SelectorMat"].use_nodes = True
        bpy.data.materials["B2A_SelectorMat"].use_fake_user = True
        bpy.data.materials["B2A_SelectorMat"].node_tree.nodes['Principled BSDF']
        bpy.data.materials["B2A_SelectorMat"].node_tree.nodes['Principled BSDF'].inputs.get("Base Color").default_value = (0,2,0,0)

        #Clean unused slots
        for obj in bpy.context.scene.objects:
            if obj.type == "MESH":
                bpy.context.view_layer.objects.active = obj
                print("Removing unused slots for: " + obj.name)
                bpy.ops.object.material_slot_remove_unused()

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
        row.prop(scene, "add_b2a_lib")
        
        row = box.row(align=True)
        row.prop(scene, "convert_materials")

        if scene.convert_materials:
            row = box.row(align=True)
            row.label(text="Material setup:")
            row = box.row(align=True)
            row.prop(scene, "material_setup")

        if scene.material_setup == "Replacement":
            row = box.row(align=True)
            row.operator("b2a.create_csv")
            row = box.row(align=True)
            row.label(text="Replacement schema:")
            row = box.row(align=True)
            row.prop(scene, "replacement_schema")
            row = box.row(align=True)
            row.label(text="Replacement library:")
            row = box.row(align=True)
            row.prop(scene, "replacement_file")

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
            row.prop(scene, "camera_speed")
            row = box.row(align=True)
            row.prop(scene, "camera_easing")

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

        if scene.ui_mode == "Advanced":
            box = layout.box()
            row = box.row(align=True)
            row.label(text="Lightmap objects", icon="FILE_CACHE")
            row = box.row(align=True)
            row.operator("b2a.lightmap")

        #Plan alignment tool
        if scene.ui_mode == "Advanced" and scene.b2a_props.storeys:
            box = layout.box()
            row = box.row(align=True)
            row.label(text="Drawing alignment tool", icon="FILE_CACHE")
            row = box.row(align=True)
            row.label(text="Select level:")
            row = box.row(align=True)
            row.prop(scene, "levels")
            row = box.row(align=True)
            row.label(text="Drawing file:") #drawing_type
            row = box.row(align=True)
            row.prop(scene, "levelPlan")
            row = box.row(align=True)
            row.label(text="File DPI:")
            row = box.row(align=True)
            row.prop(scene, "levelPlanDPI")
            row = box.row(align=True)
            row.label(text="File Scale:")
            row = box.row(align=True)
            row.prop(scene, "levelScale")
            row = box.row(align=True)

            row.label(text="Offset Drawing:")
            row = box.row(align=True)
            row.prop(scene, "offsetPlanX")
            row = box.row(align=True)
            row = box.row(align=True)
            row.prop(scene, "offsetPlanY")
            row = box.row(align=True)

            row.operator("b2a.import_plan")

            #for idx, storey in enumerate(scene.b2a_props.storeys):
                #row = box.row(align=True)
                #row.label(text=storey.name)
                #row.prop(scene, "storeys")
                #row.prop(scene, "storeys['" + str(idx) + "']")

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
        #if deployed == True:
        row = box.row(align=True)
        row.operator("b2a.explore")

        box = layout.box()
        row = box.row(align=True)
        row.label(text="Utilities", icon="FILE_CACHE")

def get_levels(self, context):

    items = []

    for lvl in bpy.context.scene.b2a_props.storeys:

        if lvl.name.startswith('IfcBuildingStorey'):

            name = lvl.name

            items.append((str(name), str(name),''))

    #items.pop(0) #Find a way to clean up characters w. unicode

    return items

classes = [SCENE_PT_B2A_panel, B2A_Prepare, B2A_Configure, B2A_Play, B2A_Deploy, B2A_LoadIFC, B2A_Explore, B2A_MakeLocal, B2A_LightmapObjects, B2A_CreateCSVTemplate, B2A_ImportPlan]

class Level_Props(bpy.types.PropertyGroup):
    levels: bpy.props.StringProperty()

classes.append(Level_Props)

def register():
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.b2a_props = B2A_Props

    bpy.types.Scene.ui_mode = EnumProperty(
        items = [('Easy', 'Easy', 'The UI is minimized to be as simple as possible'),
                 ('Advanced', 'Advanced', 'The UI exposes all available options, but can be more complex and time-consuming to setup')],
                name = "", description="UI mode for the addon", default='Easy')

    bpy.types.Scene.remove_aux_collections = bpy.props.BoolProperty(name="Remove Auxillary Collections", default=True, description="Remove the extra collections that are linked internally. Might break if not toggled or prepared manually")
    bpy.types.Scene.remove_annotations = bpy.props.BoolProperty(name="Remove annotations", default=True, description="Remove all 2D annotations from the file")
    bpy.types.Scene.remove_spaces = bpy.props.BoolProperty(name="Remove spaces", default=True, description="Remove all spaces from the file")
    bpy.types.Scene.add_physics = bpy.props.BoolProperty(name="Enable physics", default=False, description="Heavy, but required to select objects from 3D view")
    
    bpy.types.Scene.add_b2a_lib = bpy.props.BoolProperty(name="Add B2A Library", default=True, description="Add the BIM2ARM asset library")
    
    bpy.types.Scene.space_setup = EnumProperty(
        items = [('None', 'None', 'None'),
                 ('Spatial', 'Spatial Volumes', '')],
                name = "", description="Method for assigning IFC materials", default='None')
    
    bpy.types.Scene.remove_grids = bpy.props.BoolProperty(name="Remove grids", default=True, description="Remove all grids from the file")
    bpy.types.Scene.convert_materials = bpy.props.BoolProperty(name="Convert materials", default=True, description="Converts IFC materials")
    bpy.types.Scene.material_setup = EnumProperty(
        items = [('Grey', 'Conceptual', 'Default to grey material'),
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

    #Operator: Convert/Place PDF
    #Prop: DPI Settings

    #Operator: Create empty CSV file
    bpy.types.Scene.replacement_schema = StringProperty(name="", description="CSV schema describing which materials will be replaced", default="", subtype="FILE_PATH")
    bpy.types.Scene.replacement_file = StringProperty(name="", description="A blend file containing the materials that will be appended and used for replacement", default="", subtype="FILE_PATH")

    bpy.types.Scene.concept_setup = bpy.props.BoolProperty(name="Concept Setup", default=True, description="Setup for a conceptual model")

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

    bpy.types.Scene.levels = EnumProperty(items = get_levels, name="", description="")

    bpy.types.Scene.levelPlan = bpy.props.StringProperty(name="", description="An image file or PDF of your plan", default="", subtype="FILE_PATH")

    bpy.types.Scene.offsetPlanX = bpy.props.IntProperty(name="Offset X:", description="Offset the plan in the project x-direction", default=0)
    bpy.types.Scene.offsetPlanY = bpy.props.IntProperty(name="Offset Y:", description="Offset the plan in the project y-direction", default=0)

    bpy.types.Scene.schema_tool = EnumProperty(
        items = [('Window', 'Window', ''),
                 ('Door', 'Door', ''),
                 ('Walls', 'Walls', ''),
                 ('Rooms', 'Rooms', '')],
                name = "", description="Window tool", default='Window')
    
    bpy.types.Scene.levelScale = EnumProperty(
        items = [('a', '1:5', ''),
                 ('b', '1:10', ''),
                 ('c', '1:20', ''),
                 ('d', '1:50', ''),
                 ('e', '1:100', ''),
                 ('f', '1:200', '')],
                name = "", description="Plan scale", default='d')

    bpy.types.Scene.drawing_type = EnumProperty(
        items = [('Plan', 'Plan', ''),
                 ('Section', 'Section', '')],
                name = "", description="Drawing type - Plan: Horisontal or Section:Vertical", default='Plan')
    
    bpy.types.Scene.levelPlanDPI = EnumProperty(
        items = [('Low', 'Low', 'Low setting. Corresponds to 72 DPI in Revit'),
                 ('Medium', 'Medium', 'Medium setting. Corresponds to 150 DPI in Revit'),
                 ('High', 'High', 'High setting. Corresponds to 300 DPI in Revit'),
                 ('Presentation', 'Presentation', 'Presentation setting. Corresponds to 600 DPI in Revit'),
                 ('Custom', 'Custom', 'Set your own DPI')],
                name = "", description="DPI of the selected plan", default='High')

    # bpy.types.Scene.levelPlanDPI = EnumProperty(
    #         items = [('Low', 'Low', 'Low setting. Corresponds to 72 DPI in Revit'),
    #                 ('Medium', 'Medium', 'Medium setting. Corresponds to 150 DPI in Revit'),
    #                 ('High', 'High', 'High setting. Corresponds to 300 DPI in Revit'),
    #                 ('Presentation', 'Presentation setting. Corresponds to 600 DPI in Revit'),
    #                 ('Custom', 'Custom', 'Set your own DPI')],
    #                 name = "", description="DPI of the selected plan", default='High')

    print("Registering namespaces...")
    #bpy.app.driver_namespace['b2a_ifc_loaded'] = False
    #bpy.app.driver_namespace['b2a_ifc_configured'] = False
   #bpy.app.driver_namespace['b2a_ifc_prepared'] = False
    #bpy.app.driver_namespace['b2a_storeys'] = []
    #bpy.app.driver_namespace['b2a_deployed'] = False
    

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
- Group meshes by classes
'''
