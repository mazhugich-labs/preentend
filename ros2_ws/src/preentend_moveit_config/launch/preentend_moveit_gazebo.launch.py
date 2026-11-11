"""Start MoveIt with the Gazebo simulation."""

from preentend_moveit_config.launch_common import generate_moveit_launch_description


def generate_launch_description():
    return generate_moveit_launch_description('gazebo')
