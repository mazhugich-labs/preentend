# Mock camera description

This package provides a simplified D435-like RGB-D camera as two independent
xacro macros. The housing is a 90 × 25 × 25 mm box with a nominal mass of
75 g. Its origin is at the center; +X points forward, +Y left, and +Z up.
The optical frames use the ROS convention (+Z forward, +X right, +Y down).
The depth frame is at the same origin with +X forward for Gazebo point clouds.

```xml
<xacro:include filename="$(find mock_camera_description)/urdf/mock_camera_macro.xacro"/>
<xacro:include filename="$(find mock_camera_description)/urdf/mock_camera_gazebo_macro.xacro"/>
<xacro:mock_camera prefix="front_" parent="world">
  <origin xyz="0 0 1" rpy="0 0 0"/>
</xacro:mock_camera>
<xacro:mock_camera_gazebo prefix="front_" topic_prefix="/front_camera"/>
```

The Gazebo macro is optional and assumes that the matching description macro
has been instantiated. Give each camera a unique prefix and absolute topic
prefix. The world must load the Gazebo Sensors system with a rendering engine;
ROS users also need a `ros_gz_bridge` for the desired sensor topics. With the
example prefix, Gazebo publishes color images on `/front_camera/color/image`,
depth images on `/front_camera/depth`, point clouds on
`/front_camera/depth/points`, and camera info on
`/front_camera/{color,depth}/camera_info`.

The color and depth sensors default to 1280 × 720 at 30 Hz, with 69° and 87°
horizontal fields of view respectively. Depth clipping defaults to 0.28–10 m;
image sizes, frame rate and depth clipping can be overridden in the macro. The
housing dimensions, mass and FOV are based on the [D400 series datasheet](https://www.realsenseai.com/wp-content/uploads/2022/11/Intel-RealSense-D400-Series-Datasheet-November-2022.pdf)
and the [D435 specifications](https://www.realsenseai.com/products/stereo-depth-camera-d435/).

This is an approximation: optical centers are coincident, and the ideal
Gazebo depth camera does not simulate stereo matching, infrared images,
distortion, calibration, or realistic depth noise. The 10 m far clip is a
simulation setting, not a guaranteed measurement range. Color and depth have
different fields of view and are not registered images.
