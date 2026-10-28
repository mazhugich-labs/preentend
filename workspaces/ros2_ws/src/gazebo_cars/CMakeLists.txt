cmake_minimum_required(VERSION 3.8)
project(gazebo_cars)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch models DESTINATION share/${PROJECT_NAME})

ament_package()
