"""Start the Preentend MoveIt configuration with mock ros2_control hardware."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from moveit_configs_utils import MoveItConfigsBuilder


def generate_launch_description():
    description_share = Path(get_package_share_directory("preentend_description"))
    control_share = Path(get_package_share_directory("preentend_ros2_control"))
    bringup_share = Path(get_package_share_directory("preentend_bringup"))
    builder = MoveItConfigsBuilder("preentend", package_name="preentend_moveit_config")
    config = (
        builder.robot_description(
            file_path=str(description_share / "urdf" / "preentend.urdf.xacro"),
            mappings={"mode": "mock"},
        )
        .robot_description_semantic(file_path="srdf/preentend.srdf.xacro")
        .joint_limits(file_path=str(description_share / "config" / "joint_limits"))
        .planning_pipelines(
            pipelines=["ompl", "chomp", "pilz_industrial_motion_planner", "stomp"],
            default_planning_pipeline="ompl",
        )
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .to_moveit_configs()
    )
    parameters = config.to_dict()

    controllers_file = str(control_share / "config" / "ros2_controllers.yaml")
    nodes = [
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            parameters=[config.robot_description],
            output="screen",
        ),
        Node(
            package="controller_manager",
            executable="ros2_control_node",
            parameters=[controllers_file],
            output="screen",
        ),
        Node(
            package="moveit_ros_move_group",
            executable="move_group",
            parameters=[parameters],
            output="screen",
        ),
        Node(
            package="rviz2",
            executable="rviz2",
            arguments=["-d", str(bringup_share / "rviz" / "moveit_mock.rviz")],
            parameters=[parameters],
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
                    "30",
                    "--param-file",
                    controllers_file,
                    *([] if name == "joint_state_broadcaster" else ["--inactive"]),
                ],
            )
        )
    return LaunchDescription(nodes)
