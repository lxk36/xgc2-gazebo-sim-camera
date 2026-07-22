#!/usr/bin/env python3
"""Keep managed camera launches supervised after spawn_model exits."""

import rospy


def main() -> None:
    rospy.init_node("camera_lifecycle_keepalive")
    rospy.loginfo("Gazebo camera lifecycle keepalive is active")
    rospy.spin()


if __name__ == "__main__":
    main()
