import json
import time

from src.terminal import run, run_async
from src.mouse import click_at

def get_clients() -> str:
    output = run('hyprctl clients -j')
    return output

def get_client_addresses() -> set[str]:
    output = get_clients()
    return {client['address'] for client in json.loads(output)}

def wait_for_new_window(existing_addresses:set[str], timeout:float=15.0, poll_interval:float=0.25) -> str | None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        new_addresses = get_client_addresses() - existing_addresses
        if new_addresses:
            return next(iter(new_addresses))
        time.sleep(poll_interval)
    return None

def move_window_to_monitor(address:str, monitor:str='l') -> None:
    # focuswindow is required first since movewindow only acts on the active window
    run(f'hyprctl dispatch focuswindow address:{address}')
    run(f'hyprctl dispatch movewindow mon:{monitor}')

def start_app(package_name:str) -> bool:
    stop_app()
    try:    
        run_async(f'waydroid app launch {package_name}')
        time.sleep(20) #startup delay
        return True
    except Exception as e:
        print(e)
        return False

def stop_app() -> bool:
    try:
        run('waydroid session stop')
        return True
    except Exception as e:
        print(e)
        return False

def get_loc(client_class:str) -> dict:
    output = get_clients()
    output_list = json.loads(output)
    loc = {'at':[], 'size':[]}
    for client in output_list:
        if client['class'].lower() == client_class.lower():
            loc['at'] = client['at']
            loc['size'] = client['size']
    
    return loc

def is_app_running(client_class:str) -> bool:
    output = get_clients()
    output_list = json.loads(output)
    app_running = False
    for client in output_list:
        if client['class'].lower() == client_class.lower():
            app_running = True
            
    return app_running

def app_size_check(loc:dict, min_window_height:int) -> bool:
    size = loc['size']
    height = size[1]
    if height >= min_window_height:
        return True
    else:
        print(f'App window is too small, got height {height} < {min_window_height}')
        return False

def activate_map(loc:dict, map_x:int, map_y:int) -> bool:
    try:
        at = loc['at']
        at_x = at[0]
        at_y = at[1]
        map_button_x = int(at_x + map_x)
        map_button_y = int(at_y + map_y)
        click_at(x=map_button_x, y=map_button_y)
        return True
    except Exception as e:
        print(e)
        return False

if __name__ == '__main__':
    ANDROID_PACKAGE = 'com.disney.wdw.android'
    HYPRLAND_WAYDROID_MONITOR = 'l'
    HYPRLAND_WAYDROID_WINDOW_CLASS = 'waydroid.com.disney.wdw.android'
    MAP_BUTTON_REL_X = 310
    MAP_BUTTON_REL_Y = 912
    MIN_WINDOW_HEIGHT = 1000

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
    while is_app_running(client_class=HYPRLAND_WAYDROID_WINDOW_CLASS):
        pass
    stopped = stop_app()
    if not stopped:
        raise RuntimeError('App did not stop.')
    print('App stopped.')