"""
IFC Logic pack for B2A and Armory3D

https://github.com/Naxela/BBIM2ARM/
"""
import arm.logicnode
import arm.logicnode.arm_nodes as arm_nodes

import logicnode_definitions


def register():
    # Register a category for the logic node package
    arm_nodes.add_category(
        logicnode_definitions.CATEGORY_NAME,
        icon='DISK_DRIVE',
        description='IFC Logic nodes for BBIM2ARM (https://github.com/Naxela/BBIM2ARM/)'
    )

    # Then register all the nodes
    logicnode_definitions.register_all()