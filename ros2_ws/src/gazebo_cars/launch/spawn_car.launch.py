import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    models_dir = os.path.join(get_package_share_directory("gazebo_cars"), "models")
    cars = sorted(
        name
        for name in os.listdir(models_dir)
        if os.path.isfile(os.path.join(models_dir, name, "model.sdf"))
    )
    car = LaunchConfiguration("car")

    # Spawns into the running Gazebo world; the world is detected automatically.
    spawn_car = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-file",
            PathJoinSubstitution([models_dir, car, "model.sdf"]),
            "-name",
            "gazebo_car",
            "-x",
            LaunchConfiguration("x"),
            "-y",
            LaunchConfiguration("y"),
            "-z",
            LaunchConfiguration("z"),
            "-Y",
            LaunchConfiguration("yaw"),
        ],
        output="screen",
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("car", default_value="car_golf", choices=cars),
            DeclareLaunchArgument("x", default_value="0.0"),
            DeclareLaunchArgument("y", default_value="0.0"),
            DeclareLaunchArgument("z", default_value="0.0"),
            DeclareLaunchArgument("yaw", default_value="0.0", description="Rotation about z, rad"),
            spawn_car,
        ]
    )
