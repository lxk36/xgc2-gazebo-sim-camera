#!/usr/bin/env python3
import json
import re
from pathlib import Path


root = Path(__file__).resolve().parents[1]
xacro = (root / "urdf/fixed_rgb_camera.urdf.xacro").read_text(encoding="utf-8")
launch = (root / "launch/static_camera.launch").read_text(encoding="utf-8")
extrinsic = (root / "launch/extrinsic_calibration_world.launch").read_text(encoding="utf-8")
markers = (root / "launch/extrinsic_markers.launch").read_text(encoding="utf-8")
checkerboard = (root / "urdf/checkerboard_8x6.urdf.xacro").read_text(encoding="utf-8")
world = (root / "worlds/calibration.world").read_text(encoding="utf-8")
rviz = (root / "rviz/camera_ar.rviz").read_text(encoding="utf-8")
definition = json.loads(
    (root / "process-definitions/gazebo-static-camera.json").read_text(encoding="utf-8")
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
assert "arg('mode') == 'calibration'" not in launch  # calibration deliberately publishes no TF group

assert '<arg name="vrpn_use_server_time" default="false"/>' in extrinsic
assert '<arg name="use_server_time" value="$(arg vrpn_use_server_time)"/>' in extrinsic
for material in ("Red", "Green", "Blue", "Yellow", "Purple", "Turquoise"):
    assert "Gazebo/" + material in markers
for marker in range(1, 7):
    assert f"/vrpn_client_node/cal_marker_{marker:02d}/pose" in rviz
assert "Image Topic: /usb_cam/image_raw" in rviz
assert checkerboard.count("<xacro:black_square") == 24
assert "<material>Gazebo/White</material>" in checkerboard
assert "<material>Gazebo/Black</material>" in checkerboard
assert "<preserveFixedJoint>true</preserveFixedJoint>" in checkerboard
assert "--gui-client-plugin libKeyboardGUIPlugin.so" in launch
assert 'type="keyboard_camera_teleop.py"' in (
    root / "launch/intrinsic_calibration_world.launch"
).read_text(encoding="utf-8")

positions = [
    tuple(map(float, values))
    for values in re.findall(
        r'name="spawn_cal_marker_\d+" args="[^"]* -x ([\d.-]+) -y ([\d.-]+) -z ([\d.-]+)"',
        markers,
    )
]
assert len(positions) == 6
a, b, c, d = positions[:4]
u = tuple(b[i] - a[i] for i in range(3))
v = tuple(c[i] - a[i] for i in range(3))
w = tuple(d[i] - a[i] for i in range(3))
volume6 = (
    u[0] * (v[1] * w[2] - v[2] * w[1])
    - u[1] * (v[0] * w[2] - v[2] * w[0])
    + u[2] * (v[0] * w[1] - v[1] * w[0])
)
assert abs(volume6) > 1.0e-6  # at least four targets are not coplanar

mode_values = definition["parameters"]["properties"]["mode"]["enum"]
assert mode_values == ["truth", "calibration", "validation"]
probe = definition["readiness"]
assert probe["kind"] == "exec"
assert probe["command"]["executable"] == "/opt/ros/noetic/bin/rostopic"
assert "/${cameraNamespace}/image_raw/header/stamp" in probe["command"]["args"]

print("Static product contracts passed")
