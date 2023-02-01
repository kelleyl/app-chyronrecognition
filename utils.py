import math
from east_utils import image_to_east_boxes
import numpy as np
import cv2

def get_chyron(frame, threshold=.03):
    boxes = image_to_east_boxes(frame)
    text_box_mask = np.zeros(frame.shape)
    for box in boxes: # box is (startX, startY, endX, endY)
        text_box_mask[box[1]:box[3],box[0]:box[2]] = 1
    bottom_third = text_box_mask[math.floor(.6 * frame.shape[0]):,:]
    top = text_box_mask[:math.floor(.6 * frame.shape[0]),:]
    if np.sum(top) / (top.shape[0] * top.shape[1]) > .5:
        return None
    if np.sum(bottom_third) / (bottom_third.shape[0] * bottom_third.shape[1]) > threshold:
        return boxes #todo kelley currently this is returning all east boxes not just chyron
    return None

def preprocess(image:np.array):
    image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    image = cv2.bitwise_not(image)
    image = cv2.resize(image, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    # image = cv2.medianBlur(image, 3)
    # image = cv2.bilateralFilter(image,9,75,75)

    return image
    