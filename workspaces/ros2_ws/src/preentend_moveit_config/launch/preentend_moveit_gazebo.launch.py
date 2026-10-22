from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"]
            )
        ),
        launch_arguments={"gz_args": "-r -v 2 empty.sdf"}.items(),
    )

    ros2_control = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("preentend_controller"), "launch", "_ros2_control.launch.py"]
            )
        ),
        launch_arguments={"hardware_plugin": "gz_ros2_control/GazeboSimSystem"}.items(),
    )

    spawn_robot = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-world",
            "empty",
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

    moveit = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare("preentend_moveit_config"), "launch", "_moveit_common.launch.py"]
            )
        ),
        launch_arguments={"use_sim_time": "true", "use_rviz": "true"}.items(),
    )

    return LaunchDescription([gazebo, ros2_control, clock_bridge, spawn_robot, moveit])
