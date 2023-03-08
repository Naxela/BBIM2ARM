package armory.logicnode;

import iron.object.Object;

class GetObjectsByAttributeNode extends LogicNode {

	var content:haxe.DynamicAccess<Dynamic>;
	var parameterList:Array<String> = [];
	var globalList:Array<String> = [];
	var retObjects:Array<iron.object.Object> = [];

	public function new(tree:LogicTree) {
		super(tree);
	}

	public function iterateChildren(parent:iron.object.Object) {

		if(parent.children.length > 0){
			for(child in parent.children){
				iterateChildren(child);
			}
		} else {

			if (parent.name.charAt(0) == ".") {
				//Pass
			} else if (Std.isOfType(parent, iron.object.LightObject)){
				//Pass
			} else if (Std.isOfType(parent, iron.object.CameraObject)){
				//Pass
			} else {
				globalList.push(parent.name);
			}
			
		}
	};

	override function get(from:Int):Dynamic {

		var attribute:String = inputs[0].get();
		var value:String = inputs[1].get();

		iterateChildren(iron.Scene.active.root);

		for(objname in globalList){
		
			var obj = iron.Scene.active.getChild(objname);

			if(obj.properties != null){
			
				var propertyList = obj.properties.get("BIMDATA");

				if (propertyList) {
	
					content = haxe.Json.parse(propertyList);

					for(index => key in content){ //For each parameter

						if(Std.is(key, String)){
							//It is an attribute

							if(index == attribute){ //If the attribute exists

								if(value == ""){ //The attribute value is optional, only need the attribute

									//trace("Attribute type found");

									retObjects.push(obj);

								} else { //Only return object is a value fits

									if(key == value){

										//trace("Attribute type and value found");

										retObjects.push(obj);

									}

								}

							}
	
						}
	
					}

				}
			
			}
		
		}

		return retObjects;
	}
}
