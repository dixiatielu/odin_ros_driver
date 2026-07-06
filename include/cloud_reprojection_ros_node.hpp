/*
Copyright 2025 Manifold Tech Ltd.(www.manifoldtech.com.co)
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
   http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

#pragma once

#if __has_include(<cv_bridge/cv_bridge.hpp>)
#include <cv_bridge/cv_bridge.hpp>  // ROS 2 Iron/Jazzy+
#else
#include <cv_bridge/cv_bridge.h>  // ROS 2 Humble
#endif
#include <image_transport/image_transport.hpp>
#include <message_filters/subscriber.h>
#include <message_filters/sync_policies/approximate_time.h>
#include <message_filters/synchronizer.h>
#include <nav_msgs/msg/odometry.hpp>
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>
#include <pcl_conversions/pcl_conversions.h>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>

#include "cloud_reprojector.hpp"

#include <memory>
#include <string>

class CloudReprojectionRosNode : public rclcpp::Node
{
public:
    explicit CloudReprojectionRosNode(const rclcpp::NodeOptions& options = rclcpp::NodeOptions());

private:
    using PointCloud2 = sensor_msgs::msg::PointCloud2;
    using Odometry = nav_msgs::msg::Odometry;

    std::string cloud_slam_topic_;
    std::string odometry_topic_;
    std::string wiwc_topic_;
    std::string reprojected_image_topic_;

    message_filters::Subscriber<PointCloud2> cloud_sub_;
    message_filters::Subscriber<Odometry> odom_sub_;
    message_filters::Subscriber<Odometry> wiwc_sub_;

    using MySyncPolicy = message_filters::sync_policies::ApproximateTime<PointCloud2, Odometry, Odometry>;
    using Sync = message_filters::Synchronizer<MySyncPolicy>;
    std::shared_ptr<Sync> sync_;

    image_transport::Publisher reprojected_image_pub_;
    std::unique_ptr<CloudReprojector> reprojector_;

    void loadParameters();
    void syncCallback(const PointCloud2::ConstSharedPtr& cloud_msg,
                      const Odometry::ConstSharedPtr& odom_msg,
                      const Odometry::ConstSharedPtr& wiwc_msg);
};
