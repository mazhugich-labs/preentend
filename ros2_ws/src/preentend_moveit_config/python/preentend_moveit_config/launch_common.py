"""Shared MoveIt setup for mock and Gazebo control backends."""

from pathlib import Path
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.logging import get_logger
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import xacro
import yaml
from preentend_moveit_config.collision_cache import get_collision_srdf


ROBOT_MODELS = (
    'lrmate25_19a', 'lrmate25_19afc', 'm20_25_18d', 'm20_35_18d',
    'kr16_r2010_2', 'kr20_r1820_2_e', 'kr35_r1840_3', 'kr35_r1840_3_hw',
    'kr30_r2100',
)
ROBOT_DEFAULTS = {
    'robot_model': 'kr30_r2100', 'separation': '4.0', 'track_length': '6.4',
    'track_width': '0.4', 'track_height': '0.2', 'carrier_length': '0.4',
    'carrier_width': '0.4', 'carrier_height': '0.4', 'travel': '6.0',
}


def load_yaml(path):
    with path.open() as file:
        return yaml.safe_load(file)


def launch_nodes(context, backend):
    model = LaunchConfiguration('robot_model').perform(context)
    if model not in ROBOT_MODELS:
        raise ValueError(f'Unsupported robot model: {model}')
    moveit_share = Path(get_package_share_directory('preentend_moveit_config'))
    control_share = Path(get_package_share_directory('preentend_ros2_control'))
    description_share = Path(get_package_share_directory('preentend_description'))

    # Keep the model argument identical for geometry, control and semantics.
    mappings = {name: LaunchConfiguration(name).perform(context) for name in ROBOT_DEFAULTS}
    mappings['control_backend'] = backend
    if backend == 'gazebo':
        robot_file = Path(get_package_share_directory('preentend_gazebo')) / 'robot/preentend_gazebo.urdf.xacro'
    else:
        robot_file = control_share / 'robot/preentend_ros2_control.urdf.xacro'
    robot_description = {'robot_description': xacro.process_file(
        str(robot_file), mappings=mappings).toxml()}
    semantic_template = xacro.process_file(
        str(moveit_share / 'srdf/preentend_groups.srdf.xacro')).toxml()
    srdf, cache_hit = get_collision_srdf(
        robot_description['robot_description'], semantic_template, mappings,
        int(LaunchConfiguration('collision_trials').perform(context)),
        LaunchConfiguration('collision_cache_dir').perform(context),
    )
    get_logger('preentend_moveit').info(
        'Using cached collision matrix' if cache_hit else 'Generated collision matrix'
    )
    semantic_description = {'robot_description_semantic': srdf}
    kinematics = {'robot_description_kinematics': load_yaml(
        moveit_share / 'config/kinematics.yaml')}
    ompl = load_yaml(moveit_share / 'config/ompl_planning.yaml')
    planning = {'planning_pipelines': ['ompl', 'chomp', 'pilz_industrial_motion_planner'],
                'default_planning_pipeline': 'ompl', 'ompl': ompl,
                'chomp': load_yaml(moveit_share / 'config/chomp_planning.yaml'),
                'pilz_industrial_motion_planner': load_yaml(
                    moveit_share / 'config/pilz_industrial_motion_planner_planning.yaml')}
    controller_settings = load_yaml(moveit_share / 'config/moveit_controllers.yaml')

    planning_limits = {'robot_description_planning': load_yaml(
        description_share / 'config/joint_limits' / f'{model}_joint_limits.yaml')}
    planning_limits['robot_description_planning'].update(
        load_yaml(moveit_share / 'config/pilz_cartesian_limits.yaml'))

    common = [robot_description, semantic_description, kinematics, planning, planning_limits]
    if backend == 'gazebo':
        backend_share = Path(get_package_share_directory('preentend_gazebo'))
        backend_launch = backend_share / 'launch/preentend_gazebo.launch.py'
        backend_args = {'gz_args': LaunchConfiguration('gz_args')}
    else:
        backend_launch = control_share / 'launch/preentend_ros2_control_fake.launch.py'
        backend_args = {}
    control = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(backend_launch)),
        launch_arguments={
            **{name: mappings[name] for name in ROBOT_DEFAULTS},
            'robot_description': robot_description['robot_description'],
            **backend_args,
        }.items(),
    )
    if backend == 'gazebo':
        common.append({'use_sim_time': True})
    return [
        control,
        Node(package='moveit_ros_move_group', executable='move_group',
             parameters=[*common, controller_settings], output='screen'),
        Node(package='rviz2', executable='rviz2',
             arguments=['-d', str(moveit_share / 'rviz/preentend_moveit_fake.rviz')],
             parameters=common, output='screen'),
    ]


def generate_moveit_launch_description(backend):
    arguments = [DeclareLaunchArgument('robot_model', default_value=ROBOT_DEFAULTS['robot_model'],
                                       choices=list(ROBOT_MODELS))]
    arguments.extend(DeclareLaunchArgument(name, default_value=value)
                     for name, value in ROBOT_DEFAULTS.items() if name != 'robot_model')
    cache_home = Path(os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache')
    if backend == 'gazebo':
        arguments.append(DeclareLaunchArgument('gz_args', default_value='-r empty.sdf',
                                               description='Arguments passed to Gazebo Sim.'))
    return LaunchDescription(arguments + [
        DeclareLaunchArgument('collision_trials', default_value='100000',
                              description='Number of collision-sampling trials.'),
        DeclareLaunchArgument('collision_cache_dir',
                              default_value=str(cache_home / 'preentend_moveit_config/collisions'),
                              description='Directory for generated collision matrices.'),
        OpaqueFunction(function=launch_nodes, kwargs={'backend': backend}),
    ])
