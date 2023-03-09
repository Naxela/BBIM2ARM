package arm;

using StringTools;

import zui.*;
import iron.object.Object;
import iron.math.Vec4;
import iron.object.MeshObject;
import iron.data.MaterialData;
import armory.trait.physics.RigidBody;
import armory.trait.physics.bullet.RigidBody.Shape;

@:access(zui.Zui)
@:access(armory.logicnode.LogicNode)

class BIMInspector extends iron.Trait {

    var ui:Zui; //The UI Class instance
    var focusedObj: Object = null; //The object which is currently selected in the list
	var selectedObject: iron.object.Object;

	var content:haxe.DynamicAccess<Dynamic>; //Holder for dynamic property information

	var mouse = iron.system.Input.getMouse(); //Get the mouse input

	var physics = armory.trait.physics.PhysicsWorld.active; //Get the rigid body physics controller
	var hideLoc:Map<String, iron.math.Vec4> = new Map();


	var archIfcClasses = [''];
	var mepIfcClasses = [''];
	var structuralIfcClasses = [''];

	var inspectorWindow = Id.handle();
	var windowTab = Id.handle();
	var modelTreePanel = Id.handle();
	var propertiesPanel = Id.handle();
	var prevMaterials = [];

	var hwin = Id.handle();
	var htab = Id.handle();
	var mtab = Id.handle();
	var ptab = Id.handle();
	var subtab = Id.handle();

	public function new() {
		super();

        // Load font for UI labels - We need a font that supports unicode
		//arial.ttf
        iron.data.Data.getFont("font_default.ttf", function(f:kha.Font) {
            ui = new Zui({font: f});
            iron.Scene.active.notifyOnInit(sceneInit);
        });

	}

	//On scene init, execute subfunctions
	function sceneInit() {
		notifyOnRender2D(render2D); //Render 2D View
		notifyOnUpdate(update); //Manipulate 3D Elements
	}

