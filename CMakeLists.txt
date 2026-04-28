cmake_minimum_required(VERSION 3.16)
project(odin_ros_driver)

add_compile_definitions(ROS2)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

find_package(ament_cmake REQUIRED)
find_package(ament_index_cpp REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(image_transport REQUIRED)
find_package(pcl_conversions REQUIRED)
find_package(message_filters REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)

find_package(PkgConfig REQUIRED)
find_package(OpenCV REQUIRED)
find_package(Eigen3 REQUIRED)
find_package(PCL REQUIRED)
find_package(yaml-cpp REQUIRED)
find_package(OpenSSL REQUIRED)
pkg_check_modules(LIBUSB REQUIRED libusb-1.0)

execute_process(
    COMMAND uname -m
    OUTPUT_VARIABLE ARCH
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

if(ARCH MATCHES "arm|aarch64")
    set(LYD_HOST_API_LIB_NAME "lydHostApi_arm")
    message(STATUS "Detected ARM architecture: ${ARCH}")
else()
    set(LYD_HOST_API_LIB_NAME "lydHostApi_amd")
    message(STATUS "Detected x86 architecture: ${ARCH}")
endif()

set(LIB_DIR "${CMAKE_CURRENT_SOURCE_DIR}/lib")
find_library(LYD_HOST_API_LIB
    NAMES ${LYD_HOST_API_LIB_NAME} lib${LYD_HOST_API_LIB_NAME}.a lib${LYD_HOST_API_LIB_NAME}.so
    PATHS ${LIB_DIR}
    NO_DEFAULT_PATH
)

if(NOT LYD_HOST_API_LIB)
    message(FATAL_ERROR "Could not find precompiled ${LYD_HOST_API_LIB_NAME} in ${LIB_DIR}")
endif()

set(ROS2_DEPS
    ament_index_cpp
    rclcpp
    std_msgs
    sensor_msgs
    nav_msgs
    visualization_msgs
    geometry_msgs
    cv_bridge
    image_transport
    pcl_conversions
    message_filters
    tf2
    tf2_ros
    tf2_geometry_msgs
)

set(COMMON_LIBS
    ${OpenCV_LIBS}
    ${PCL_LIBRARIES}
    yaml-cpp
    OpenSSL::SSL
    OpenSSL::Crypto
    ${LIBUSB_LIBRARIES}
    pthread
    rt
    ${CMAKE_DL_LIBS}
)

include_directories(
    include
    ${EIGEN3_INCLUDE_DIRS}
    ${OpenCV_INCLUDE_DIRS}
    ${PCL_INCLUDE_DIRS}
    ${LIBUSB_INCLUDE_DIRS}
)

add_executable(host_sdk_sample
    src/host_sdk_sample.cpp
    src/yaml_parser.cpp
    src/rawCloudRender.cpp
    src/camera_pose_visualization.cpp
)
ament_target_dependencies(host_sdk_sample ${ROS2_DEPS})
target_link_libraries(host_sdk_sample
    ${COMMON_LIBS}
    ${LYD_HOST_API_LIB}
)

add_library(pointcloud_depth_converter_ros2 src/pointcloud_depth_converter.cpp)
target_link_libraries(pointcloud_depth_converter_ros2
    ${OpenCV_LIBS}
    ${PCL_LIBRARIES}
)

add_library(depth_image_ros2_node_lib src/depth_image_ros2_node.cpp)
ament_target_dependencies(depth_image_ros2_node_lib
    rclcpp
    sensor_msgs
    std_msgs
    cv_bridge
    image_transport
    pcl_conversions
    message_filters
)
target_link_libraries(depth_image_ros2_node_lib
    pointcloud_depth_converter_ros2
    ${OpenCV_LIBS}
    ${PCL_LIBRARIES}
)

add_executable(pcd2depth_ros2_node src/pcd2depth_ros2.cpp)
ament_target_dependencies(pcd2depth_ros2_node
    rclcpp
    sensor_msgs
    std_msgs
    cv_bridge
    image_transport
    pcl_conversions
    message_filters
)
target_link_libraries(pcd2depth_ros2_node
    depth_image_ros2_node_lib
    yaml-cpp
)

add_library(cloud_reprojector_ros2 src/cloud_reprojector.cpp)
target_link_libraries(cloud_reprojector_ros2
    ${OpenCV_LIBS}
    ${PCL_LIBRARIES}
)

add_executable(cloud_reprojection_ros2_node src/cloud_reprojection_ros.cpp)
ament_target_dependencies(cloud_reprojection_ros2_node
    rclcpp
    sensor_msgs
    nav_msgs
    cv_bridge
    image_transport
    pcl_conversions
    message_filters
)
target_link_libraries(cloud_reprojection_ros2_node
    cloud_reprojector_ros2
    yaml-cpp
)

add_executable(image_overlay_node src/image_overlay_node.cpp)
ament_target_dependencies(image_overlay_node
    rclcpp
    sensor_msgs
    cv_bridge
    image_transport
    message_filters
)
target_link_libraries(image_overlay_node ${OpenCV_LIBS})

install(TARGETS
    host_sdk_sample
    pcd2depth_ros2_node
    cloud_reprojection_ros2_node
    image_overlay_node
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION lib/${PROJECT_NAME}
)

install(DIRECTORY include/
    DESTINATION include
)

install(DIRECTORY launch_ROS2/
    DESTINATION share/${PROJECT_NAME}/launch
)

install(DIRECTORY config/
    DESTINATION share/${PROJECT_NAME}/config
)

ament_export_dependencies(${ROS2_DEPS})
ament_package()

message(STATUS "=======================================")
message(STATUS "Project: ${PROJECT_NAME}")
message(STATUS "ROS: ROS 2 / ament")
message(STATUS "Architecture: ${ARCH}")
message(STATUS "lydHostApi library: ${LYD_HOST_API_LIB}")
message(STATUS "=======================================")
