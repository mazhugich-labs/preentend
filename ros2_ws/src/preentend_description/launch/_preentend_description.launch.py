from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare
from preentend_utils import process_xacro


XACRO_ARGUMENTS = {
    'robot_family': 'kuka',
    'robot_model': 'kr30_r2100',
    'external_axis_model': 'mock',
    'end_effector_model': 'mock',
    'robot_arm_camera_model': 'd435',
    'overhead_camera_model': 'd435',
    'mode': 'mock',
    'controllers_file': '',
    'separation': '4.0',
}

XACRO_ARGUMENTS.update({
    'travel': '6.0',
    'robot_arm_camera_update_rate': '15',
    'robot_arm_camera_color_width': '1280',
    'robot_arm_camera_color_height': '720',
    'robot_arm_camera_depth_width': '640',
    'robot_arm_camera_depth_height': '480',
    'overhead_camera_update_rate': '15',
    'overhead_camera_color_width': '1920',
    'overhead_camera_color_height': '1080',
    'overhead_camera_depth_width': '640',
    'overhead_camera_depth_height': '480',
})


def _robot_state_publisher(context):
    description_file = LaunchConfiguration('description_file').perform(context)
    mappings = {name: LaunchConfiguration(name).perform(context) for name in XACRO_ARGUMENTS}
    description = process_xacro(description_file, mappings=mappings)
    return [Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': ParameterValue(description, value_type=str),
            'use_sim_time': ParameterValue(LaunchConfiguration('use_sim_time'), value_type=bool),
        }],
    )]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'description_file',
            default_value=PathJoinSubstitution([
                FindPackageShare('preentend_description'), 'urdf', 'preentend.urdf.xacro',
            ]),
            description='Path to the robot URDF or xacro file',
        ),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        *[DeclareLaunchArgument(name, default_value=default)
          for name, default in XACRO_ARGUMENTS.items()],
        OpaqueFunction(function=_robot_state_publisher),
    ])
