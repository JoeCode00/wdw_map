import select
import time
import cv2
import evdev
import numpy as np

from numbers import Integral
from pathlib import Path

from src.screenshot import capture, display_image, save_image
from src.compositor import Map
from src.launch_app import get_client_addresses, start_app, wait_for_new_window, move_window_to_monitor, get_loc, app_size_check, activate_map, is_app_running, stop_app
from src.terminal import run

SCREENSHOT_X1 = 38
SCREENSHOT_Y1 = 210
SCREENSHOT_X2 = 978
SCREENSHOT_Y2 = 810

ANDROID_SAFE_CLICK_X = 0
ANDROID_SAFE_CLICK_Y = 0

SHORT_DELAY_TIME_SECONDS = 0.25
LONG_DELAY_TIME_SECONDS = 1
SCROLLING_DELAY_TIME = 0.5

PORTAL_BUTTONS = {
    'left': 1,
    'middle': 2,
    'right': 3,
}

def delay(delay_type: str | float = 'short') -> None:
    delay_time_seconds = 0
    if isinstance(delay_type, float):
        delay_time_seconds = delay_type
    elif isinstance(delay_type, str):
        match delay_type.lower():
            case 'short':
                delay_time_seconds = SHORT_DELAY_TIME_SECONDS
            case 'long':
                delay_time_seconds = LONG_DELAY_TIME_SECONDS
            case 'scrolling':
                delay_time_seconds = SCROLLING_DELAY_TIME
            case _:
                raise ValueError(f'Got delay type {delay_type} that does no map to any time value.')
    time.sleep(delay_time_seconds)

ANDROID_PACKAGE = 'com.disney.wdw.android'
HYPRLAND_WAYDROID_MONITOR = 'l'
HYPRLAND_WAYDROID_WINDOW_CLASS = 'waydroid.com.disney.wdw.android'
MAP_BUTTON_REL_X = 310
MAP_BUTTON_REL_Y = 912
MIN_WINDOW_HEIGHT = 1000

def app_startup() -> None:
    existing_addresses = get_client_addresses()
    started = start_app(ANDROID_PACKAGE)
    address = wait_for_new_window(existing_addresses=existing_addresses)
    if address is not None:
        move_window_to_monitor(address=address, monitor=HYPRLAND_WAYDROID_MONITOR)
    if not started:
        raise RuntimeError('App did not start.')
    loc = get_loc(client_class=HYPRLAND_WAYDROID_WINDOW_CLASS)
    if not app_size_check(loc=loc, min_window_height=MIN_WINDOW_HEIGHT):
        raise RuntimeError('App cannot be interacted with, does not meet size requirements.')
    time.sleep(0.5) #menu rendering pause
    activate_map(loc=loc, map_x=MAP_BUTTON_REL_X, map_y=MAP_BUTTON_REL_Y)

def generate_recovery(direction_hint:str) -> list:
    match direction_hint.lower()[0]:
        case 'u': return ['d', 'r', 'u', 'l']
        case 'l': return ['r', 'd', 'l', 'u']
        case 'r': return ['l', 'd', 'r', 'u']
        case 'd': return ['u', 'r', 'd', 'l']
        case _: return []

def recovery_path(steps:list, depth:int=1, max_depth:int=5)->list:
        print(f'entering recovery depth {depth}')
        recover = steps
        for recovery_step in steps:
            press_key(recovery_step)
            recover = make_image(direction_hint=recovery_step)
            if not recover:
                return []
            if depth < max_depth:
                recover = recovery_path(recover, depth + 1, max_depth)
                if not recover:
                    return []
        return recover

def make_image(direction_hint:str, first_image:bool=False)->list:
    try:
        time.sleep(1.5) #rendering delay
        image = capture(SCREENSHOT_X1, SCREENSHOT_Y1, SCREENSHOT_X2, SCREENSHOT_Y2)
        save_image(image, 'screenshot.png')
        map.add_image(new_image_path=Path('/home/joseph/Documents/GitHub/wdw_map/screenshot.png'),
                        direction_hint=direction_hint,
                        first_image=first_image)
        
        
        
        return []
    except Exception as e:
        print(e)
        print('Entering recovery')
        recover = generate_recovery(direction_hint=direction_hint)
        return recover


def press_key(key:str)->None:
    match key.lower()[0]:
        case 'u': run('ydotool key 103:1 103:0')  # Up
        case 'l': run('ydotool key 105:1 105:0')  # Left
        case 'r': run('ydotool key 106:1 106:0')  # Right
        case 'd': run('ydotool key 108:1 108:0')  # Down

# if __name__ == '__main__':
#     app_startup()
#     device = evdev.InputDevice("/dev/input/event8")
#     map = Map()
#     keyboard_keys = {103:'up', 105:'left', 106:'right', 108:'down'}
#     codes = list(keyboard_keys.keys())
#     make_image(direction_hint='l', first_image=True)
#     while is_app_running(client_class=HYPRLAND_WAYDROID_WINDOW_CLASS):
#         r, _, _ = select.select([device], [], [], 0.5)
#         if r:
#             for event in device.read():
#                 if event.type == evdev.ecodes.EV_KEY:
#                     if event.code in codes and event.value == 0:
#                         direction_hint = keyboard_keys[event.code]
#                         make_image(direction_hint=direction_hint)

#     stopped = stop_app()
#     if not stopped:
#         raise RuntimeError('App did not stop.')
#     print('App stopped.')
    
if __name__ == '__main__':
    # app_startup()
    time.sleep(5)
    device = evdev.InputDevice("/dev/input/event8")
    map = Map()

    make_image(direction_hint='l', first_image=True)
    direction_hint = 'left'
    recover = []
    count = 0
    while is_app_running(client_class=HYPRLAND_WAYDROID_WINDOW_CLASS):
        press_key(direction_hint)
        recover = make_image(direction_hint=direction_hint)
        
        if recover:
            recover = recovery_path(recover)
        if count%10 == 0:
            map.save_composite()
            # print('saved composite')
        count = count+1

    stopped = stop_app()
    if not stopped:
        raise RuntimeError('App did not stop.')
    print('App stopped.')

#add much higher need to match score and add retry screenshot before accepting lower.