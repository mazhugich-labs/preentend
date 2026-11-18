import os
from pathlib import Path
import shlex
import tempfile

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction,
                            RegisterEventHandler, SetEnvironmentVariable)
from launch.conditions import IfCondition
from launch.event_handlers import OnShutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import xacro


def _remove_world(context, path):
    Path(path).unlink(missing_ok=True)
    return []


def _launch_simulation(context):
    share = Path(get_package_share_directory('preentend_gazebo'))
    world = xacro.process_file(str(share / 'worlds/preentend_world.sdf.xacro')).toxml()
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.sdf',
                                     prefix='preentend-world-', delete=False) as output:
        output.write(world)
        world_path = output.name

    shares = [str(Path(prefix) / 'share') for prefix in os.environ.get('AMENT_PREFIX_PATH', '').split(os.pathsep) if prefix]
    resource_paths = [os.environ.get('GZ_SIM_RESOURCE_PATH', ''), *shares]
    server_only = IfCondition(LaunchConfiguration('headless')).evaluate(context)
    gz_args = ['-r'] + (['-s', '--headless-rendering'] if server_only else []) + [world_path]
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py',
        ])),
        launch_arguments={'gz_args': shlex.join(gz_args), 'on_exit_shutdown': 'true'}.items(),
    )
    spawn = Node(
        package='ros_gz_sim', executable='create', output='screen',
        arguments=['-world', 'preentend_world', '-topic', LaunchConfiguration('robot_description_topic'),
                   '-name', LaunchConfiguration('robot_name')],
    )
    return [
        RegisterEventHandler(OnShutdown(on_shutdown=[OpaqueFunction(function=_remove_world, args=[world_path])])),
        SetEnvironmentVariable('GZ_SIM_RESOURCE_PATH', os.pathsep.join(path for path in resource_paths if path)),
        gazebo,
        spawn,
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('robot_description_topic', default_value='/robot_description'),
        DeclareLaunchArgument('robot_name', default_value='preentend'),
        DeclareLaunchArgument('headless', default_value='false',
                              description='Run the Gazebo server without its GUI'),
        OpaqueFunction(function=_launch_simulation),
    ])
