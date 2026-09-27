import time
from numbers import Integral

from src.screenshot import capture, display_image
from launch_app import get_client_addresses, start_app, wait_for_new_window, move_window_to_monitor, get_loc, app_size_check, activate_map, is_app_running, stop_app

SCREENSHOT_X1 = 32
SCREENSHOT_Y1 = 166
SCREENSHOT_X2 = 1048
SCREENSHOT_Y2 = 840

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

def delay(delay_type: str | Integral = 'short') -> None:
    delay_time_seconds = 0
    if isinstance(delay_type, Integral):
        delay_time_seconds = delay_type
    else:
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
    time.sleep(1) #menu rendering pause
    activate_map(loc=loc, map_x=MAP_BUTTON_REL_X, map_y=MAP_BUTTON_REL_Y)


if __name__ == '__main__':
    app_startup()
    while is_app_running(client_class=HYPRLAND_WAYDROID_WINDOW_CLASS):
        pass
    stopped = stop_app()
    if not stopped:
        raise RuntimeError('App did not stop.')
    print('App stopped.')
    image = capture(SCREENSHOT_X1, SCREENSHOT_Y1, SCREENSHOT_X2, SCREENSHOT_Y2)
    display_image(image)