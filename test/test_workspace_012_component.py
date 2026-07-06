from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_driver_keeps_upstream_012_firmware_gate():
    source = read("src/host_sdk_sample.cpp")

    assert '#define ros_driver_version "0.11.0"' in source
    assert "#define required_firmware_version_major 0" in source
    assert "#define required_firmware_version_minor 12" in source
    assert "#define required_firmware_version_patch 0" in source


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
