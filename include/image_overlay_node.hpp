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

#include <cv_bridge/cv_bridge.hpp>
#include <opencv2/opencv.hpp>
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <std_msgs/msg/header.hpp>

#include <memory>
#include <mutex>
#include <string>

class ImageOverlayNode : public rclcpp::Node
{
public:
    explicit ImageOverlayNode(const rclcpp::NodeOptions& options = rclcpp::NodeOptions());

private:
    using Image = sensor_msgs::msg::Image;

    std::string reprojected_topic_;
    std::string camera_topic_;
    std::string overlay_topic_;
    double alpha_;

    rclcpp::Subscription<Image>::SharedPtr reproj_sub_;
    rclcpp::Subscription<Image>::SharedPtr camera_sub_;
    rclcpp::Publisher<Image>::SharedPtr overlay_pub_;

    cv::Mat latest_reproj_img_;
    cv::Mat latest_camera_img_;
    std_msgs::msg::Header latest_header_;
    std::mutex mutex_;

    void reprojCallback(const Image::ConstSharedPtr& msg);
    void cameraCallback(const Image::ConstSharedPtr& msg);
    void publishOverlay();
};
