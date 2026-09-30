import cv2
import numpy as np
import os

# OpenCV's bundled Qt plugins don't include "wayland"; force xcb (via XWayland)
# so cv2.imshow doesn't warn about a missing platform plugin.
os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
# OpenCV's bundled Qt has no fonts dir; QT_QPA_FONTDIR doesn't suppress the
# warning, so silence the qt.qpa.fonts logging category instead.
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.fonts=false")

def current_map_large_image(correlation_map, current_map, correlation_map_x, correlation_map_y):
    """
    Copies the current_map region corresponding to correlation_map, where
    (correlation_map_x, correlation_map_y) is the correlation_map's top-left in current_map coordinates.
    """
    correlation_map_height, correlation_map_width = correlation_map.shape[:2]
    current_map_height, current_map_width = current_map.shape[:2]

    # Find the current_maperlap in current_map coordinates.
    current_map_x1 = max(0, correlation_map_x)
    current_map_y1 = max(0, correlation_map_y)
    current_map_x2 = min(current_map_width, correlation_map_x + correlation_map_width)
    current_map_y2 = min(current_map_height, correlation_map_y + correlation_map_height)

    # If the region is completely out of bounds, return the original correlation_map.
    if current_map_x1 >= current_map_x2 or current_map_y1 >= current_map_y2:
        return correlation_map

    # Map the current_maperlap back to correlation_map coordinates.
    correlation_map_x1 = current_map_x1 - correlation_map_x
    correlation_map_y1 = current_map_y1 - correlation_map_y
    correlation_map_x2 = correlation_map_x1 + (current_map_x2 - current_map_x1)
    correlation_map_y2 = correlation_map_y1 + (current_map_y2 - current_map_y1)

    # Perform the slice and assignment
    correlation_map[correlation_map_y1:correlation_map_y2, 
                    correlation_map_x1:correlation_map_x2] = current_map[current_map_y1:current_map_y2,
                                                                         current_map_x1:current_map_x2]
    
    return correlation_map

# Example usage:
# Create a small correlation_map (e.g., 300x300) and a larger current_map (e.g., 500x500)
correlation_map = np.zeros((300, 300, 4), dtype=np.uint8)
correlation_map[:,:,3] = 255
correlation_map_x = -50
correlation_map_y = -50
# current_map = np.random.randint(0, 256, (500, 500, 3), dtype=np.uint8)
current_map = np.ones((20, 200, 4), dtype=np.uint8)*255

# The correlation_map's top-left is at (50, 50) in current_map coordinates.
result = current_map_large_image(correlation_map, current_map, correlation_map_x=correlation_map_x, correlation_map_y=correlation_map_y)

try:
    # cv2.imshow('correlation_map', correlation_map)
    # cv2.imshow('current_map', current_map)
    cv2.imshow('result', result)

    cv2.waitKey(0)
finally:
    cv2.destroyAllWindows()