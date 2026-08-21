from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def section(source: str, start: str, end: str) -> str:
    start_index = source.index(start)
    end_index = source.index(end, start_index)
    return source[start_index:end_index]


def test_driver_keeps_rolled_back_012_firmware_gate():
    source = read("src/host_sdk_sample.cpp")

    assert '#define ros_driver_version "0.11.0"' in source
    assert "#define required_firmware_version_major 0" in source
    assert "#define required_firmware_version_minor 12" in source
    assert "#define required_firmware_version_patch 0" in source


def test_local_connection_config_files_are_ignored():
    gitignore = read(".gitignore")

    assert "/config/Conn*" in gitignore


def test_humble_and_jazzy_cv_bridge_headers_are_supported():
    for relative_path in (
        "include/cloud_reprojection_ros_node.hpp",
        "include/depth_image_ros2_node.hpp",
        "include/host_sdk_sample.h",
        "include/image_overlay_node.hpp",
    ):
        header = read(relative_path)
        assert "__has_include(<cv_bridge/cv_bridge.hpp>)" in header
        assert "<cv_bridge/cv_bridge.hpp>" in header
        assert "<cv_bridge/cv_bridge.h>" in header


def test_upstream_runtime_fixes_remain_after_013_rebase():
    source = read("src/host_sdk_sample.cpp")

    signal_handler = section(
        source,
        "static void signal_handler",
        "// Custom parameter monitoring function",
    )
    assert "stop_imu_thread();" in signal_handler

    start_imu_thread = section(
        source,
        "static void start_imu_thread",
        "// Stop IMU dedicated thread",
    )
    assert "if (g_imu_thread.joinable())" in start_imu_thread
    assert "g_imu_thread.join();" in start_imu_thread

    data_callback_preamble = section(
        source,
        "static void lidar_data_callback",
        "device_handle *dev_handle",
    )
    assert "if (!g_ros_object)" in data_callback_preamble

    stream_setup = section(
        source,
        "if (dtof_subframe_odr > 0)",
        "software_connect_timing = false",
    )
    for data_type in (
        "LIDAR_DT_RAW_RGB",
        "LIDAR_DT_RAW_IMU",
        "LIDAR_DT_SLAM_ODOMETRY",
        "LIDAR_DT_RAW_DTOF",
        "LIDAR_DT_SLAM_CLOUD",
    ):
        assert f"lidar_deactivate_stream_type(odinDevice, {data_type});" in stream_setup

    param_monitor_setup = section(
        source,
        "// Start custom parameter monitoring thread",
        "g_param_monitor_thread = std::thread(custom_parameter_monitor);",
    )
    assert "if (g_param_monitor_thread.joinable())" in param_monitor_setup
    assert "g_param_monitor_thread.join();" in param_monitor_setup

    relocalization_setup = section(
        source,
        "} else if (g_custom_map_mode == 2)",
        "// Transfer image mask if enabled",
    )
    assert "int retryTime = 3;" in relocalization_setup
    assert "while(retryTime-- > 0)" in relocalization_setup


def test_ros2_services_and_components_are_built_together():
    cmake = read("CMakeLists.txt")
    package_xml = read("package.xml")

    assert "rosidl_generate_interfaces" in cmake
    assert "srv/GetAe.srv" in cmake
    assert "rosidl_get_typesupport_target" in cmake
    assert "find_package(rclcpp_components REQUIRED)" in cmake
    assert "add_library(host_sdk_sample_core SHARED" in cmake
    assert "add_library(odin_ros_driver_components SHARED src/components.cpp)" in cmake
    assert "rclcpp_components_register_nodes(odin_ros_driver_components" in cmake
    assert '"odin_ros_driver::HostSdkSampleComponent"' in cmake
    assert "<depend>rclcpp_components</depend>" in package_xml
    assert "<buildtool_depend>rosidl_default_generators</buildtool_depend>" in package_xml


def test_host_sdk_sample_can_run_as_executable_or_component():
    source = read("src/host_sdk_sample.cpp")
    component = read("src/components.cpp")

    assert "int run_host_sdk_sample_node(" in source
    assert "void request_host_sdk_sample_stop()" in source
    assert "#ifndef ODIN_ROS_DRIVER_DISABLE_MAIN" in source
    assert "RCLCPP_COMPONENTS_REGISTER_NODE(odin_ros_driver::HostSdkSampleComponent)" in component


def test_auxiliary_ros2_nodes_can_be_linked_into_component_library():
    cloud_reprojection = read("src/cloud_reprojection_ros.cpp")
    image_overlay = read("src/image_overlay_node.cpp")

    assert "#ifndef ODIN_ROS_DRIVER_DISABLE_MAIN" in cloud_reprojection
    assert "#ifndef ODIN_ROS_DRIVER_DISABLE_MAIN" in image_overlay
