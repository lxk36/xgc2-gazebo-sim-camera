#!/usr/bin/env python3
import math
import threading
import time
import unittest

import rospy
import tf
from sensor_msgs.msg import CameraInfo, Image


class CameraContractTest(unittest.TestCase):
    def wait_for_camera_pair(self, image_topic, info_topic, timeout):
        condition = threading.Condition()
        images = {}
        infos = {}
        matched = [None]

        def trim(messages):
            while len(messages) > 64:
                messages.pop(next(iter(messages)))

        def on_image(message):
            key = message.header.stamp.to_nsec()
            with condition:
                images[key] = message
                trim(images)
                if key in infos:
                    matched[0] = (message, infos[key])
                    condition.notify_all()

        def on_info(message):
            key = message.header.stamp.to_nsec()
            with condition:
                infos[key] = message
                trim(infos)
                if key in images:
                    matched[0] = (images[key], message)
                    condition.notify_all()

        image_subscriber = rospy.Subscriber(
            image_topic, Image, on_image, queue_size=30, buff_size=2**24
        )
        info_subscriber = rospy.Subscriber(info_topic, CameraInfo, on_info, queue_size=30)
        deadline = time.monotonic() + timeout
        try:
            with condition:
                while matched[0] is None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0.0:
                        self.fail(
                            "no Image/CameraInfo pair with an identical stamp arrived within {:.1f}s".format(
                                timeout
                            )
                        )
                    condition.wait(remaining)
            return matched[0]
        finally:
            image_subscriber.unregister()
            info_subscriber.unregister()

    def test_camera_contract(self):
        image_topic = rospy.get_param("~image_topic", "/usb_cam/image_raw")
        info_topic = rospy.get_param("~camera_info_topic", "/usb_cam/camera_info")
        frame_id = rospy.get_param("~frame_id", "usb_cam_optical_frame")
        parent_frame = rospy.get_param("~parent_frame", "map")
        width = int(rospy.get_param("~width", 320))
        height = int(rospy.get_param("~height", 240))
        hfov = float(rospy.get_param("~hfov", 1.0471975512))

        image, info = self.wait_for_camera_pair(image_topic, info_topic, timeout=45.0)

        self.assertEqual((image.width, image.height), (width, height))
        self.assertEqual((info.width, info.height), (width, height))
        self.assertEqual(image.header.frame_id, frame_id)
        self.assertEqual(info.header.frame_id, frame_id)
        self.assertFalse(image.header.stamp.is_zero())
        self.assertEqual(image.header.stamp, info.header.stamp)
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
