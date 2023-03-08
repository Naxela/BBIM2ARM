import bpy
from bpy.props import *
from bpy.types import Node, NodeSocket

from arm.logicnode.arm_nodes import *

class GetObjectByGUIDNode(ArmLogicTreeNode):
   """Get the object which has the specific GUID."""
   bl_idname = 'LNGetObjectByGUIDNode'
   bl_label = 'Get Object by GUID'

   arm_category = 'IFC'
   arm_section = 'get'
   arm_version = 1

   def arm_init(self, context):
       self.add_input('ArmStringSocket', 'GUID')
       self.add_output('ArmNodeSocketObject', 'Object')