cmake_minimum_required(VERSION 3.8)
project(preentend_perception)

find_package(ament_cmake REQUIRED)

install(PROGRAMS scripts/fuse_point_clouds scripts/filter_point_cloud DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY launch DESTINATION share/${PROJECT_NAME})

ament_package()
