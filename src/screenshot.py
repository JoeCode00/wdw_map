import os
import shutil
import subprocess
from pathlib import Path

# OpenCV's bundled Qt plugins don't include "wayland"; force xcb (via XWayland)
# so cv2.imshow doesn't warn about a missing platform plugin.
os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
# OpenCV's bundled Qt has no fonts dir; QT_QPA_FONTDIR doesn't suppress the
# warning, so silence the qt.qpa.fonts logging category instead.
os.environ.setdefault("QT_LOGGING_RULES", "qt.qpa.fonts=false")

import cv2
import numpy as np


def capture(x1:int, y1:int, x2:int, y2:int, filename:str="current_map_screenshot.png") -> np.ndarray:
	"""Capture a region of the Hyprland desktop with grim and return its pixels."""
	grim = shutil.which("grim")
	if grim is None:
		raise FileNotFoundError(
			"grim is not installed or is not on PATH. Install it with: "
			"sudo apt install grim -y"
		)
	if x1 < 0 or y1 < 0 or x2 <= x1 or y2 <= y1:
		raise ValueError(f"Invalid crop bounds {(x1, y1, x2, y2)}.")

	geometry = f"{x1},{y1} {x2 - x1}x{y2 - y1}"
	screenshot = Path(__file__).resolve().parent.parent / filename
	try:
		result = subprocess.run(
			[grim, "-g", geometry, str(screenshot)],
			capture_output=True,
			check=False,
			text=True,
			timeout=15,
		)
	except subprocess.TimeoutExpired as error:
		raise RuntimeError("grim did not finish capturing within 15 seconds.") from error

	if result.returncode != 0:
		detail = result.stderr.strip() or result.stdout.strip()
		raise RuntimeError(f"grim could not capture the screen. {detail}")
	if not screenshot.is_file():
		raise RuntimeError("grim completed without saving a screenshot.")

	image = cv2.imread(str(screenshot), cv2.IMREAD_COLOR)
	if image is None:
		raise RuntimeError(f"OpenCV could not read {screenshot}.")

	return image

def save_image(image:cv2.typing.MatLike, filename:str) -> Path:
	filename_split = filename.split('.')
	name = filename_split[0]
	extension = filename_split[1]
	if extension != 'png':
		raise ValueError(f'Images in this project are saved as .png, got {filename}.')
	filepath = Path(__file__).resolve().parent.parent / filename
	lossless_compression_level = 5
	cv2.imwrite(filepath, image, [cv2.IMWRITE_PNG_COMPRESSION, lossless_compression_level])
	return filepath

def display_image(image):
	try:
		cv2.imshow("Screenshot", image)
		cv2.waitKey(0)
	finally:
		cv2.destroyAllWindows()


if __name__ == "__main__":
	SCREENSHOT_X1 = 38
	SCREENSHOT_Y1 = 210
	SCREENSHOT_X2 = 978
	SCREENSHOT_Y2 = 810
	image = capture(SCREENSHOT_X1, SCREENSHOT_Y1, SCREENSHOT_X2, SCREENSHOT_Y2)
	save_image(image=image, filename='sc4.png')
