#!/usr/bin/env python3

"""
This example shows usage of Camera Control message to change exposure and iso for grey camera
Uses 'IOKL' for manual exposure/focus:
  Control:      key[dec/inc]  min..max
  exposure time:     I   O      1..33000 [us]
  sensitivity iso:   K   L    100..1600
To go back to auto controls:
  'E' - autoexposure
"""
import os
import sys

import depthai as dai
import cv2

sys.path.insert(0, os.path.realpath('../'))
from modules.settings import Settings

settings = Settings("../grey.yaml")

default_settings = {
    "exp": 1000,
    "iso": 400
}

settings.update_defaults(default_settings)

# Manual exposure/focus set step
EXP_STEP = 100  # us
ISO_STEP = 50

pipeline = dai.Pipeline()

# Nodes
camLeft = pipeline.createMonoCamera()
camLeft.setBoardSocket(dai.CameraBoardSocket.LEFT)
camLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_720_P)

# Create control input
controlIn = pipeline.createXLinkIn()
controlIn.setStreamName('control')

# Create output
xoutLeft = pipeline.createXLinkOut()
xoutLeft.setStreamName('left')

# Link nodes
camLeft.out.link(xoutLeft.input)
controlIn.out.link(camLeft.inputControl)

def clamp(num, v0, v1):
    return max(v0, min(num, v1))


# Pipeline is defined, now we can connect to the device
with dai.Device(pipeline) as dev:

    # Get data queues
    controlQueue = dev.getInputQueue('control')
    qLeft = dev.getOutputQueue(name="left", maxSize=4, blocking=False)
    frameLeft = None

    # Start pipeline
    dev.startPipeline()

    expTime = settings["exp"]
    expMin = 1
    expMax = 33000

    sensIso = settings["iso"]
    sensMin = 100
    sensMax = 1600

    ctrl = dai.CameraControl()
    ctrl.setManualExposure(expTime, sensIso)
    controlQueue.send(ctrl)

    while True:

        inLeft = qLeft.tryGet()

        if inLeft is not None:
            frameLeft = inLeft.getCvFrame()

        # show the frames if available
        if frameLeft is not None:
            cv2.imshow("left", frameLeft)

        # Update screen
        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif key == ord('c'):
            ctrl = dai.CameraControl()
            ctrl.setCaptureStill(True)
            controlQueue.send(ctrl)
        elif key == ord('e'):
            print("Autoexposure enable")
            ctrl = dai.CameraControl()
            ctrl.setAutoExposureEnable()
            controlQueue.send(ctrl)
        elif key in [ord('i'), ord('o'), ord('k'), ord('l')]:
            if key == ord('i'): expTime -= EXP_STEP
            if key == ord('o'): expTime += EXP_STEP
            if key == ord('k'): sensIso -= ISO_STEP
            if key == ord('l'): sensIso += ISO_STEP
            expTime = clamp(expTime, expMin, expMax)
            settings.update_value("exp", expTime)
            sensIso = clamp(sensIso, sensMin, sensMax)
            settings.update_value("iso", sensIso)
            print("Setting manual exposure, time:", expTime, "iso:", sensIso)
            ctrl = dai.CameraControl()
            ctrl.setManualExposure(expTime, sensIso)
            controlQueue.send(ctrl)
