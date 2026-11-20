"""Start MoveIt and the Preentend robot in Gazebo Sim."""

import os
from pathlib import Path
import shlex

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
    SetEnvironmentVariable,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def _gazebo(context):
    gazebo_share = Path(get_package_share_directory("preentend_gazebo"))
    ros_gz_share = Path(get_package_share_directory("ros_gz_sim"))
    headless = IfCondition(LaunchConfiguration("headless")).evaluate(context)
    args = ["-r"] + (["-s", "--headless-rendering"] if headless else [])
    args.append(str(gazebo_share / "worlds" / "empty.sdf"))
    return [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                str(ros_gz_share / "launch" / "gz_sim.launch.py")
            ),
            launch_arguments={
                "gz_args": shlex.join(args),
                "on_exit_shutdown": "true",
            }.items(),
        )
    ]


def generate_launch_description():
    description_share = Path(get_package_share_directory("preentend_description"))
    control_share = Path(get_package_share_directory("preentend_ros2_control"))
    gazebo_share = Path(get_package_share_directory("preentend_gazebo"))
    bringup_share = Path(get_package_share_directory("preentend_bringup"))
    controllers_file = str(control_share / "config" / "ros2_controllers.yaml")
    config = (
        MoveItConfigsBuilder("preentend", package_name="preentend_moveit_config")
        .robot_description(
            file_path=str(description_share / "urdf" / "preentend.urdf.xacro"),
            mappings={"mode": "gazebo", "controllers_file": controllers_file},
        )
        .robot_description_semantic(file_path="srdf/preentend.srdf.xacro")
        .joint_limits(file_path=str(description_share / "config" / "joint_limits"))
        .planning_pipelines(
            pipelines=["ompl", "chomp", "pilz_industrial_motion_planner", "stomp"],
            default_planning_pipeline="ompl",
        )
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .sensors_3d(file_path="config/sensors_3d.yaml")
        .to_moveit_configs()
    )
    sim_time = {"use_sim_time": True}
    parameters = [config.to_dict(), sim_time]
    resource_paths = [os.environ.get("GZ_SIM_RESOURCE_PATH", "")]
    resource_paths.extend(
        str(Path(prefix) / "share")
        for prefix in os.environ.get("AMENT_PREFIX_PATH", "").split(os.pathsep)
        if prefix
    )
    nodes = [
        DeclareLaunchArgument(
            "headless", default_value="false", description="Run Gazebo without its GUI"
        ),
        SetEnvironmentVariable(
            "GZ_SIM_RESOURCE_PATH", os.pathsep.join(filter(None, resource_paths))
        ),
        OpaqueFunction(function=_gazebo),
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            parameters=[config.robot_description, sim_time],
            output="screen",
        ),
        Node(
            package="ros_gz_sim",
            executable="create",
            arguments=[
                "-world",
                "preentend_world",
                "-topic",
                "/robot_description",
                "-name",
                "preentend",
            ],
            output="screen",
        ),
        Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            parameters=[
                {"config_file": str(gazebo_share / "config" / "bridge.yaml")},
                sim_time,
            ],
            output="screen",
        ),
        Node(
            package="moveit_ros_move_group",
            executable="move_group",
            parameters=parameters,
            output="screen",
        ),
        Node(
            package="rviz2",
            executable="rviz2",
             arguments=["-d", str(bringup_share / "rviz" / "moveit_gazebo.rviz")],
            parameters=parameters,
            output="screen",
        ),
    ]
    for name in (
        "joint_state_broadcaster",
        "robot_1_controller",
        "robot_2_controller",
        "robots_controller",
    ):
        nodes.append(
            Node(
                package="controller_manager",
                executable="spawner",
                output="screen",
                arguments=[
                    name,
                    "--controller-manager",
                    "/controller_manager",
                    "--controller-manager-timeout",
                    "60",
                    "--param-file",
                    controllers_file,
                    *([] if name == "joint_state_broadcaster" else ["--inactive"]),
                ],
            )
        )
    return LaunchDescription(nodes)
