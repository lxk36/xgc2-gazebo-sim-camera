#!/usr/bin/env python3

import copy
import importlib.util
import math
import sys
import unittest
from unittest import mock
from pathlib import Path

from geometry_msgs.msg import Pose


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
SPEC = importlib.util.spec_from_file_location(
    "keyboard_camera_teleop", str(SCRIPT_DIR / "keyboard_camera_teleop.py")
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class KeyboardCameraTeleopTest(unittest.TestCase):
    def pose(self):
        pose = Pose()
        pose.orientation.w = 1.0
        return pose

    def test_w_is_throttle_up(self):
        pose = self.pose()
        result, changed = MODULE.apply_key(ord("W"), pose, copy.deepcopy(pose), 0.2, 0.1)
        self.assertTrue(changed)
        self.assertAlmostEqual(result.position.z, 0.2)  # drone throttle up

    def test_arrow_up_moves_forward(self):
        pose = self.pose()
        result, changed = MODULE.apply_key(MODULE.KEY_UP, pose, copy.deepcopy(pose), 0.2, 0.1)
        self.assertTrue(changed)
        self.assertAlmostEqual(result.position.x, 0.2)  # right stick forward

    def test_space_restores_initial_pose(self):
        pose = self.pose()
        pose.position.x = 4.0
        initial = self.pose()
        initial.position.x = -4.0
        result, changed = MODULE.apply_key(ord(" "), pose, initial, 0.2, 0.1)
        self.assertTrue(changed)
        self.assertAlmostEqual(result.position.x, -4.0)
        self.assertIsNot(result, initial)

    def test_yaw_key_keeps_quaternion_normalized(self):
        pose = self.pose()
        result, changed = MODULE.apply_key(ord("A"), pose, copy.deepcopy(pose), 0.2, 0.1)
        self.assertTrue(changed)
        norm = math.sqrt(
            result.orientation.x ** 2
            + result.orientation.y ** 2
            + result.orientation.z ** 2
            + result.orientation.w ** 2
        )
        self.assertAlmostEqual(norm, 1.0)

    def test_keyboard_stream_is_line_buffered(self):
        # gz block-buffers its pipe stdout, so keypresses must be un-batched with
        # stdbuf -oL or the camera freezes and then lurches.
        command = MODULE.keyboard_stream_command("/gazebo/calibration/keyboard/keypress")
        self.assertEqual(command[:3], ["stdbuf", "-oL", "gz"])
        self.assertEqual(command[-4:], ["gz", "topic", "-e", "/gazebo/calibration/keyboard/keypress"])

    @mock.patch.object(MODULE.subprocess, "check_output")
    def test_private_keyboard_topic_is_resolved_from_gazebo_world(self, check_output):
        check_output.return_value = "/gazebo/calibration/keyboard/keypress\n"
        self.assertEqual(
            MODULE.resolve_keyboard_topic("~/keyboard/keypress"),
            "/gazebo/calibration/keyboard/keypress",
        )


if __name__ == "__main__":
    unittest.main()
