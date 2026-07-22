#!/usr/bin/env python3
import json
from pathlib import Path


root = Path(__file__).resolve().parents[1]
xacro = (root / "urdf/fixed_rgb_camera.urdf.xacro").read_text(encoding="utf-8")
launch = (root / "launch/static_camera.launch").read_text(encoding="utf-8")
extrinsic = (root / "launch/extrinsic_calibration_world.launch").read_text(encoding="utf-8")
rviz = (root / "rviz/camera_ar.rviz").read_text(encoding="utf-8")
keepalive = (root / "scripts/camera_lifecycle_keepalive.py").read_text(encoding="utf-8")
cmake = (root / "CMakeLists.txt").read_text(encoding="utf-8")
definition = json.loads(
    (root / "process-definitions/gazebo-static-camera.json").read_text(encoding="utf-8")
)["definitions"][0]
archived_definition = json.loads(
    (root / "process-definitions/gazebo-static-camera-0.4.0.json").read_text(
        encoding="utf-8"
    )
)["definitions"][0]

assert "<gazebo><static>true</static></gazebo>" in xacro  # static:=true default
# static:=false spawns a movable camera: it stays in physics (no <static>) but
# floats via disabled gravity so /gazebo/set_model_state can reposition it.
assert '<xacro:arg name="static" default="true"/>' in xacro
assert "<gravity>false</gravity>" in xacro
assert "static:=$(arg static)" in launch
assert '<arg name="static" value="$(arg camera_static)"/>' in (
    root / "launch/intrinsic_calibration_world.launch"
).read_text(encoding="utf-8")
assert "<robotNamespace>/</robotNamespace>" in xacro
assert "<cameraName>$(arg camera_namespace)</cameraName>" in xacro
assert "<imageTopicName>image_raw</imageTopicName>" in xacro
assert "<cameraInfoTopicName>camera_info</cameraInfoTopicName>" in xacro
assert "$(arg optical_frame)" in xacro
assert '<xacro:property name="body_depth" value="0.06"/>' in xacro
assert '<xacro:property name="body_side" value="0.14"/>' in xacro
assert '<xacro:property name="lens_length" value="0.035"/>' in xacro
assert '<xacro:property name="lens_radius" value="0.04"/>' in xacro
assert xacro.count("<geometry><cylinder") == 2  # matching lens visual and collision
assert '<material name="camera_black"><color rgba="0.02 0.02 0.02 1"/></material>' in xacro
assert "<material>Gazebo/Black</material>" in xacro

assert "arg('mode') == 'truth'" in launch
assert "arg('mode') == 'validation'" in launch
assert "gt_camera_link_frame" in launch and "gt_optical_frame" in launch
assert launch.count("arg('mode') == 'calibration'") == 1
assert "arg('mode') == 'calibration' or not arg('publish_truth_tf')" in launch
assert 'type="camera_lifecycle_keepalive.py"' in launch
assert 'name="$(arg model_name)_lifecycle_keepalive"' in launch
assert "rospy.init_node(\"camera_lifecycle_keepalive\")" in keepalive
assert "rospy.spin()" in keepalive
assert "scripts/camera_lifecycle_keepalive.py" in cmake

assert '<arg name="vrpn_use_server_time" default="false"/>' in extrinsic
assert '<arg name="use_server_time" value="$(arg vrpn_use_server_time)"/>' in extrinsic
for marker in range(1, 7):
    assert f"/vrpn_client_node/cal_marker_{marker:02d}/pose" in rviz
assert "Image Topic: /usb_cam/image_raw" in rviz
assert "--gui-client-plugin libKeyboardGUIPlugin.so" in launch
assert 'type="keyboard_camera_teleop.py"' in (
    root / "launch/intrinsic_calibration_world.launch"
).read_text(encoding="utf-8")

# The calibration checkerboard and markers are now shared model:// assets in the
# gazebo_sim_worlds package (models/checkerboard_8x6, models/cal_marker_*, and the
# camera_calibration_{intrinsic,extrinsic} worlds); they are validated by that
# package's own compliance, not here.

mode_values = definition["parameters"]["properties"]["mode"]["enum"]
assert definition["version"] == "0.5.0"
assert archived_definition["version"] == "0.4.0"
assert archived_definition["parameters"] == definition["parameters"]
assert archived_definition["command"] == definition["command"]
assert mode_values == ["truth", "calibration", "validation"]
assert definition["parameters"]["properties"]["startGazebo"]["default"] is False
assert definition["parameters"]["properties"]["cameraStatic"]["default"] is True
assert "start_gazebo:=${startGazebo}" in definition["command"]["args"]
assert "static:=${cameraStatic}" in definition["command"]["args"]
assert definition["beforeStart"]["command"]["args"][1] == "/gazebo/delete_model"
assert definition["beforeStop"]["command"]["args"][1] == "/gazebo/delete_model"
assert definition["resourceClaims"][0]["namespace"] == "gazebo-model"
probe = definition["readiness"]
assert probe["kind"] == "exec"
assert probe["command"]["executable"] == "/opt/ros/noetic/bin/rostopic"
assert "/${cameraNamespace}/image_raw/header/stamp" in probe["command"]["args"]

print("Static product contracts passed")
