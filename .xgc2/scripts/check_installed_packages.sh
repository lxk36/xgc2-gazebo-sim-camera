#!/usr/bin/env bash
set -euo pipefail

ROS_DISTRO="${ROS_DISTRO:-noetic}"
source "/opt/ros/${ROS_DISTRO}/setup.bash"
SHARE="/opt/ros/${ROS_DISTRO}/share/gazebo_sim_camera"
PLUGIN="/usr/share/xgc2/process-definitions/gazebo-static-camera.json"

dpkg -s ros-noetic-xgc2-gazebo-sim-camera >/dev/null
test "$(rospack find gazebo_sim_camera)" = "${SHARE}"
test -x "/opt/ros/${ROS_DISTRO}/lib/gazebo_sim_camera/camera_contract_test.py"
test -x "/opt/ros/${ROS_DISTRO}/lib/gazebo_sim_camera/camera_lifecycle_keepalive.py"
test -f "${SHARE}/urdf/fixed_rgb_camera.urdf.xacro"
test -f "${SHARE}/process-definitions/gazebo-static-camera.json"
test -f "${PLUGIN}"
cmp -s "${SHARE}/process-definitions/gazebo-static-camera.json" "${PLUGIN}"
grep -q '<static>true</static>' "${SHARE}/urdf/fixed_rgb_camera.urdf.xacro"
grep -q '<robotNamespace>/</robotNamespace>' "${SHARE}/urdf/fixed_rgb_camera.urdf.xacro"
grep -q '<cameraName>$(arg camera_namespace)</cameraName>' "${SHARE}/urdf/fixed_rgb_camera.urdf.xacro"
grep -q '<imageTopicName>image_raw</imageTopicName>' "${SHARE}/urdf/fixed_rgb_camera.urdf.xacro"
grep -q '<cameraInfoTopicName>camera_info</cameraInfoTopicName>' "${SHARE}/urdf/fixed_rgb_camera.urdf.xacro"
grep -q 'type="camera_lifecycle_keepalive.py"' "${SHARE}/launch/static_camera.launch"
python3 -m json.tool "${SHARE}/process-definitions/gazebo-static-camera.json" >/dev/null
python3 -m json.tool "${PLUGIN}" >/dev/null

roslaunch --files gazebo_sim_camera static_camera.launch gui:=false >/dev/null
roslaunch --files gazebo_sim_camera intrinsic_calibration_world.launch gui:=false >/dev/null
roslaunch --files gazebo_sim_camera extrinsic_calibration_world.launch gui:=false start_vrpn:=false >/dev/null
echo "Installed package check passed"
