from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    # Available robot models:
    # lrmate25_19a, lrmate25_19afc
    # m20_25_18d, m20_35_18d,
    # kr16_r2010_2, kr20_r1820_2_e, kr35_r1840_3, kr35_r1840_3_hw
    # kr20_r3100, kr30_r2100.
    defaults = {
        "robot_model": "kr30_r2100",
        "separation": "4.0",
        "track_length": "6.4",
        "track_width": "0.4",
        "track_height": "0.2",
        "carrier_length": "0.4",
        "carrier_width": "0.4",
        "carrier_height": "0.4",
        "travel": "6.0",
    }
    arguments = [
        DeclareLaunchArgument(name, default_value=value)
        for name, value in defaults.items()
    ]
    description_file = PathJoinSubstitution(
        [FindPackageShare("preentend_description"), "robot", "two_robots_on_linear_axes.urdf.xacro"]
    )
    command = [FindExecutable(name="xacro"), " ", description_file]
    for name in defaults:
        command.extend([" ", name, ":=", LaunchConfiguration(name)])

    robot_description = ParameterValue(Command(command), value_type=str)
    return LaunchDescription(
        arguments
        + [
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                parameters=[{"robot_description": robot_description}],
            ),
            Node(package="joint_state_publisher", executable="joint_state_publisher"),
            Node(
                package="preentend_description",
                executable="robot_model_selector",
                parameters=[{
                    name: ParameterValue(LaunchConfiguration(name), value_type=str)
                    for name in defaults
                }],
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                arguments=["-d", PathJoinSubstitution(
                    [FindPackageShare("preentend_description"), "rviz", "view_preentend.rviz"]
                )],
            ),
        ]
    )
