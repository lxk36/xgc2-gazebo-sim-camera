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

The target is the shared `model://checkerboard_8x6` asset (8 by 6 squares / 7 by
5 inner corners, `0.20 m`), composed into the `camera_calibration_intrinsic`
world in the `gazebo_sim_worlds` package — this launch only spawns and drives the
camera. Gazebo's ideal pinhole camera publishes the ground-truth `CameraInfo`;
run the normal ROS camera calibrator on the same two topics to exercise an
intrinsic-calibration workflow. Move the *camera* to several poses with
`/gazebo/set_model_state` to collect geometrically diverse samples.

The calibration world spawns the camera in movable mode (`static:=false`) and
repositions it by publishing `gazebo_msgs/ModelState` on the
`/gazebo/set_model_state` topic; the standalone `static_camera.launch` keeps
`static:=true` so its fixed-site camera stays pinned. (A `<static>true</static>`
model is excluded from physics, so `set_model_state` cannot move it — movable
mode instead disables the link's gravity so the camera floats and can be
teleported.) With the ROS Noetic `camera_calibration` GUI open for the 7 by 5
inner-corner board, this assisted sweep moves the camera through far, near, edge
and oblique views. It mirrors the official X/Y/Size/Skew acceptance ranges and
restores the initial pose afterward:

```bash
rosrun gazebo_sim_camera drive_intrinsic_calibration.py \
  --image-topic /usb_cam/image_raw --board-size 7x5
```

When all four GUI bars are green, press `CALIBRATE` and then `SAVE` in the
official calibration window.

For manual UE-style camera movement, click the Gazebo render area so it has
keyboard focus. The intrinsic world starts the native Gazebo keyboard capture
plugin and the Python pose controller by default:

Controls follow a drone RC "Mode 2" layout:

```text
W / S          throttle up / down (altitude)
A / D          yaw left / right
Arrow keys     forward-back (up/down) / strafe (left/right)
Q / E          pitch (aim up / down)
Z / C          roll
+ / -          increase / decrease movement step
Space          restore the launch pose
H              show controls
Esc            stop keyboard control
```

Set `keyboard_teleop:=false` when launching the intrinsic world to disable it.

## Web calibration UI

`web_calibration.py` runs the whole *move camera → collect samples → calibrate →
commit* flow in a browser. It reuses ROS `camera_calibration`'s CV engine
unchanged (subclassing its `CalibrationNode` and replacing only the OpenCV
window), and moves the camera over the same `/gazebo/set_model_state` topic as
the keyboard teleop. The backend is Python standard library only
(`http.server` + an MJPEG stream); the frontend is dependency-free HTML/JS.

Start the world without the native keyboard teleop (so the web node is the only
authority on the camera pose), then launch the UI:

```bash
roslaunch gazebo_sim_camera intrinsic_calibration_world.launch \
  gui:=true keyboard_teleop:=false
roslaunch gazebo_sim_camera web_calibration.launch   # or: rosrun ... web_calibration.py
```

Open `http://localhost:8080`. The left pane is the live corner-overlaid image;
the right pane keeps the X/Y/Size/Skew bars, the `Calibrate` / `Save` / `Commit`
buttons, and a 3D **sample guide**: grey spheres are the poses still to capture,
the amber-ringed one is next, green means captured, and the blue dot is the live
camera. Below it, a reference snapshot shows roughly what that pose should look
like (pre-record the set once with `curl -XPOST localhost:8080/record_refs`).
Click the page and fly the camera manually with the drone Mode 2 keys (`W/S`
throttle, `A/D` yaw, arrows forward-back/strafe, `Q/E` pitch, `Z/C` roll) until a
sphere greens. `Commit` uploads through `/usb_cam/set_camera_info` (saved to
`~/.ros/camera_info/usb_cam.yaml`); `Save` writes `/tmp/calibrationdata.tar.gz`.

Pass `extra_args:="--no-camera-control"` to serve calibration only. Do not run
the native keyboard teleop at the same time — both publish camera poses.

## Extrinsic scene and VRPN

```bash
# Ground-truth visualization
roslaunch gazebo_sim_camera camera_ar_rviz.launch mode:=truth

# Assisted calibration: no truth camera TF is emitted
roslaunch gazebo_sim_camera extrinsic_calibration_world.launch \
  mode:=calibration publish_truth_tf:=false
```

Six independent, colored, non-coplanar markers named `cal_marker_01` through
`cal_marker_06` (the shared `model://cal_marker_*` assets) are composed into the
`camera_calibration_extrinsic` world in `gazebo_sim_worlds`.
`config/extrinsic_markers_vrpn.yaml` maps them to the same VRPN tracker names
through the existing `gazebo_sim_vrpn_bridge`.
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
