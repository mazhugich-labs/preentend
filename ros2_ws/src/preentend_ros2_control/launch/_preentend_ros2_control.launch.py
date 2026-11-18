from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    controllers_file = PathJoinSubstitution([
        FindPackageShare('preentend_ros2_control'), 'config', 'ros2_controller.yaml',
    ])
    manager_timeout = LaunchConfiguration('controller_manager_timeout')

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument(
            'start_control_node', default_value='true',
            description='Set false when Gazebo or another process supplies the controller manager',
        ),
        DeclareLaunchArgument('controller_manager_timeout', default_value='120'),
        Node(
            package='controller_manager', executable='ros2_control_node',
            parameters=[controllers_file, {
                'use_sim_time': ParameterValue(LaunchConfiguration('use_sim_time'), value_type=bool),
            }],
            condition=IfCondition(LaunchConfiguration('start_control_node')),
            output='screen',
        ),
        Node(
            package='controller_manager', executable='spawner',
            arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager',
                       '--controller-manager-timeout', manager_timeout, '--param-file', controllers_file],
            output='screen',
        ),
        Node(
            package='controller_manager', executable='spawner',
            arguments=['robot_1_controller', '--controller-manager', '/controller_manager',
                       '--controller-manager-timeout', manager_timeout, '--param-file', controllers_file,
                       '--inactive'],
            output='screen',
        ),
        Node(
            package='controller_manager', executable='spawner',
            arguments=['robot_2_controller', '--controller-manager', '/controller_manager',
                       '--controller-manager-timeout', manager_timeout, '--param-file', controllers_file,
                       '--inactive'],
            output='screen',
        ),
        Node(
            package='controller_manager', executable='spawner',
            arguments=['robots_controller', '--controller-manager', '/controller_manager',
                       '--controller-manager-timeout', manager_timeout, '--param-file', controllers_file,
                       '--inactive'],
            output='screen',
        ),
    ])
