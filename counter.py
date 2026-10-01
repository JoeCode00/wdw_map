import evdev
device = evdev.InputDevice("/dev/input/event8")
count = 0
for event in device.read_loop():
    if event.type == evdev.ecodes.EV_KEY:
        # if event.code == 108 and event.value == 0:
        #     count = count + 1
        #     print(count)
        print(event)
        # up = 103
        # down = 108
        # left = 105
        # right = 106