	//2D access at runtime
	function render2D(g:kha.graphics2.Graphics) { //g as the 2D graphics module
	
		g.end(); //End any unclosed g-modules?

		ui.begin(g); //Begin drawing the zui class with the g-module

		//Make window
		if (ui.window(inspectorWindow, 10, 20, 400, iron.App.h() - 45, false)) { //Handle, x-pos, y-pos, width, height, dragable
		
			//Make the model tree tab
			if (ui.tab(windowTab, "Model Hierarchy")) { //Handle, name
			
				//Make a model tree panel
				if (ui.panel(modelTreePanel, "Model Tree")) {
				
					var lineCounter = 0; //Count lines

					var b = false; //????

					function drawList(listHandle: zui.Zui.Handle, listObject: iron.object.Object) { //Draw a UI list
				
						//If the list object has a dot prefix, it becomes hidden
						if (listObject.name.charAt(0) == ".") return; // Hidden

						//If the list object is a light object, it becomes hidden
						if (Std.isOfType(listObject, iron.object.LightObject)) return; // Hidden

						//If the list object is a camera object, it becomes hidden
						if (Std.isOfType(listObject, iron.object.CameraObject)) return; // Hidden

						//If the list object is selected / in focus it get's a different color
						if (listObject == focusedObj) {
							ui.g.color = 0xff205d9c;
							ui.g.fillRect(0, ui._y, ui._windowW, ui.ELEMENT_H());
							ui.g.color = 0xffffffff;
						}

						//If the list object has sub-objects, we create more panel lines
						if (listObject.children.length > 0) {

							if (listObject.name == "Scene") {

								ui.row([1 / 13, 12 / 13]);
								b = ui.panel(listHandle.nest(lineCounter, {selected: true}), "", true, false, false); //Handle, name, isTree, filled, pack
								ui.text("Model Hierarchy");

							}

						} else { //If it doesn't have sub-objects

							ui._x += 18; // Sign offset

							ui.g.color = ui.t.ACCENT_COL;
							ui.g.drawLine(ui._x - 10, ui._y + ui.ELEMENT_H() / 2, ui._x, ui._y + ui.ELEMENT_H() / 2);
							ui.g.color = 0xffffffff;

							//ui.text(currentObject.name);

							//ui.text(listObject.name);
							var postfix = ' []';
							if(!listObject.visible){
								var postfix = " [H]";
							} else {
								var postfix = " [Hx]";
							}

							if(StringTools.contains(listObject.name, "/")){
								var ifcClass = (listObject.name).split("/")[0];
								var ifcName = (listObject.name).split("/")[1];
	
								if(ifcName == ""){
									ui.text(ifcClass);
								} else {
									ui.text(ifcName);
								}
							} else {

								ui.text(listObject.name);

							}

							ui._x -= 18;

						}

						lineCounter++;

						ui._y -= ui.ELEMENT_OFFSET();

						if (ui.isReleased) {
							trace("Clicked: " + listObject.name); //This needs to be the object, maybe the mesh get's selected?
							selectObject(listObject);
						}


						if (b) {
							var currentY = ui._y;
							for (child in listObject.children) {
								ui.indent();
								drawList(listHandle, child);
								ui.unindent();
							}

							// Draw line that shows parent relations
							ui.g.color = ui.t.ACCENT_COL;
							//ui.g.drawLine(ui._x + 14, currentY, ui._x + 14, ui._y - ui.ELEMENT_H() / 2);
							ui.g.color = 0xffffffff;
						}

					}

					for (c in iron.Scene.active.root.children) {
						drawList(Id.handle(), c);
					}

					ui.unindent();

				}

				//Make a properties panel
				if (ui.panel(propertiesPanel, 'Properties')) {

					ui.indent();

					var panelId = 0;

					for(index => key in content){

						if (Std.is(key, String)) {

							if(StringTools.contains(key, "/")){
								var ifcClass = (key).split("/")[0];
								var ifcName = (key).split("/")[1];

								ui.text("IFC Class: " + ifcClass);
								ui.text("Name: " + ifcName);
	
								if(ifcName == ""){
									//ui.text(ifcClass);
								} else {
									//ui.text(ifcName);
								}
							}

							//ui.text(index + ": " + key);

						} else {

							if(ui.panel(Id.handle().nest(panelId), index)){
								//ui.text(index);
								deflateObject(key);
							}

						}

						panelId = panelId + 1;

					}

					//First level content/non-array items
					// for (idx => key in content.keys()){
					// 	if(Std.is(content.get(key), String)){
					// 		ui.text(key + ": " + content.get(key));
					// 	}
					// }


					//Second level content/non-array items
					// for (idx => key in content.keys()){
					// 	if(!Std.is(content.get(key), String)){
							
					// 		if(ui.panel(Id.handle().nest(idx), key)){

								
					// 			ui.text("Sublevel");
					// 			ui.text(content);
					// 			//ui.text(key);




					// 		}
	
					// 	}
					// }


					
				}
			
			}

			if (ui.tab(windowTab, "Discipline View")) {

				if (ui.panel(modelTreePanel, "View Toggle")) {

					var archview = ui.check(Id.handle({selected:true}), "Architecture");
					var mepview = ui.check(Id.handle({selected:true}), "MEP");
					var structureview = ui.check(Id.handle({selected:true}), "Structure");

				}

			}

			if (ui.tab(windowTab, "Options")) {

				if (ui.panel(modelTreePanel, "Shortcuts")) {

					ui.text('Foward: W');
					ui.text('Backward: S');
					ui.text('Left: A');
					ui.text('Right: D');
					ui.text('Elevation Up: E');
					ui.text('Elevation Down: Q');
					ui.text('Sprint: Shift');
					ui.text('Adjust Speed: Middle Mouse');

					ui.text('Hide Toggle: H');
					ui.text('Unhide All: Alt + H');

					ui.text('Translate Tool: 1');
					ui.text('Rotate Tool: 2');
					ui.text('Scale Tool: 3');

					ui.text('Markup: 4');
					ui.text('Dimension: 5');
					ui.text('Sectioning: 6');

					ui.text('Perspective/Orthogonal: 7');
					ui.text('Front-View: 8');
					ui.text('Left-View: 9');
					ui.text('Top-View: 0');

				}

			}

		
		}

      	ui.end(); //End the UI Module

        g.begin(false);

		inspectorWindow.redraws = 1; //Keep updating it
	
	}

