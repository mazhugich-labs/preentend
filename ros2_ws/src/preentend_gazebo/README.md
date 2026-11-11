# Preentend Gazebo simulation

Launch Gazebo Sim with the complete robot and ROS 2 control:

```sh
ros2 launch preentend_gazebo preentend_gazebo.launch.py
```

The launch accepts the same `robot_model`, `separation`, `track_length`,
`track_width`, `track_height`, `carrier_length`, `carrier_width`,
`carrier_height`, and `travel` arguments as the robot description. For example:

```sh
ros2 launch preentend_gazebo preentend_gazebo.launch.py robot_model:=m20_25_18d separation:=3.2
```

For a headless server, use the included world with Gazebo's server-only option:

```sh
ros2 launch preentend_gazebo preentend_gazebo.launch.py \
  gz_args:="-s -r $(ros2 pkg prefix preentend_gazebo)/share/preentend_gazebo/worlds/preentend.sdf"
```

The included world loads Gazebo's sensor system. Custom worlds must load the
`gz-sim-sensors-system` plugin to publish camera data. Each robot has a camera
on its flange; edit its shared mounting origin in
`preentend_description/urdf/preentend_robot_macro.xacro`. The initial zero
transform is a placeholder and may overlap the tool.

The bridge forwards `/clock` and the following topics for each of `robot_1` and
`robot_2`:

- `/<robot>/camera/color/image` and `/<robot>/camera/color/camera_info`
- `/<robot>/camera/depth` and `/<robot>/camera/depth/camera_info`
- `/<robot>/camera/depth/points`

Images and camera info use optical frames; point clouds use the depth frame
with +X forward to match Gazebo’s point coordinates.

`gz_ros2_control` provides the controller manager and
joint states directly in ROS; no joint-state or command bridge is needed. The
joint-state broadcaster starts active, while the individual and combined
trajectory controllers start inactive and can be activated as needed. Activate
either the combined controller or the individual controllers, since they claim
the same joints.
