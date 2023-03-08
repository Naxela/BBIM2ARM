import bpy
from bpy.props import *
from bpy.types import Node, NodeSocket

from arm.logicnode.arm_nodes import *

class GetAvailableAttributesNode(ArmLogicTreeNode):
   """Get all the available IFC attributes from either object or all"""
   bl_idname = 'LNGetAvailableAttributesNode'
   bl_label = 'Get Available Attributes'

   arm_category = 'IFC'
   arm_section = 'get'
   arm_version = 1

   def arm_init(self, context):
       self.add_input('ArmNodeSocketObject', 'Object')
       self.add_output('ArmNodeSocketArray', 'Attribute Array')