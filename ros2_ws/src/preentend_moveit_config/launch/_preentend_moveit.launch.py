import os
from pathlib import Path

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, ExecuteProcess, OpaqueFunction, RegisterEventHandler
from launch.event_handlers import OnProcessExit, OnProcessIO
from launch.events import Shutdown
from launch.substitutions import FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare
import yaml


def _move_group(context):
    def load(argument):
        path = LaunchConfiguration(argument).perform(context)
        with Path(path).open(encoding='utf-8') as stream:
            return yaml.safe_load(stream) or {}

    pilz = load('pilz_planning_file')
    capabilities = pilz.pop('capabilities', '')
    parameters = {
        'robot_description_kinematics': load('kinematics_file'),
        'robot_description_planning': {**load('joint_limits_file'), **load('pilz_cartesian_limits_file')},
        'planning_pipelines': ['ompl', 'chomp', 'pilz_industrial_motion_planner'],
        'default_planning_pipeline': 'ompl',
        'ompl': load('ompl_planning_file'),
        'chomp': load('chomp_planning_file'),
        'pilz_industrial_motion_planner': pilz,
        'capabilities': capabilities,
        **load('moveit_controllers_file'),
        'use_sim_time': ParameterValue(LaunchConfiguration('use_sim_time'), value_type=bool),
    }
    return [Node(
        package='moveit_ros_move_group', executable='move_group', output='screen',
        parameters=[parameters],
        remappings=[('robot_description', LaunchConfiguration('robot_description_topic')),
                    ('robot_description_semantic', LaunchConfiguration('semantic_description_topic'))],
    )]


def generate_launch_description():
    share = FindPackageShare('preentend_moveit_config')
    cache_home = Path(os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache')
    semantic = ExecuteProcess(
        cmd=[FindExecutable(name='ros2'), 'run', 'preentend_moveit_config', 'semantic_description_publisher',
             '--robot-model', LaunchConfiguration('robot_model'),
             '--srdf-file', PathJoinSubstitution([share, 'srdf', 'robot.srdf.xacro']),
             '--collision-matrices-dir', LaunchConfiguration('collision_matrices_dir'),
             '--collision-trials', LaunchConfiguration('collision_trials'),
             '--description-timeout', LaunchConfiguration('description_timeout'),
             '--robot-description-topic', LaunchConfiguration('robot_description_topic'),
             '--semantic-description-topic', LaunchConfiguration('semantic_description_topic')],
        output='screen',
    )
    state = {'output': '', 'started': False}

    def ready(event):
        if state['started']:
            return []
        state['output'] = (state['output'] + event.text.decode('utf-8', errors='replace'))[-256:]
        if 'SEMANTIC_DESCRIPTION_READY' in state['output']:
            state['started'] = True
            return [OpaqueFunction(function=_move_group)]
        return []

    def semantic_exit(event, context):
        return [EmitEvent(event=Shutdown(reason='Semantic description publisher exited'))]

    return LaunchDescription([
        DeclareLaunchArgument('robot_model', default_value='kr30_r2100'),
        DeclareLaunchArgument('robot_description_topic', default_value='/robot_description'),
        DeclareLaunchArgument('semantic_description_topic', default_value='/robot_description_semantic'),
        DeclareLaunchArgument('joint_limits_file', default_value=PathJoinSubstitution([
            share, 'config', 'joint_limits.yaml']),
            description='Path to the robot joint-limits YAML'),
        DeclareLaunchArgument('kinematics_file', default_value=PathJoinSubstitution([
            share, 'config', 'kinematics.yaml'])),
        DeclareLaunchArgument('pilz_cartesian_limits_file', default_value=PathJoinSubstitution([
            share, 'config', 'pilz_cartesian_limits.yaml'])),
        DeclareLaunchArgument('ompl_planning_file', default_value=PathJoinSubstitution([
            share, 'config', 'ompl_planning.yaml'])),
        DeclareLaunchArgument('chomp_planning_file', default_value=PathJoinSubstitution([
            share, 'config', 'chomp_planning.yaml'])),
        DeclareLaunchArgument('pilz_planning_file', default_value=PathJoinSubstitution([
            share, 'config', 'pilz_industrial_motion_planner_planning.yaml'])),
        DeclareLaunchArgument('moveit_controllers_file', default_value=PathJoinSubstitution([
            share, 'config', 'moveit_controllers.yaml'])),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('collision_trials', default_value='100000'),
        DeclareLaunchArgument('description_timeout', default_value='60.0'),
        DeclareLaunchArgument('collision_matrices_dir', default_value=str(
            cache_home / 'preentend_moveit_config/collision_matrices')),
        RegisterEventHandler(OnProcessIO(target_action=semantic, on_stdout=ready)),
        RegisterEventHandler(OnProcessExit(target_action=semantic, on_exit=semantic_exit)),
        semantic,
    ])
