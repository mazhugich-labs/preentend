"""Start Gazebo Sim and spawn the complete, ROS 2 controlled robot."""

import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory, get_packages_with_prefixes
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import xacro


ROBOT_DEFAULTS = {
    'robot_model': 'kr30_r2100', 'separation': '4.0', 'track_length': '6.4',
    'track_width': '0.4', 'track_height': '0.2', 'carrier_length': '0.4',
    'carrier_width': '0.4', 'carrier_height': '0.4', 'travel': '6.0',
}


def launch_nodes(context):
    gazebo_share = Path(get_package_share_directory('preentend_gazebo'))
    mappings = {name: LaunchConfiguration(name).perform(context) for name in ROBOT_DEFAULTS}
    mappings['control_backend'] = 'gazebo'
    description = LaunchConfiguration('robot_description').perform(context)
    if not description:
        description = xacro.process_file(
            str(gazebo_share / 'robot/preentend_gazebo.urdf.xacro'), mappings=mappings,
        ).toxml()
    # Gazebo resolves package:// meshes relative to the parent of each package share.
    paths = sorted({str(Path(prefix) / 'share') for prefix in get_packages_with_prefixes().values()})
    resource_path = os.pathsep.join(filter(None, [os.environ.get('GZ_SIM_RESOURCE_PATH', ''), *paths]))
    gz_launch = Path(get_package_share_directory('ros_gz_sim')) / 'launch/gz_sim.launch.py'
    return [
        SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', resource_path),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(gz_launch)),
            launch_arguments={'gz_args': LaunchConfiguration('gz_args')}.items(),
        ),
        Node(package='ros_gz_bridge', executable='parameter_bridge',
             parameters=[{'config_file': str(gazebo_share / 'config/bridge.yaml'),
                          'use_sim_time': True}], output='screen'),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': description, 'use_sim_time': True}], output='screen'),
        Node(package='ros_gz_sim', executable='create',
             arguments=['-name', 'preentend', '-topic', 'robot_description'], output='screen'),
        Node(package='controller_manager', executable='spawner',
             arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
             parameters=[{'use_sim_time': True}], output='screen'),
        Node(package='controller_manager', executable='spawner',
             arguments=['robot_1_controller', 'robot_2_controller', 'robots_controller',
                        '--inactive', '--controller-manager', '/controller_manager'],
             parameters=[{'use_sim_time': True}], output='screen'),
    ]


def generate_launch_description():
    return LaunchDescription(
        [DeclareLaunchArgument(name, default_value=value) for name, value in ROBOT_DEFAULTS.items()]
        + [DeclareLaunchArgument('robot_description', default_value='',
                                 description='Optional already-expanded robot description.'),
           DeclareLaunchArgument('gz_args', default_value='-r empty.sdf',
                                 description='Arguments passed to Gazebo Sim.'),
           OpaqueFunction(function=launch_nodes)]
    )
