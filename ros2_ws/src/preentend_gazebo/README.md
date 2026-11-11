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

Use `gz_args:="-s -r empty.sdf"` for a headless server. The bridge forwards
Gazebo's `/clock` to ROS. `gz_ros2_control` provides the controller manager and
joint states directly in ROS; no joint-state or command bridge is needed. The
joint-state broadcaster starts active, while the individual and combined
trajectory controllers start inactive and can be activated as needed. Activate
either the combined controller or the individual controllers, since they claim
the same joints.
