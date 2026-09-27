import time
from numbers import Integral
from wayland_automation import Mouse
from src.screenshot import capture, display_image

SCREENSHOT_X1 = 32
SCREENSHOT_Y1 = 166
SCREENSHOT_X2 = 1048
SCREENSHOT_Y2 = 840

ANDROID_SAFE_CLICK_X = 20
ANDROID_SAFE_CLICK_Y = 100

SHORT_DELAY_TIME_SECONDS = 0.25
LONG_DELAY_TIME_SECONDS = 1
SCROLLING_DELAY_TIME = 0.5

mouse = Mouse()
def delay(delay_type:str|Integral = 'short') -> None:
    delay_time_seconds = 0
    if isinstance(delay_type, Integral):
        delay_time_seconds = delay_type
    else:
        match delay_type.lower():
            case 'short': delay_time_seconds = SHORT_DELAY_TIME_SECONDS
            case 'long': delay_time_seconds = LONG_DELAY_TIME_SECONDS
            case 'scrolling': delay_time_seconds = SCROLLING_DELAY_TIME
            case _: raise ValueError(f'Got delay type {delay_type} that does no map to any time value.')
    time.sleep(delay_time_seconds)
    
def click(x:int, y:int, button:str='left') -> None:
    mouse.click(x, y, button)
    delay()

def move_to(x:int, y:int) -> None:
    button = 'nothing'
    click(x, y, button)

def activate_android():
    click(ANDROID_SAFE_CLICK_X,
            ANDROID_SAFE_CLICK_Y)
    

activate_android()
image = capture(SCREENSHOT_X1, SCREENSHOT_Y1, SCREENSHOT_X2, SCREENSHOT_Y2)
display_image(image)