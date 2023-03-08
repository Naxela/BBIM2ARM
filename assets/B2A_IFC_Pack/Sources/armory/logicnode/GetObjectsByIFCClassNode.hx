package armory.logicnode;

import iron.object.Object;

class GetObjectsByIFCClassNode extends LogicNode {

	var retObjects:Array<iron.object.Object> = [];
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

		var IfcClass:String = inputs[0].get();

		iterateChildren(iron.Scene.active.root);

		for(objname in globalList){
			
			var obj = iron.Scene.active.getChild(objname);

			if(obj.properties != null){

				var propClass = obj.properties.get("IFCCLASS");

				if(IfcClass == propClass){

					retObjects.push(obj);

				}

			}
		}

		return retObjects;

	}
}
