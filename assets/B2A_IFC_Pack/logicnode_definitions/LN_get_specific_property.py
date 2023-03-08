import bpy
from bpy.props import *
from bpy.types import Node, NodeSocket

from arm.logicnode.arm_nodes import *

class GetSpecificPropertyNode(ArmLogicTreeNode):
   """Get the value of the specific property if it exists"""
   bl_idname = 'LNGetSpecificPropertyNode'
   bl_label = 'Get Specific Property'

   arm_category = 'IFC'
   arm_section = 'get'
   arm_version = 1

   def arm_init(self, context):
       self.add_input('ArmNodeSocketObject', 'Object')
       self.add_input('ArmStringSocket', 'Property')
       self.add_output('ArmStringSocket', 'Value')