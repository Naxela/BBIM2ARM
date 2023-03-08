import bpy
from bpy.props import *
from bpy.types import Node, NodeSocket

from arm.logicnode.arm_nodes import *

class GetSpecificAttributeNode(ArmLogicTreeNode):
   """Get the value of the specific attribute if it exists"""
   bl_idname = 'LNGetSpecificAttributeNode'
   bl_label = 'Get Specific Attribute'

   arm_category = 'IFC'
   arm_section = 'get'
   arm_version = 1

   def arm_init(self, context):
       self.add_input('ArmNodeSocketObject', 'Object')
       self.add_input('ArmStringSocket', 'Attribute')
       self.add_output('ArmStringSocket', 'Value')