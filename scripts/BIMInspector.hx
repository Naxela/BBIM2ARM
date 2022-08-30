package arm;

import zui.*;
import iron.object.Object;
import iron.math.Vec4;

@:access(zui.Zui)
@:access(armory.logicnode.LogicNode)

class BIMInspector extends iron.Trait {

    var ui:Zui; //The UI Class instance
    var focusedObj: Object; //The object which is currently selected in the list
	var selectedObject: iron.object.Object;

	var content:haxe.DynamicAccess<Dynamic>; //Holder for dynamic property information

	var mouse = iron.system.Input.getMouse(); //Get the mouse input

	var physics = armory.trait.physics.PhysicsWorld.active; //Get the rigid body physics controller

	var inspectorWindow = Id.handle();
	var windowTab = Id.handle();
	var modelTreePanel = Id.handle();
	var propertiesPanel = Id.handle();

	var hwin = Id.handle();
	var htab = Id.handle();
	var mtab = Id.handle();
	var ptab = Id.handle();
	var subtab = Id.handle();

	public function new() {
		super();

        // Load font for UI labels - We need a font that supports unicode
        iron.data.Data.getFont("arial.ttf", function(f:kha.Font) {
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
		if (ui.window(inspectorWindow, 0, 0, 400, iron.App.h(), false)) { //Handle, x-pos, y-pos, width, height, dragable
		
			//Make the model tree tab
			if (ui.tab(windowTab, "BIM2ARM")) { //Handle, name
			
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

							ui.text(index + ": " + key);

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
		
		}

      	ui.end(); //End the UI Module

        g.begin(false);

		inspectorWindow.redraws = 1; //Keep updating it
	
	}

	//Deflate objects
	function deflateObject(object){
		var iteratorAccess:haxe.DynamicAccess<Dynamic> = object;

		for (idx => key in iteratorAccess) {
			if (Std.is(key, String)) {
				ui.text(idx + ": " + key);
			} else {
				deflateObject(key);
			}
		}
	}


	//3D Scene access at runtime
	function update(){

	}

	//Select the object from the list ?? OR Scene RB?
	function selectObject(obj: iron.object.Object) {

		focusedObj = obj;
		
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

				var empty_data = '{"Name":"' + obj.name + '", "Data":"Unavailable"}';
				content = haxe.Json.parse(empty_data);

			}

		} else {

			var empty_data = '{"Name":"' + obj.name + '", "Data":"Unavailable"}';
			content = haxe.Json.parse(empty_data);

		}

		//trace(content);

	}

}
