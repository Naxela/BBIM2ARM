import bpy
from bpy.props import *
from bpy.types import Node, NodeSocket

from arm.logicnode.arm_nodes import *

class GetObjectsByAttributeNode(ArmLogicTreeNode):
   """Get the objects which has the specific attribute and value. If value is empty, it will return all that has the property."""
   bl_idname = 'LNGetObjectsByAttributeNode'
   bl_label = 'Get Objects by Attribute'

   arm_category = 'IFC'
   arm_section = 'get'
   arm_version = 1

   def arm_init(self, context):
       self.add_input('ArmStringSocket', 'Attribute')
       self.add_input('ArmStringSocket', 'Value')
       self.add_output('ArmNodeSocketArray', 'Object Array')