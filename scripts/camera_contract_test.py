#!/usr/bin/env python3
import math
import unittest

import rospy
import tf
from sensor_msgs.msg import CameraInfo, Image


class CameraContractTest(unittest.TestCase):
    def test_camera_contract(self):
        image_topic = rospy.get_param("~image_topic", "/usb_cam/image_raw")
        info_topic = rospy.get_param("~camera_info_topic", "/usb_cam/camera_info")
        frame_id = rospy.get_param("~frame_id", "usb_cam_optical_frame")
        parent_frame = rospy.get_param("~parent_frame", "map")
        width = int(rospy.get_param("~width", 320))
        height = int(rospy.get_param("~height", 240))
        hfov = float(rospy.get_param("~hfov", 1.0471975512))

        image = rospy.wait_for_message(image_topic, Image, timeout=45.0)
        info = rospy.wait_for_message(info_topic, CameraInfo, timeout=15.0)

        self.assertEqual((image.width, image.height), (width, height))
        self.assertEqual((info.width, info.height), (width, height))
        self.assertEqual(image.header.frame_id, frame_id)
        self.assertEqual(info.header.frame_id, frame_id)
        self.assertFalse(image.header.stamp.is_zero())
        self.assertLess(abs((image.header.stamp - info.header.stamp).to_sec()), 0.2)
        self.assertGreater(len(image.data), 0)
        self.assertEqual(len(info.K), 9)
        expected_fx = width / (2.0 * math.tan(hfov / 2.0))
        self.assertAlmostEqual(info.K[0], expected_fx, delta=max(2.0, expected_fx * 0.03))
        self.assertAlmostEqual(info.K[8], 1.0, places=6)

        listener = tf.TransformListener()
        listener.waitForTransform(parent_frame, frame_id, rospy.Time(0), rospy.Duration(20.0))
        translation, rotation = listener.lookupTransform(parent_frame, frame_id, rospy.Time(0))
        self.assertEqual(len(translation), 3)
        self.assertAlmostEqual(sum(value * value for value in rotation), 1.0, delta=1.0e-4)


if __name__ == "__main__":
    import rostest

    rospy.init_node("gazebo_sim_camera_contract_test")
    rostest.rosrun("gazebo_sim_camera", "camera_contract", CameraContractTest)
