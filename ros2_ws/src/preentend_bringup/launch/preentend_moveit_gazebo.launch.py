import os
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, EmitEvent, ExecuteProcess,
                            IncludeLaunchDescription, OpaqueFunction, RegisterEventHandler)
from launch.event_handlers import OnProcessExit
from launch.conditions import IfCondition
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
import yaml


def generate_launch_description():
    kinematics_file = Path(get_package_share_directory('preentend_moveit_config')) / 'config' / 'kinematics.yaml'
    with kinematics_file.open(encoding='utf-8') as stream:
        kinematics = yaml.safe_load(stream)
    bringup_share = FindPackageShare('preentend_bringup')
    description_share = FindPackageShare('preentend_description')
    control_share = FindPackageShare('preentend_ros2_control')
    gazebo_share = FindPackageShare('preentend_gazebo')
    moveit_share = FindPackageShare('preentend_moveit_config')
    description = LaunchConfiguration('description_file')
    semantic_topic = '/robot_description_semantic'
    robot_topic = '/robot_description'

    def description_and_move_group(context):
        def read_yaml(path):
            with Path(path).open(encoding='utf-8') as stream:
                return yaml.safe_load(stream) or {}

        config = read_yaml(LaunchConfiguration('config_file').perform(context))
        configured_arm = config['robot_arm']
        model_override = LaunchConfiguration('robot_model').perform(context)
        robot_model = model_override or str(configured_arm['model'])
        robot_family = (('fanuc' if robot_model.startswith(('lrmate', 'm20')) else 'kuka')
                        if model_override else str(configured_arm['family']))
        axis = config['external_axis']
        axis_arguments = {'travel': str(axis['travel'])}
        camera_arguments = {}
        for camera in ('robot_arm', 'overhead'):
            settings = config['cameras'][camera]
            camera_arguments[f'{camera}_camera_update_rate'] = str(settings['update_rate'])
            for stream in ('color', 'depth'):
                for dimension in ('width', 'height'):
                    camera_arguments[f'{camera}_camera_{stream}_{dimension}'] = str(settings[stream][dimension])
        description_launch = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                description_share, 'launch', '_preentend_description.launch.py'])),
            launch_arguments={
                'description_file': description,
                'use_sim_time': 'true',
                'robot_model': robot_model,
                'robot_family': robot_family,
                'external_axis_model': LaunchConfiguration('external_axis_model').perform(context) or str(axis['model']),
                'end_effector_model': LaunchConfiguration('end_effector_model').perform(context) or str(config['end_effector']['model']),
                'robot_arm_camera_model': LaunchConfiguration('robot_arm_camera_model').perform(context) or str(config['cameras']['robot_arm']['model']),
                'overhead_camera_model': LaunchConfiguration('overhead_camera_model').perform(context) or str(config['cameras']['overhead']['model']),
                'mode': 'gazebo',
                'controllers_file': PathJoinSubstitution([control_share, 'config', 'ros2_controller.yaml']),
                'separation': LaunchConfiguration('separation').perform(context) or str(config['layout']['separation']),
                **axis_arguments,
                **camera_arguments,
            }.items(),
        )
        move_group = IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([
                moveit_share, 'launch', '_preentend_moveit.launch.py'])),
            launch_arguments={'use_sim_time': 'true', 'robot_model': robot_model,
                              'joint_limits_file': LaunchConfiguration('joint_limits_file'),
                              'robot_description_topic': robot_topic,
                              'semantic_description_topic': semantic_topic,
                              'collision_matrices_dir': LaunchConfiguration('collision_matrices_dir'),
                              'collision_trials': LaunchConfiguration('collision_trials'),
                              'description_timeout': LaunchConfiguration('description_timeout')}.items(),
        )
        return [description_launch, move_group]

    control_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            control_share, 'launch', '_preentend_ros2_control.launch.py'])),
        launch_arguments={'use_sim_time': 'true', 'start_control_node': 'false'}.items(),
    )
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([
            gazebo_share, 'launch', '_preentend_gazebo.launch.py'])),
        launch_arguments={'robot_description_topic': robot_topic,
                          'headless': LaunchConfiguration('headless')}.items(),
    )
    clock_bridge = Node(
        package='ros_gz_bridge', executable='parameter_bridge', name='clock_bridge', output='screen',
        parameters=[{'config_file': PathJoinSubstitution([gazebo_share, 'config', 'global_bridge.yaml'])}],
    )
    camera_bridges = [Node(
        package='ros_gz_bridge', executable='parameter_bridge', name='camera_bridge', namespace=name,
        output='screen', parameters=[{
            'config_file': PathJoinSubstitution([gazebo_share, 'config', 'camera_bridge.yaml']),
            'expand_gz_topic_names': True,
            'use_sim_time': True,
        }],
    ) for name in ('robot_1', 'robot_2', 'overhead')]
    # Gazebo's depth cloud uses the camera body axes; images use optical axes.
    point_cloud_bridges = [Node(
        package='ros_gz_bridge', executable='parameter_bridge', name='point_cloud_bridge', namespace=name,
        output='screen', parameters=[{
            'config_file': PathJoinSubstitution([gazebo_share, 'config', name + '_points_bridge.yaml']),
            'expand_gz_topic_names': True,
            'use_sim_time': True,
        }],
    ) for name in ('robot_1', 'robot_2', 'overhead')]
    rviz = Node(
        package='rviz2', executable='rviz2', output='screen',
        parameters=[{'robot_description_kinematics': kinematics,
                     'default_planning_pipeline': 'ompl', 'use_sim_time': True}],
        arguments=['-d', PathJoinSubstitution([bringup_share, 'rviz', 'moveit_gazebo.rviz'])],
        condition=IfCondition(LaunchConfiguration('use_rviz')),
    )
    wait_for_move_group = ExecuteProcess(
        cmd=[FindExecutable(name='ros2'), 'run', 'preentend_bringup', 'wait_for_move_group',
             '--timeout', LaunchConfiguration('move_group_timeout')],
        output='screen',
    )
    def move_group_ready(event, context):
        if event.returncode != 0:
            return [EmitEvent(event=Shutdown(reason='Move group did not become ready'))]
        return [rviz]

    cache_home = Path(os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache')
    return LaunchDescription([
        DeclareLaunchArgument('robot_model', default_value=''),
        DeclareLaunchArgument('external_axis_model', default_value=''),
        DeclareLaunchArgument('end_effector_model', default_value=''),
        DeclareLaunchArgument('robot_arm_camera_model', default_value=''),
        DeclareLaunchArgument('overhead_camera_model', default_value=''),
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument('headless', default_value='false'),
        DeclareLaunchArgument('joint_limits_file', default_value=PathJoinSubstitution([
            moveit_share, 'config', 'joint_limits.yaml'])),
        DeclareLaunchArgument('description_file', default_value=PathJoinSubstitution([
            description_share, 'urdf', 'preentend.urdf.xacro'])),
        DeclareLaunchArgument('separation', default_value=''),
        DeclareLaunchArgument('config_file', default_value=PathJoinSubstitution([
            bringup_share, 'config', 'config.yaml'])),
        DeclareLaunchArgument('collision_trials', default_value='100000'),
        DeclareLaunchArgument('description_timeout', default_value='60.0'),
        DeclareLaunchArgument('move_group_timeout', default_value='120.0'),
        DeclareLaunchArgument('collision_matrices_dir', default_value=str(
            cache_home / 'preentend_moveit_config/collision_matrices')),
        RegisterEventHandler(OnProcessExit(target_action=wait_for_move_group, on_exit=move_group_ready)),
        OpaqueFunction(function=description_and_move_group),
        gazebo_launch,
        clock_bridge,
        *camera_bridges,
        *point_cloud_bridges,
        control_launch,
        wait_for_move_group,
    ])
