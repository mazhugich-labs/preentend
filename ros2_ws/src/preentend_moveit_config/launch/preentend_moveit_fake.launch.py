"""Start MoveIt with ROS 2 mock hardware for the selected robot model."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import xacro
import yaml


ROBOT_MODELS = (
    'lrmate25_19a', 'lrmate25_19afc', 'm20_25_18d', 'm20_35_18d',
    'kr16_r2010_2', 'kr20_r1820_2_e', 'kr35_r1840_3', 'kr35_r1840_3_hw',
    'kr30_r2100',
)


def load_yaml(path):
    with path.open() as file:
        return yaml.safe_load(file)


def launch_nodes(context):
    model = LaunchConfiguration('robot_model').perform(context)
    if model not in ROBOT_MODELS:
        raise ValueError(f'Unsupported robot model: {model}')
    moveit_share = Path(get_package_share_directory('preentend_moveit_config'))
    control_share = Path(get_package_share_directory('preentend_ros2_control'))
    description_share = Path(get_package_share_directory('preentend_description'))

    # Keep the model argument identical for geometry, control and semantics.
    mappings = {'robot_model': model, 'control_backend': 'mock'}
    robot_description = {'robot_description': xacro.process_file(
        str(control_share / 'robot/preentend_ros2_control.urdf.xacro'), mappings=mappings).toxml()}
    semantic_description = {'robot_description_semantic': xacro.process_file(
        str(moveit_share / 'srdf/preentend.srdf.xacro'),
        mappings={'robot_model': model}).toxml()}
    kinematics = {'robot_description_kinematics': load_yaml(
        moveit_share / 'config/kinematics.yaml')}
    ompl = load_yaml(moveit_share / 'config/ompl_planning.yaml')
    planning = {'planning_pipelines': ['ompl'], 'default_planning_pipeline': 'ompl',
                'ompl': ompl}
    controller_settings = load_yaml(moveit_share / 'config/moveit_controllers.yaml')

    planning_limits = {'robot_description_planning': load_yaml(
        description_share / 'config/joint_limits' / f'{model}_joint_limits.yaml')}

    common = [robot_description, semantic_description, kinematics, planning, planning_limits]
    controllers_file = str(control_share / 'config/ros2_controllers.yaml')
    return [
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[robot_description], output='screen'),
        Node(package='controller_manager', executable='ros2_control_node',
             parameters=[controllers_file], output='screen'),
        Node(package='controller_manager', executable='spawner',
             arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
             output='screen'),
        # Load all trajectory controllers inactive so MoveIt can switch between
        # the two single-arm controllers and the combined controller.
        Node(package='controller_manager', executable='spawner',
             arguments=['robot_1_controller', 'robot_2_controller', 'robots_controller',
                        '--inactive', '--controller-manager', '/controller_manager'],
             output='screen'),
        Node(package='moveit_ros_move_group', executable='move_group',
             parameters=[*common, controller_settings], output='screen'),
        Node(package='rviz2', executable='rviz2',
             # arguments=['-d', str(moveit_share / 'rviz/preentend.rviz')],
             parameters=common, output='screen'),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('robot_model', default_value='kr30_r2100',
                              choices=list(ROBOT_MODELS)),
        OpaqueFunction(function=launch_nodes),
    ])
