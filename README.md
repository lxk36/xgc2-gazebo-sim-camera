# XGC2 Gazebo Sim Camera

Independent fixed-site RGB camera product for Gazebo Classic 11 and ROS Noetic.
It intentionally contains no vehicle model and does not modify FS150, Scout, or
other robot camera definitions.

## Stable ROS contract

The default instance publishes:

- `/usb_cam/image_raw` (`sensor_msgs/Image`)
- `/usb_cam/camera_info` (`sensor_msgs/CameraInfo`)
- image and camera-info headers use `usb_cam_optical_frame`

`usb_cam_link -> usb_cam_optical_frame` uses the REP-103 rotation
`rpy=(-pi/2, 0, -pi/2)`. Every identity field is parameterized, so a second
instance must use a unique model name, namespace, camera-link frame, and optical
frame.

```bash
roslaunch gazebo_sim_camera static_camera.launch gui:=true

roslaunch gazebo_sim_camera static_camera.launch \
  camera_namespace:=yard_cam model_name:=yard_camera \
  camera_link_frame:=yard_cam_link optical_frame:=yard_cam_optical_frame \
  x:=-3 y:=2 z:=2 yaw:=-0.3
```

## TF ownership modes

- `mode:=truth publish_truth_tf:=true` publishes the exact Gazebo pose as
  `map -> <camera_link> -> <optical_frame>`.
- `mode:=calibration` publishes no camera TF, even if `publish_truth_tf` was
  left true. An external calibration result may therefore own
  `map -> <optical_frame>` without duplicate TF authorities.
- `mode:=validation` leaves the official camera frames to the calibration
  result and publishes truth only as
  `map -> <camera_link>_gt -> <optical_frame>_gt`. The GT frame names are
  parameterized by `gt_camera_link_frame` and `gt_optical_frame`.

Use truth mode for a standalone ground-truth demo, calibration mode while
estimating a transform, and validation mode to compare a published calibration
against a non-conflicting truth tree.

## Intrinsic scene

```bash
roslaunch gazebo_sim_camera intrinsic_calibration_world.launch gui:=true
```

The target has 8 by 6 squares (7 by 5 inner corners), each `0.20 m`. Camera and
board poses are launch arguments. Gazebo's ideal pinhole camera publishes the
ground-truth `CameraInfo`; run the normal ROS camera calibrator on the same two
topics to exercise an intrinsic-calibration workflow. Move the board to several
poses with `/gazebo/set_model_state` to collect geometrically diverse samples.

## Extrinsic scene and VRPN

```bash
# Ground-truth visualization
roslaunch gazebo_sim_camera camera_ar_rviz.launch mode:=truth

# Assisted calibration: no truth camera TF is emitted
roslaunch gazebo_sim_camera extrinsic_calibration_world.launch \
  mode:=calibration publish_truth_tf:=false
```

Six independent, colored, non-coplanar models named `cal_marker_01` through
`cal_marker_06` are spawned. `config/extrinsic_markers_vrpn.yaml` maps them to
the same VRPN tracker names through the existing `gazebo_sim_vrpn_bridge`.
The resulting poses are `/vrpn_client_node/cal_marker_XX/pose` in `map`.
This package does not copy or fork the VRPN bridge algorithm.
The client defaults to `vrpn_use_server_time:=false`, so pose headers use the
same simulated ROS clock as the camera frames and can be synchronized during
calibration.

`camera_ar_rviz.launch` overlays all six pose axes on the camera image using
RViz's Camera display. In calibration mode the overlay becomes valid once the
calibration TF publisher supplies `map -> usb_cam_optical_frame`.

## Test and package

```bash
source /opt/ros/noetic/setup.bash
catkin_make run_tests_gazebo_sim_camera
catkin_test_results

.xgc2/scripts/build_debs_in_docker.sh --output-dir "$PWD/debs"
```

The product CI builds and install-checks both amd64 and arm64 Debian packages.
The Debian package installs the ProcessDefinition plugin at the canonical
`/usr/share/xgc2/process-definitions/gazebo-static-camera.json` path (and keeps
a package-share copy for ROS tooling). Configure
`/usr/share/xgc2/process-definitions` in `XGC_PROCESS_DEFINITION_PLUGINS` for
XGC Core discovery alongside the physical camera definition.