	//Deflate objects
	function deflateObject(object){
		var iteratorAccess:haxe.DynamicAccess<Dynamic> = object;
		var header = "";
		var value:String = "";

		// for (idx => key in iteratorAccess) {
		// 	if (Std.is(key, String)) {
		// 		ui.text(idx + ": " + key);
		// 	} else {
		// 		deflateObject(key);
		// 	}
		// }
		for (idx => key in iteratorAccess) {

			//trace(idx + " | " + key);

			header = key.Name;
			//var value = key.NominalValue;
			var valueAccess:haxe.DynamicAccess<Dynamic> = key.NominalValue;

			if(haxe.Json.stringify(valueAccess).charAt(0) == "{"){

				//TODO: CHECK AT A DEEPER LEVEL
				//TODO: MAKE THIS RECURSIVE

				// var indexkeys = [];

				// for (idy => subkey in valueAccess) {
				// 	indexkeys.push(idy + ": " + subkey);
				// }

				// //trace("{ is first character: OBJECT");
				// //ui.text(header + ": " + haxe.Json.stringify(valueAccess));
				// ui.text(header + ": ");

				// for(index in indexkeys){
				// 	ui.text("        " + index);
				// }
				ui.text(header + ": " + haxe.Json.stringify(valueAccess));

			} else {
				//trace("STRING");
				ui.text(header + ": " + valueAccess);
			}

			//var vx = haxe.Json.stringify(valueAccess);

			// for (n in Reflect.fields(valueAccess))
			// 	trace(Reflect.field(valueAccess, n));
			//var gString = haxe.Json.parse(valueAccess);
			//trace(gString);

			// for (idy => subkey in iteratorAccess) {



			// }


			// if(Std.is(value, String)){

			// 	//pass

			// } else {

			// 	value = "OBJECT!";

			// }

			//trace(key.Name);
			//trace(key.NominalValue);
			//ui.text(idx + "[A]:[B] " + key);
			
			//THIS WAS COMMENTED
			//ui.text(header + ": " + value);

			//key should contain both name and value


			//idx is always a string

			// if(StringTools.startsWith(key,"{")){
			// 	trace("ABCD");
			// } else {
			// 	trace("EFG");
			// }

			// if( StringTools.startsWith(key, "{") ){
			// 	var keyAccess = haxe.Json.parse(key);
			// 	ui.text(idx + "[A]:[B] " + keyAccess.Name);
			// } else {
			// 	ui.text(idx + "[A]:[B] " + key);
			// }


			// //value['NominalValue']

			// if (Std.is(key, String)) {

			// 	if(idx == "Name"){
			// 		header = key;
			// 	}
			// 	if(idx == "NominalValue"){
			// 		value = key;
			// 	}

			// } else {

			// 	//value = "[OBJECT]";

			// 	value = key[0];

			// 	deflateObject(key);

			// }

			// if(header != ""){

			// 	if(value != ""){

			// 		if(Std.is(value, String)){

			// 			ui.text(header + ": " + value);

			// 		} else {

			// 			//Check if it exists first?
			// 			//ui.text(header + ": " + value);
			// 			ui.text(header + ": " + value);

			// 		}

			// 	} else {

			// 		//SKIP THIS
			// 		value = "??? SKIP";

			// 		if(Std.is(value, String)){

			// 			ui.text(header + ": " + value);

			// 		} else {

			// 			//Check if it exists first?
			// 			ui.text(header + ": " + value);
						
			// 		}

			// 	}

			// }

			// if (Std.is(key, String)) {
			// 	if(idx == "Name"){
			// 		header = key;
			// 	}
			// 	if(idx == "NominalValue"){
			// 		value = key;
			// 	}
			// 	//ui.text("[STRING]");
			// 	ui.text(header + ": " + value);
			// } else {
			// 	ui.text(header + ": " + value);
			// 	ui.text("[DEFLATE]------------------");
			// 	deflateObject(key);
			// }
		}

		//ui.text(header + ": " + value);


	}


