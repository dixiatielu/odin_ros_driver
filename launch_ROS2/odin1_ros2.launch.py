# USAGE: ros2 launch odin_ros_driver odin1_ros2.launch.py
import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode
from launch_ros.parameter_descriptions import ParameterValue


def _load_yaml(path):
    with open(path, "r") as stream:
        return yaml.safe_load(stream) or {}


def _enabled(config, key, default=0):
    value = (config.get("register_keys") or {}).get(key, default)
    try:
        return int(value) != 0
    except (TypeError, ValueError):
        return bool(value)


def _component_extra_args():
    return [
        {
            "use_intra_process_comms": ParameterValue(
                LaunchConfiguration("use_intra_process_comms"),
                value_type=bool,
            )
        }
    ]


def _launch_setup(context, *args, **kwargs):
    del args, kwargs

    package_dir = get_package_share_directory("odin_ros_driver")
    config_file = LaunchConfiguration("config_file").perform(context)
    rviz_config = LaunchConfiguration("rviz_config").perform(context)
    use_composition = LaunchConfiguration("use_composition").perform(context).lower()
    launch_rviz = LaunchConfiguration("launch_rviz").perform(context).lower()

    config = _load_yaml(config_file)
    calib_path = os.path.join(package_dir, "config", "calib.yaml")

    if use_composition not in ("1", "true", "yes", "on"):
        return _standalone_nodes(config_file, config, calib_path, rviz_config, launch_rviz)

    components = [
        ComposableNode(
            package="odin_ros_driver",
            plugin="odin_ros_driver::HostSdkSampleComponent",
            name="host_sdk_sample",
            parameters=[{"config_file": config_file}],
            extra_arguments=_component_extra_args(),
        )
    ]
    fallback_nodes = []
    messages = []

    if _enabled(config, "senddepth"):
        if os.path.exists(calib_path):
            depth_params = dict(config)
            depth_params["calib_file_path"] = calib_path
            components.append(
                ComposableNode(
                    package="odin_ros_driver",
                    plugin="odin_ros_driver::DepthImageRos2Component",
                    name="pcd2depth_ros2_node",
                    parameters=[depth_params, _load_yaml(calib_path)],
                    extra_arguments=_component_extra_args(),
                )
            )
        else:
            messages.append(
                "senddepth is enabled, but calib.yaml is not available at launch time; "
                "starting pcd2depth_ros2_node as a standalone fallback."
            )
            fallback_nodes.append(
                Node(
                    package="odin_ros_driver",
                    executable="pcd2depth_ros2_node",
                    name="pcd2depth_ros2_node",
                    output="screen",
                    parameters=[dict(config, calib_file_path=calib_path)],
                )
            )

    if _enabled(config, "sendreprojection"):
        if os.path.exists(calib_path):
            components.append(
                ComposableNode(
                    package="odin_ros_driver",
                    plugin="CloudReprojectionRosNode",
                    name="cloud_reprojection_ros2_node",
                    parameters=[config],
                    extra_arguments=_component_extra_args(),
                )
            )
        else:
            messages.append(
                "sendreprojection is enabled, but calib.yaml is not available at launch time; "
                "starting cloud_reprojection_ros2_node as a standalone fallback."
            )
            fallback_nodes.append(
                Node(
                    package="odin_ros_driver",
                    executable="cloud_reprojection_ros2_node",
                    name="cloud_reprojection_ros2_node",
                    output="screen",
                    parameters=[config],
                )
            )

    if _enabled(config, "sendoverlay"):
        components.append(
            ComposableNode(
                package="odin_ros_driver",
                plugin="ImageOverlayNode",
                name="image_overlay_node",
                parameters=[config],
                extra_arguments=_component_extra_args(),
            )
        )

    actions = [
        ComposableNodeContainer(
            package="rclcpp_components",
            executable="component_container_mt",
            name="odin_zero_copy_container",
            namespace="",
            output="screen",
            composable_node_descriptions=components,
        )
    ]
    actions.extend(LogInfo(msg=message) for message in messages)
    actions.extend(fallback_nodes)

    if launch_rviz in ("1", "true", "yes", "on"):
        actions.append(_rviz_node(rviz_config))

    return actions


def _standalone_nodes(config_file, config, calib_path, rviz_config, launch_rviz):
    actions = [
        Node(
            package="odin_ros_driver",
            executable="host_sdk_sample",
            name="host_sdk_sample",
            output="screen",
            parameters=[{"config_file": config_file}],
        )
    ]

    if _enabled(config, "senddepth"):
        actions.append(
            Node(
                package="odin_ros_driver",
                executable="pcd2depth_ros2_node",
                name="pcd2depth_ros2_node",
                output="screen",
                parameters=[dict(config, calib_file_path=calib_path)],
            )
        )

    if _enabled(config, "sendreprojection"):
        actions.append(
            Node(
                package="odin_ros_driver",
                executable="cloud_reprojection_ros2_node",
                name="cloud_reprojection_ros2_node",
                output="screen",
                parameters=[config],
            )
        )

    if _enabled(config, "sendoverlay"):
        actions.append(
            Node(
                package="odin_ros_driver",
                executable="image_overlay_node",
                name="image_overlay_node",
                output="screen",
                parameters=[config],
            )
        )

    if launch_rviz in ("1", "true", "yes", "on"):
        actions.append(_rviz_node(rviz_config))

    return actions


def _rviz_node(rviz_config):
    return Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config],
    )


def generate_launch_description():
    package_dir = get_package_share_directory("odin_ros_driver")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "config_file",
                default_value=os.path.join(package_dir, "config", "control_command.yaml"),
                description="Path to the control config YAML file.",
            ),
            DeclareLaunchArgument(
                "rviz_config",
                default_value=os.path.join(package_dir, "config", "odin_ros2.rviz"),
                description="Path to RViz2 config file.",
            ),
            DeclareLaunchArgument(
                "launch_rviz",
                default_value="true",
                description="Launch RViz2.",
            ),
            DeclareLaunchArgument(
                "use_composition",
                default_value="true",
                description="Launch Odin C++ nodes in a composable container.",
            ),
            DeclareLaunchArgument(
                "use_intra_process_comms",
                default_value="true",
                description="Enable rclcpp intra-process zero-copy for composable Odin C++ nodes.",
            ),
            OpaqueFunction(function=_launch_setup),
        ]
    )
