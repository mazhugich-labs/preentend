# Preentend Simulation

## About

Preentend is a simulation project for a touchless car wash: two industrial robots travel on parallel linear axes and carry washing tools around a vehicle. The workspace brings together robot descriptions, motion planning, control, and simulation for developing the robotic system.

## Software stack

- ROS 2 Jazzy and xacro for robot descriptions and launch files.
- MoveIt 2 and RViz for motion planning and visualization.
- ros2_control and ROS 2 controllers for joint control.
- Gazebo Sim and ROS–Gazebo integration for physics simulation.
- Docker Compose and colcon for the development environment and workspace build.

## Overview

- `ros2_ws/src/preentend_description` — assembles the two robots, linear axes, and tools; provides robot-specific joint limits and a visualization launch.
- `ros2_ws/src/preentend_ros2_control` — defines control interfaces, initial positions, controllers, and a mock hardware launch.
- `ros2_ws/src/preentend_gazebo` — spawns the system in Gazebo with simulated control and a clock bridge.
- `ros2_ws/src/preentend_moveit_config` — provides planning groups, collision matrix generation and caching, planning configuration, and MoveIt launches.
- `ros2_ws/src/miscellaneous` — reusable FANUC and KUKA robot descriptions, mock linear axis, tool, and RGB-D camera descriptions, and KUKA resources.
- `docker/` and `docker-compose.yaml` — the container image and runtime configuration; `scripts/` contains Compose helpers.

## Installation

The supplied container setup targets Linux with Docker, Docker Compose, an X11 display, an NVIDIA GPU, and the NVIDIA Container Toolkit. Gazebo and RViz need access to the display; the Compose configuration also passes through `/dev/dri`.

From the repository root:

```sh
cp .env.example .env
source scripts/setup_env.sh
bash scripts/compose_up.sh
bash scripts/compose_exec.sh
```

Inside the container, build and source the workspace:

```sh
cd /home/ros2_ws
source /opt/ros/jazzy/setup.bash
bash build.sh
source source.sh
```

Source the ROS and workspace setup files in each new container shell. From the repository root, run `source scripts/setup_env.sh` and `bash scripts/compose_down.sh` to stop the container.

## Example usage

Run these commands in a sourced container shell:

```sh
# View the description and select a robot model.
ros2 launch preentend_description _preentend_description.launch.py
```

https://github.com/user-attachments/assets/95a4e74f-8a9e-47c8-92a5-244c3c14af5b

```sh
# Run Gazebo, MoveIt, and RViz together.
ros2 launch preentend_bringup preentend_moveit_gazebo.launch.py
```

https://github.com/user-attachments/assets/31ae3f52-45ab-42b3-96b8-aee3a7ff0b26

Choose another model or adjust separation through launch arguments, for example:

```sh
ros2 launch preentend_bringup preentend_moveit_gazebo.launch.py \
  robot_model:=m20_25_18d separation:=3.2
```

Edit `ros2_ws/src/preentend_bringup/config/config.yaml` or pass `config_file:=<path>` to adjust the system configuration. Use `--show-args` with a launch command to see its options. MoveIt generates a collision matrix for each family, model, and separation on first launch and reuses the file if it exists. Remove the file to regenerate it after changing robot geometry or planning groups.

The standalone MoveIt launch takes its robot-specific paths as arguments. For the included description, run:

```sh
description_share="$(ros2 pkg prefix --share preentend_description)"
ros2 launch preentend_moveit_config standalone.launch.py \
  description_file:="${description_share}/urdf/preentend.urdf.xacro" \
  srdf_file:="${description_share}/srdf/preentend.srdf.xacro" \
  groups_file:="${description_share}/srdf/_common.srdf.xacro" \
  collision_matrices_dir:="${description_share}/srdf/collision_matrices"
```

The matrix output directory must match the location included by the supplied SRDF xacro. The standalone generator accepts the same paths through `--robot-description`, `--groups-file`, and `--output-dir`.

Spawn car alongside MoveIt Gazebo launch script.

```sh
ros2 launch gazebo_cars spawn_car.launch.py
```

https://github.com/user-attachments/assets/8a0d0032-1cf5-4a1b-b658-e0b456bbbb14

Use `--car <model>` with launch command to specify car model.

## TODO

- [x] Add RGB-D camera support.
- [x] Add variety of car models.
- [ ] Add washing bay geometry.
