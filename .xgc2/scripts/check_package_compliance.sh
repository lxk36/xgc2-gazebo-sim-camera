#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"
export PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/tmp/xgc2-gazebo-sim-camera-pycache}"
bash -n .xgc2/scripts/*.sh
python3 -m py_compile scripts/camera_contract_test.py scripts/web_calibration.py .xgc2/scripts/xgc2_artifact_manifest.py
python3 test/static_product_contract.py
python3 -m json.tool process-definitions/gazebo-static-camera.json >/dev/null

required=(
  .github/workflows/ci.yml .github/workflows/release.yml .xgc2/product.yml
  .xgc2/scripts/build_debs_in_docker.sh .xgc2/scripts/check_installed_packages.sh
  .xgc2/scripts/check_package_compliance.sh .xgc2/scripts/package_debs.sh
  CMakeLists.txt LICENSE README.md package.xml
  launch/static_camera.launch launch/intrinsic_calibration_world.launch
  launch/extrinsic_calibration_world.launch launch/camera_ar_rviz.launch
  launch/web_calibration.launch web/index.html web/app.js web/style.css
  urdf/fixed_rgb_camera.urdf.xacro urdf/checkerboard_8x6.urdf.xacro
  urdf/calibration_marker.urdf.xacro config/extrinsic_markers_vrpn.yaml
  process-definitions/gazebo-static-camera.json test/static_camera_contract.test
  test/static_product_contract.py
)
for path in "${required[@]}"; do test -f "${path}" || { echo "Missing ${path}" >&2; exit 1; }; done

grep -q 'id: xgc2-gazebo-sim-camera' .xgc2/product.yml
grep -Eq '^version: [0-9]+\.[0-9]+\.[0-9]+-[0-9]+$' .xgc2/product.yml
grep -q 'PACKAGE="ros-noetic-xgc2-gazebo-sim-camera"' .xgc2/scripts/package_debs.sh
grep -q '<name>gazebo_sim_camera</name>' package.xml
grep -q 'id": "gazebo-static-camera"' process-definitions/gazebo-static-camera.json
grep -q '/usr/share/xgc2/process-definitions' CMakeLists.txt
grep -q 'PLUGIN_RELATIVE="usr/share/xgc2/process-definitions/gazebo-static-camera.json"' .xgc2/scripts/package_debs.sh

for xml in launch/*.launch test/*.test worlds/*.world; do xmllint --noout "${xml}"; done
# Direct expansion exercises every declared default.  This specifically guards
# against root-element substitutions that are evaluated before <xacro:arg>.
/opt/ros/noetic/bin/xacro urdf/fixed_rgb_camera.urdf.xacro >/dev/null
/opt/ros/noetic/bin/xacro urdf/checkerboard_8x6.urdf.xacro >/dev/null
/opt/ros/noetic/bin/xacro urdf/calibration_marker.urdf.xacro >/dev/null

# Also verify that launch-time mappings remain accepted.
/opt/ros/noetic/bin/xacro urdf/fixed_rgb_camera.urdf.xacro model_name:=test_camera camera_namespace:=usb_cam camera_link_frame:=usb_cam_link optical_frame:=usb_cam_optical_frame width:=320 height:=240 fps:=10 hfov:=1.0 near_clip:=0.05 far_clip:=20 noise_stddev:=0 >/dev/null
echo "Package compliance checks passed"
