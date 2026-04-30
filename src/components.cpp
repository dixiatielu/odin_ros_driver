#include <chrono>
#include <memory>
#include <thread>

#include <rclcpp/rclcpp.hpp>
#include <rclcpp_components/register_node_macro.hpp>

#include "cloud_reprojection_ros_node.hpp"
#include "depth_image_ros2_node.hpp"
#include "image_overlay_node.hpp"

int run_host_sdk_sample_node(
    const rclcpp::Node::SharedPtr& node,
    bool spin_node,
    bool shutdown_context,
    bool install_signal_handlers);
void request_host_sdk_sample_stop();

namespace odin_ros_driver
{
using namespace std::chrono_literals;

class HostSdkSampleComponent : public rclcpp::Node
{
public:
    explicit HostSdkSampleComponent(const rclcpp::NodeOptions& options)
        : Node("lydros_node", options)
    {
        start_timer_ = this->create_wall_timer(1ms, [this]() {
            start_timer_->cancel();
            auto node = this->shared_from_this();
            worker_ = std::thread([node]() {
                run_host_sdk_sample_node(node, false, false, false);
            });
        });
    }

    ~HostSdkSampleComponent() override
    {
        request_host_sdk_sample_stop();
        if (worker_.joinable()) {
            worker_.join();
        }
    }

private:
    rclcpp::TimerBase::SharedPtr start_timer_;
    std::thread worker_;
};

class DepthImageRos2Component : public DepthImageRos2Node
{
public:
    explicit DepthImageRos2Component(const rclcpp::NodeOptions& options)
        : DepthImageRos2Node(options)
    {
        initialize_timer_ = this->create_wall_timer(1ms, [this]() {
            initialize_timer_->cancel();
            this->initialize();
        });
    }

private:
    rclcpp::TimerBase::SharedPtr initialize_timer_;
};

}  // namespace odin_ros_driver

RCLCPP_COMPONENTS_REGISTER_NODE(odin_ros_driver::HostSdkSampleComponent)
RCLCPP_COMPONENTS_REGISTER_NODE(odin_ros_driver::DepthImageRos2Component)
RCLCPP_COMPONENTS_REGISTER_NODE(CloudReprojectionRosNode)
RCLCPP_COMPONENTS_REGISTER_NODE(ImageOverlayNode)
