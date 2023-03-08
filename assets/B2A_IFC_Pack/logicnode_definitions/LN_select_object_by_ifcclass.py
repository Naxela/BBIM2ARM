import bpy
from bpy.props import *
from bpy.types import Node, NodeSocket

from arm.logicnode.arm_nodes import *

class GetObjectsByIFCClassNode(ArmLogicTreeNode):
   """Get the objects which has the specific IFC class."""
   bl_idname = 'LNGetObjectsByIFCClassNode'
   bl_label = 'Get Objects by IFC Class'

   arm_category = 'IFC'
   arm_section = 'get'
   arm_version = 1

   def arm_init(self, context):
       self.add_input('ArmStringSocket', 'IFC Class')
       self.add_output('ArmNodeSocketArray', 'Object Array')