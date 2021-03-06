#!/usr/bin/env python3

import depthai as dai
import os
import sys
import logging
import datetime

sys.path.insert(0, os.path.realpath('../'))
from modules.settings import Settings

settings_grey = Settings("../grey.yaml")
settings_color = Settings("../color.yaml")

logger = logging.getLogger(__name__)

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H.%M.%S")

record_dir = f"record_{timestamp}"

os.makedirs(record_dir, exist_ok=True)

def exec_out(cmd):
    logger.info(f"Executing: {cmd}")
    stream = os.popen(cmd)
    lines = stream.readlines()
    if lines:
        return lines[-1].strip("\n")
    else:
        return ""

mono1_path = os.path.join(record_dir, 'mono1.h264')
mono1_mp4_path = os.path.join(record_dir, 'mono1.mp4')
mono2_path = os.path.join(record_dir, 'mono2.h264')
mono2_mp4_path = os.path.join(record_dir, 'mono2.mp4')
color_path = os.path.join(record_dir, 'color.h265')
color_mp4_path = os.path.join(record_dir, 'color.mp4')

# Start defining a pipeline
pipeline = dai.Pipeline()

# Define a source - color and mono cameras
colorCam = pipeline.createColorCamera()
monoCam = pipeline.createMonoCamera()
monoCam.setBoardSocket(dai.CameraBoardSocket.LEFT)
monoCam2 = pipeline.createMonoCamera()
monoCam2.setBoardSocket(dai.CameraBoardSocket.RIGHT)

# Create encoders, one for each camera, consuming the frames and encoding them using H.264 / H.265 encoding
ve1 = pipeline.createVideoEncoder()
ve1.setDefaultProfilePreset(1280, 720, 30, dai.VideoEncoderProperties.Profile.H264_MAIN)
monoCam.out.link(ve1.input)

ve2 = pipeline.createVideoEncoder()
ve2.setDefaultProfilePreset(1920, 1080, 30, dai.VideoEncoderProperties.Profile.H265_MAIN)
colorCam.video.link(ve2.input)

ve3 = pipeline.createVideoEncoder()
ve3.setDefaultProfilePreset(1280, 720, 30, dai.VideoEncoderProperties.Profile.H264_MAIN)
monoCam2.out.link(ve3.input)

# Create control inputs
controlInGrey = pipeline.createXLinkIn()
controlInGrey.setStreamName('controlGrey')
controlInGrey.out.link(monoCam.inputControl)
controlInGrey.out.link(monoCam2.inputControl)

controlInColor = pipeline.createXLinkIn()
controlInColor.setStreamName('controlColor')
controlInColor.out.link(colorCam.inputControl)

# Create outputs
ve1Out = pipeline.createXLinkOut()
ve1Out.setStreamName('ve1Out')
ve1.bitstream.link(ve1Out.input)

ve2Out = pipeline.createXLinkOut()
ve2Out.setStreamName('ve2Out')
ve2.bitstream.link(ve2Out.input)

ve3Out = pipeline.createXLinkOut()
ve3Out.setStreamName('ve3Out')
ve3.bitstream.link(ve3Out.input)


# Pipeline is defined, now we can connect to the device
with dai.Device(pipeline) as dev:
    # Start pipeline
    dev.startPipeline()
    controlQueueGrey = dev.getInputQueue('controlGrey')
    controlQueueColor = dev.getInputQueue('controlColor')

    if settings_grey.get("exp") is not None and settings_grey.get("iso") is not None:
        ctrl = dai.CameraControl()
        ctrl.setManualExposure(settings_grey["exp"], settings_grey["iso"])
        controlQueueGrey.send(ctrl)

    if settings_color.get("autofocus") is not None:
        if not settings_color["autofocus"]:
            ctrl = dai.CameraControl()
            ctrl.setAutoFocusMode(dai.CameraControl.AutoFocusMode.AUTO)
            ctrl.setAutoFocusTrigger()
            controlQueueColor.send(ctrl)

    # Output queues will be used to get the encoded data from the outputs defined above
    outQ1 = dev.getOutputQueue(name='ve1Out', maxSize=30, blocking=True)
    outQ2 = dev.getOutputQueue(name='ve2Out', maxSize=30, blocking=True)
    outQ3 = dev.getOutputQueue(name='ve3Out', maxSize=30, blocking=True)

    # The .h264 / .h265 files are raw stream files (not playable yet)
    with open(mono1_path, 'wb') as fileMono1H264, open(color_path, 'wb') as fileColorH265, open(mono2_path, 'wb') as fileMono2H264:
        print("Press Ctrl+C to stop encoding...")
        while True:
            try:
                # Empty each queue
                while outQ1.has():
                    outQ1.get().getData().tofile(fileMono1H264)

                while outQ2.has():
                    outQ2.get().getData().tofile(fileColorH265)

                while outQ3.has():
                    outQ3.get().getData().tofile(fileMono2H264)
            except KeyboardInterrupt:
                # Keyboard interrupt (Ctrl + C) detected
                break

    print("Converting the stream files (.h264/.h265) into a video files (.mp4):")
    cmd = "ffmpeg -framerate 30 -i {} -c copy {}"
    rm_cmd = "rm {}"
    exec_out(cmd.format(mono1_path, mono1_mp4_path))
    exec_out(cmd.format(mono2_path, mono2_mp4_path))
    exec_out(cmd.format(color_path, color_mp4_path))
    exec_out(rm_cmd.format(mono1_path))
    exec_out(rm_cmd.format(mono2_path))
    exec_out(rm_cmd.format(color_path))
