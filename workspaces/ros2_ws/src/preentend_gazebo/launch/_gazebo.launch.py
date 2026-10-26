from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    world = LaunchConfiguration("world")

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"]
            )
        ),
        launch_arguments={"gz_args": ["-r -v 2 ", world]}.items(),
    )

    # Spawns the model from the robot_description topic, so a
    # robot_state_publisher must be running alongside this launch file.
    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic",
            "robot_description",
            "-name",
            "preentend",
        ],
        output="screen",
    )

    clock_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"],
        output="screen",
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "world",
                default_value=PathJoinSubstitution(
                    [FindPackageShare("preentend_gazebo"), "worlds", "empty.sdf"]
                ),
            ),
            gazebo,
            spawn_robot,
            clock_bridge,
        ]
    )
