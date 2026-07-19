cmake_minimum_required(VERSION 3.0.2)
project(gazebo_sim_camera)

find_package(catkin REQUIRED COMPONENTS
  gazebo_msgs
  gazebo_ros
  rospy
  sensor_msgs
  tf
  xacro
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/camera_contract_test.py
  scripts/drive_intrinsic_calibration.py
  scripts/keyboard_camera_teleop.py
  scripts/web_calibration.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY
  config
  launch
  models
  process-definitions
  rviz
  test
  urdf
  web
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
  USE_SOURCE_PERMISSIONS
)
install(FILES process-definitions/gazebo-static-camera.json
  DESTINATION /usr/share/xgc2/process-definitions
)

if(CATKIN_ENABLE_TESTING)
  find_package(rostest REQUIRED)
  catkin_add_nosetests(test/test_intrinsic_sweep.py)
  catkin_add_nosetests(test/test_keyboard_camera_teleop.py)
  catkin_add_nosetests(test/test_web_calibration.py)
  add_rostest(test/static_camera_contract.test)
endif()
