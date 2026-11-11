"""Publish a description and start the mock ROS 2 control systems."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import xacro


ROBOT_DEFAULTS = {
    'robot_model': 'kr30_r2100', 'separation': '4.0', 'track_length': '6.4',
    'track_width': '0.4', 'track_height': '0.2', 'carrier_length': '0.4',
    'carrier_width': '0.4', 'carrier_height': '0.4', 'travel': '6.0',
}


def launch_nodes(context):
    control_share = Path(get_package_share_directory('preentend_ros2_control'))
    description = LaunchConfiguration('robot_description').perform(context)
    if not description:
        mappings = {name: LaunchConfiguration(name).perform(context) for name in ROBOT_DEFAULTS}
        mappings['control_backend'] = 'mock'
        description = xacro.process_file(
            str(control_share / 'robot/preentend_ros2_control.urdf.xacro'),
            mappings=mappings,
        ).toxml()
    controllers_file = str(control_share / 'config/ros2_controllers.yaml')
    return [
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': description}], output='screen'),
        Node(package='controller_manager', executable='ros2_control_node',
             parameters=[controllers_file], output='screen'),
        Node(package='controller_manager', executable='spawner',
             arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
             output='screen'),
        Node(package='controller_manager', executable='spawner',
             arguments=['robot_1_controller', 'robot_2_controller', 'robots_controller',
                        '--inactive', '--controller-manager', '/controller_manager'],
             output='screen'),
    ]


def generate_launch_description():
    arguments = [DeclareLaunchArgument(name, default_value=value)
                 for name, value in ROBOT_DEFAULTS.items()]
    return LaunchDescription(arguments + [
        DeclareLaunchArgument('robot_description', default_value='',
                              description='Optional already-expanded robot description.'),
        OpaqueFunction(function=launch_nodes),
    ])
