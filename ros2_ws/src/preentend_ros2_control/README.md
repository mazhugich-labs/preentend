# ROS 2 control

`robot/preentend_ros2_control.urdf.xacro` combines the description with one
`ros2_control` system for each arm and linear axis. It accepts `robot_model`,
dimension arguments, and `control_backend`:

```sh
xacro $(ros2 pkg prefix --share preentend_ros2_control)/robot/preentend_ros2_control.urdf.xacro \
  robot_model:=kr30_r2100 control_backend:=mock
```

Each system exposes position commands and position/velocity state interfaces
for seven joints. Initial positions come from `config/fanuc_initial_positions.yaml`
or `config/kuka_initial_positions.yaml` based on the model. Velocity states start at zero. The
`mock` backend uses `mock_components/GenericSystem`; choose `gazebo` for
`gz_ros2_control/GazeboSimSystem`.

The controller-manager configuration is in `config/ros2_controllers.yaml`.
Do not activate the combined trajectory controller at the same time as the
individual controllers because they claim the same joints. Gazebo also needs
a single system plugin for the whole model, controller startup, and suitable
physical properties for the robot links. These control tags do not start Gazebo
or controllers.

To start the mock hardware, robot-state publisher, and controllers:

```sh
ros2 launch preentend_ros2_control preentend_ros2_control_fake.launch.py \
  robot_model:=kr30_r2100 separation:=4.0
```

The launch accepts the robot model and all assembly dimension arguments. It
also accepts an already-expanded `robot_description`; the MoveIt launch uses
that option to share exactly the same URDF with the controller manager.
