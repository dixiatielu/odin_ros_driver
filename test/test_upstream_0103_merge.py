from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _section(source: str, start: str, end: str) -> str:
    start_index = source.index(start)
    end_index = source.index(end, start_index)
    return source[start_index:end_index]


def _sha256(relative_path: str) -> str:
    return sha256((ROOT / relative_path).read_bytes()).hexdigest()


def test_host_sdk_sample_contains_upstream_0103_runtime_fixes():
    source = _read_text("src/host_sdk_sample.cpp")
    readme = _read_text("README.md")

    assert '#define ros_driver_version "0.10.3"' in source
    assert "Current version: v0.10.3" in readme

    signal_handler = _section(
        source,
        "static void signal_handler",
        "// Custom parameter monitoring function",
    )
    assert "stop_imu_thread();" in signal_handler

    start_imu_thread = _section(
        source,
        "static void start_imu_thread",
        "// Stop IMU dedicated thread",
    )
    assert "if (g_imu_thread.joinable())" in start_imu_thread
    assert "g_imu_thread.join();" in start_imu_thread

    data_callback_preamble = _section(
        source,
        "static void lidar_data_callback",
        "device_handle *dev_handle",
    )
    assert "if (!g_ros_object)" in data_callback_preamble

    stream_setup = _section(
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

    param_monitor_setup = _section(
        source,
        "// Start custom parameter monitoring thread",
        "g_param_monitor_thread = std::thread(custom_parameter_monitor);",
    )
    assert "if (g_param_monitor_thread.joinable())" in param_monitor_setup
    assert "g_param_monitor_thread.join();" in param_monitor_setup

    relocalization_setup = _section(
        source,
        "} else if (g_custom_map_mode == 2)",
        "// Transfer image mask if enabled",
    )
    assert "int retryTime = 3;" in relocalization_setup
    assert "while(retryTime-- > 0)" in relocalization_setup
    assert "Relocalization map invalid" in relocalization_setup


def test_overlay_callbacks_use_upstream_0103_ros2_signature():
    header = _read_text("include/image_overlay_node.hpp")
    implementation = _read_text("src/image_overlay_node.cpp")

    assert "void reprojCallback(Image::ConstSharedPtr msg);" in header
    assert "void cameraCallback(Image::ConstSharedPtr msg);" in header
    assert "void ImageOverlayNode::reprojCallback(Image::ConstSharedPtr msg)" in implementation
    assert "void ImageOverlayNode::cameraCallback(Image::ConstSharedPtr msg)" in implementation


def test_bundled_sdk_libraries_match_upstream_0103():
    assert (
        _sha256("lib/liblydHostApi_arm.a")
        == "4a908c33323eac22ac4435f8a8af7d40129a3b0699bc7420060e21e32a488b00"
    )
    assert (
        _sha256("lib/liblydHostApi_amd.a")
        == "7134be42f77299b3ee2cc46c1d2d379c69224548c5458d1ddf2e6f66fb743f57"
    )
