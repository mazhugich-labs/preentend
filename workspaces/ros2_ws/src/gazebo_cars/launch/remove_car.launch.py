from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # Removes from the running Gazebo world; the world is detected automatically.
    # Gazebo reports success even when no entity has this name.
    remove_car = Node(
        package="ros_gz_sim",
        executable="remove",
        parameters=[{"entity_name": "gazebo_car"}],
        output="screen",
    )

    return LaunchDescription([remove_car])
