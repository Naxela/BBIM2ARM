package armory.logicnode;

import iron.object.Object;

class GetSpecificAttributeNode extends LogicNode {

	var content:haxe.DynamicAccess<Dynamic>;
	var attributeValue:String;

	public function new(tree:LogicTree) {
		super(tree);
	}

	override function get(from:Int):Dynamic {

		var object:Object = inputs[0].get();
		var attribute:String = inputs[1].get();

		var obj = object;

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

					//trace(index + " : " + key);

					if(index == attribute){

						attributeValue = key;

					}

				}

			}

		}

		return attributeValue;
	}
}
