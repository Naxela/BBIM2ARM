package armory.logicnode;

import iron.object.Object;

class GetObjectByGUIDNode extends LogicNode {

	var content:haxe.DynamicAccess<Dynamic>;
	var globalList:Array<String> = [];
	var guidObject:iron.object.Object;

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

		var GUID:String = inputs[0].get();

		iterateChildren(iron.Scene.active.root);

		for(objname in globalList){
			
			var obj = iron.Scene.active.getChild(objname);

			if(obj.properties != null){

				var propertyList = obj.properties.get("BIMDATA");

				if (propertyList) {

					content = haxe.Json.parse(propertyList);

					for(index => key in content){

						if(Std.is(key, String)){

							if(index == "GlobalId" || index == "GUID"){

								if(key == GUID){
									guidObject = obj;
								}
							}
						}
					}
				}
			}
		}

		return guidObject;

	}
}
