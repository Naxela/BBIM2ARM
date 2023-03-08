import bpy
from bpy.props import *
from bpy.types import Node, NodeSocket

from arm.logicnode.arm_nodes import *

class GetAvailablePropertiesNode(ArmLogicTreeNode):
   """Get all the available IFC properties from either object or all"""
   bl_idname = 'LNGetAvailablePropertiesNode'
   bl_label = 'Get Available Properties'

   arm_category = 'IFC'
   arm_section = 'get'
   arm_version = 1

   def arm_init(self, context):
       self.add_input('ArmNodeSocketObject', 'Object')
       self.add_output('ArmNodeSocketArray', 'Property Array')