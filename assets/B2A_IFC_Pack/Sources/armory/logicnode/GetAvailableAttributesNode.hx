package armory.logicnode;

import iron.object.Object;

class GetAvailableAttributesNode extends LogicNode {

	var content:haxe.DynamicAccess<Dynamic>;
	var parameterList:Array<String> = [];
	var globalList:Array<String> = [];

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

		var selfObject:Object = tree.object;
		var object:Object = inputs[0].get();

		if(object.name == "root" || object.name == selfObject.name){

			iterateChildren(iron.Scene.active.root);

			for(objname in globalList){
			
				var obj = iron.Scene.active.getChild(objname);

				if(obj.properties != null){

					var propertyList = obj.properties.get("BIMDATA");

					if (propertyList) {
	
						content = haxe.Json.parse(propertyList);
	
					} else {
	
						var empty_data = '{"Name":"' + obj.name + '", "Data":"Unavailable 1"}';
						content = haxe.Json.parse(empty_data);
	
					}
	
					for(index => key in content){

						if(Std.is(key, String)){

							if(parameterList.contains(index)){
								//Pass
							} else {
								parameterList.push(index);
							}
	
						}
	
					}

				}
			
			}

		} else {

			if(object.properties != null){

				var propertyList = object.properties.get("BIMDATA");

				if(propertyList){

					content = haxe.Json.parse(propertyList);

				} else {

					var empty_data = '{"Name":"' + object.name + '", "Data":"Unavailable 1"}';
					content = haxe.Json.parse(empty_data);

				}

				for(index => key in content){
					if(Std.is(key, String)){

						parameterList.push(index);

					}
				}

			} else {
				trace("ERROR: PROPERTIES ARE NULL");
			}

		}

		return parameterList;
	}
}
