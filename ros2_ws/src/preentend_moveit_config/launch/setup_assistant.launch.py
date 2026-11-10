from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from moveit_configs_utils.moveit_configs_builder import MoveItConfigs
from moveit_configs_utils.launches import generate_setup_assistant_launch


def generate_launch_description():
    # The setup assistant needs the package path; loading the complete MoveIt
    # configuration here would require generated planning files to already exist.
    moveit_config = MoveItConfigs(
        package_path=Path(get_package_share_directory("preentend_moveit_config"))
    )
    return generate_setup_assistant_launch(moveit_config)
