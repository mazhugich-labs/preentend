# MoveIt robot semantics

`srdf/preentend.srdf.xacro` composes the `robot_1`, `robot_2`, and `robots`
planning groups with the collision matrix selected by `robot_model`. Use the
same model argument for the URDF and SRDF:

```sh
xacro $(ros2 pkg prefix --share preentend_description)/robot/preentend.urdf.xacro robot_model:=m20_25_18d > /tmp/preentend.urdf
xacro $(ros2 pkg prefix --share preentend_moveit_config)/srdf/preentend.srdf.xacro robot_model:=m20_25_18d > /tmp/preentend.srdf
```

The per-model macros in `srdf/collision_matrices` were generated using
`moveit_setup_assistant`'s `collisions_updater` with 100,000 random trials per
model, passing `robot_model` as a xacro argument to the full two-robot
description. Each macro includes the resulting rules for the whole assembly,
including inter-arm pairs. The matrices use the description's default track
dimensions, travel, separation, and mock tool geometry. The updater's sampled
`Never` exclusions are estimates, not proof that a pair cannot collide. These
macros provide the default standalone SRDF; they are not used as the collision
matrix by the fake MoveIt launch.

To regenerate the matrices in a sourced development workspace:

```sh
ros2 run preentend_moveit_config generate_collision_matrices \
  --output-dir src/preentend_moveit_config/srdf/collision_matrices
```

To generate for non-default dimensions, pass overrides such as
`--xacro-arg separation:=3.0`. Use the same dimensions when expanding the
robot description.

The generator checks that all arm collision meshes exist, fails if any model
cannot be generated, and writes the result only after all models succeed.

## Fake hardware launch

```sh
ros2 launch preentend_moveit_config preentend_moveit_fake.launch.py robot_model:=kr30_r2100
```

The launch includes the fake control launch from `preentend_ros2_control`,
then starts MoveIt and RViz. It loads the individual and combined trajectory controllers
inactive; MoveIt's `Ros2ControlManager` activates and switches them as needed.
The default model is `kr30_r2100`. The matching URDF, SRDF, initial positions,
and joint limits from `preentend_description/config/joint_limits` are selected
together. `separation`, `track_length`, `track_width`, `track_height`,
`carrier_length`, `carrier_width`, `carrier_height`, and `travel` can also be
passed as launch arguments.

On the first launch for a particular description, MoveIt Setup Assistant's
`collisions_updater` samples the full assembly and generates its SRDF. The
result is cached under `$XDG_CACHE_HOME/preentend_moveit_config/collisions`,
or `~/.cache/preentend_moveit_config/collisions` if `XDG_CACHE_HOME` is unset.
Repeated launches reuse it; changing the URDF arguments, expanded robot,
collision meshes, semantic groups, updater executable, or sample count produces
a new matrix. Use `collision_trials` to set the sample count (default 100,000)
and `collision_cache_dir` to choose the cache directory. Missing collision
meshes or generation errors stop the launch instead of reusing another matrix.
As with the pre-generated matrices, sampled `Never` exclusions require review
for the intended application.
