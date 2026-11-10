# Robot assemblies

`urdf/preentend_robot_macro.xacro` defines `preentend_robot`.
Provide a unique `prefix`, a `parent` link, a `robot_model`, and an `origin`
block placing the bottom center of the track relative to the parent. Optional
parameters `track_length`, `track_width`, `track_height`, `carrier_length`,
`carrier_width`, `carrier_height`, and `travel` are in meters and default to
the mock axis values. The robot base is mounted to the top of the carrier,
and the default mock tool is attached to the robot flange.

The selectable models are `lrmate25_19a`, `lrmate25_19afc`, `m20_25_18d`,
`m20_35_18d`, `kr16_r2010_2`, `kr20_r1820_2_e`,
`kr35_r1840_3`, `kr35_r1840_3_hw`, and `kr30_r2100`.
Robot links use `link_1` through `link_6`, with joints named
`link_1_joint` through `link_6_joint`. Each arm exposes a `flange` frame.

`config/joint_limits/<robot_model>_joint_limits.yaml` contains MoveIt limits
for both prefixed arms and their linear axes. The axis velocity is limited to
1 m/s, matching the mock-axis URDF, and its acceleration is 6.8119 m/s².
Fanuc arm accelerations are estimates based on comparable
KUKA models, as noted in those files.

`robot/preentend.urdf.xacro` builds two assemblies, with
a shared `robot_model` for both robots. `separation`
sets the center-to-center distance between the parallel tracks along Y in
meters; they are centered around the world origin. Both axes share the
optional dimension and travel arguments listed above. For example, after
building and sourcing the workspace:

```sh
xacro $(ros2 pkg prefix --share preentend_description)/robot/preentend.urdf.xacro \
  robot_model:=kr30_r2100 separation:=3.0
```

To publish the model and open RViz with its default configuration:

```sh
ros2 launch preentend_description view_preentend.launch.py robot_model:=kr30_r2100 separation:=3.0
```

The launch opens RViz, the joint-state controls, and a robot model selector.
Choose a model and click **Load** to replace both arms while keeping the track
dimensions and separation supplied at launch. The joint-state controls are
rebuilt for the selected model. The launch file also accepts the dimension and
travel arguments above.

For a robot description with ROS 2 control interfaces, use the
`preentend_ros2_control` package.