	//3D Scene access at runtime
	function update(){

		var physics = armory.trait.physics.PhysicsWorld.active;
		var mouse = iron.system.Input.getMouse();
		var keyboard = iron.system.Input.getKeyboard();
		var clickEvent = false;

		if(mouse.released('left')){
			//trace(mouse.x);
			//trace(mouse.y);

			var rb = physics.pickClosest(mouse.x, mouse.y, 1);

			if(rb != null){
				var rbobject = cast(rb.object, iron.object.Object);
				//trace(rbobject.name);
				selectObject(rbobject);
				//rbobject.visible = false;
			} else {
				if(focusedObj != null){
					if (Std.isOfType(focusedObj, iron.object.MeshObject)) {
						var exmesh = cast(focusedObj, iron.object.MeshObject);
						var exmatLen = exmesh.materials.length;
		
						for(i in 0...exmatLen){
							exmesh.materials[i] = prevMaterials[i];
						}
		
					}
				}
				focusedObj = null;
			}
			//trace(rb.object.name);
		}

		if(keyboard.down('alt')){


			if(keyboard.started('h')){
				for (c in iron.Scene.active.root.children) {

					if (c.children.length > 0) {
	
						for(b in c.children){

							//trace(b.name);
							b.visible = true;

							if(hideLoc[b.name] != null){
								b.transform.loc.setFrom(hideLoc[b.name]);
								b.transform.buildMatrix();
								var rigidBody = b.getTrait(RigidBody);
								if (rigidBody != null) rigidBody.syncTransform();
								hideLoc[b.name] = null;
								focusedObj.visible = true;
							}

							//var shape:Shape = Mesh;
							//var rb = new RigidBody(shape, 1.0, 0.5, 0.0, 1, 1);
							//rb.staticObj = false;
							//focusedObj.addTrait(rb);
						}

					}
				}
			}

			// if(keyboard.started('h')){

			// 	for (c in iron.Scene.active.root.children) {
			// 		c.visible = true;
			// 	}

			// }
		} else {
			if(keyboard.started('h')){

				if(focusedObj != null){
					if(hideLoc[focusedObj.name] == null){
						hideLoc[focusedObj.name] = focusedObj.transform.world.getLoc();
						var Distvec:Vec4 = new iron.math.Vec4(9999,9999,9999,9999);
						focusedObj.transform.loc.setFrom(Distvec);
						focusedObj.transform.buildMatrix();
						var rigidBody = focusedObj.getTrait(RigidBody);
						if (rigidBody != null) rigidBody.syncTransform();
						focusedObj.visible = false;
					} else {
						//hideLoc[focusedObj.name] = focusedObj.transform.world.getLoc();
						//var Distvec:Vec4 = new iron.math.Vec4(9999,9999,9999,9999);
						focusedObj.transform.loc.setFrom(hideLoc[focusedObj.name]);
						focusedObj.transform.buildMatrix();
						var rigidBody = focusedObj.getTrait(RigidBody);
						if (rigidBody != null) rigidBody.syncTransform();
						hideLoc[focusedObj.name] = null;
						focusedObj.visible = true;
					}
				}

				//if(focusedObj != null){
					//if(focusedObj.visible){

						//focusedObj.visible = false;

						//var rb = focusedObj.getTrait(RigidBody);
						// if(rbmap[focusedObj.name] == null){
						// 	rbmap[focusedObj.name] = rb;
						// }
						
						//rb.remove();
						//if(rb != null){
						//	focusedObj.removeTrait(rb);
						//}
						
					//} else {
						//focusedObj.visible = true;

						//if(rbmap[focusedObj.name] != null){
						//trace(rbmap[focusedObj.name]);
						//focusedObj.addTrait(rbmap[focusedObj.name]);
						//var shape:Shape = Mesh;
						//var rb = new RigidBody(shape, 1.0, 0.5, 0.0, 1, 1);
						//rb.staticObj = true;
						//focusedObj.addTrait(rb);
					//}
				//}

			}
		}



		//Press hide => Hide/Unhide selected
		//if()


	}

	//Select the object from the list ?? OR Scene RB?
	function selectObject(obj: iron.object.Object) {

		//If focused object is set, reset materials:
		if(focusedObj != null){
			if (Std.isOfType(focusedObj, iron.object.MeshObject)) {
				var exmesh = cast(focusedObj, iron.object.MeshObject);
				var exmatLen = exmesh.materials.length;

				for(i in 0...exmatLen){
					exmesh.materials[i] = prevMaterials[i];
				}

			}
		}

		focusedObj = obj;

		//1. If existing focused obj, set material back

		//2. Store all material slots

		//3. Set all material slots to green
		//if (object.materials.length != 0) {
		//	for (slot in object.materials.length){
		//		trace(object.materials[slot].name);
		//	}
		//}
		if (Std.isOfType(obj, iron.object.MeshObject)) {
			var mesh = cast(obj, iron.object.MeshObject);
			var matLen = mesh.materials.length;
			var selectorMat = null;
			iron.data.Data.getMaterial(iron.Scene.active.raw.name, 'B2A_SelectorMat', function(mat: MaterialData) {
				selectorMat = mat;
			});

			//trace(mesh.materials.length);

			for(i in 0...matLen){
				//trace(mesh.materials[i].name);
				prevMaterials[i] = mesh.materials[i];
				mesh.materials[i] = selectorMat;
			}

			//if (mesh != null){
			//	if (mesh.materials.length != 0) {
			//		for (slot in mesh.materials.length){
			//			trace(mesh.materials[slot].name);
			//		}
			//	}
			//}

			//var slot = 0;
			
			//if (mesh != null) trace("NO MESH!");
			
			//trace(mesh.materials[slot].name);
		}
		//trace(obj.materials);
		
		trace("Reading properties for: " + obj.name);

		//TODO!: EMPTIES CAUSES ERROR + The big main object

		//If the object does have properties
		if(obj.properties != null) {

			//Get the property list
			var propertyList = obj.properties.get("BIMDATA");

			//If the property list isn't empty
			if (propertyList) {

				//Content <Dynamic> is parsed from json properties
				content = haxe.Json.parse(propertyList);

			} else {

				var empty_data = '{"Name":"' + obj.name + '", "Data":"Unavailable 1"}';
				content = haxe.Json.parse(empty_data);

			}

		} else {

			var empty_data = '{"Name":"' + obj.name + '", "Data":"Unavailable 2"}';
			content = haxe.Json.parse(empty_data);

		}

		//trace(content);

	}

}