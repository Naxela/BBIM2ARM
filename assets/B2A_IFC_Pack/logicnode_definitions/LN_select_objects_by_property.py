import bpy
from bpy.props import *
from bpy.types import Node, NodeSocket

from arm.logicnode.arm_nodes import *

class GetObjectsByPropertyNode(ArmLogicTreeNode):
   """Get the objects which has the specific property and value. If value is empty, it will return all that has the property."""
   bl_idname = 'LNGetObjectsByPropertyNode'
   bl_label = 'Get Objects by Property'

   arm_category = 'IFC'
   arm_section = 'get'
   arm_version = 1

   def arm_init(self, context):
       self.add_input('ArmStringSocket', 'Property')
       self.add_input('ArmStringSocket', 'Value')
       self.add_output('ArmNodeSocketArray', 'Object Array')