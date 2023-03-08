package armory.logicnode;

import iron.object.Object;

class GetSpecificPropertyNode extends LogicNode {

	var content:haxe.DynamicAccess<Dynamic>;
	var propertyValue:String;

	public function new(tree:LogicTree) {
		super(tree);
	}

	override function get(from:Int):Dynamic {

		var object:Object = inputs[0].get();
		var property:String = inputs[1].get();

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

				if(!Std.is(key, String)){

					var iteratorAccess:haxe.DynamicAccess<Dynamic> = key;

					for (idy => subkey in iteratorAccess) {

						if(subkey.Name == property){

							propertyValue = subkey.NominalValue;

						}
					
					}

				}

			}

		}

		return propertyValue;
	}
}
