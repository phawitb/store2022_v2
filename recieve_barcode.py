from evdev import InputDevice, ecodes, list_devices, categorize
import signal, sys
import csv

def write_csv(filename,barcode):
	f = open(filename,'a')
	f.write(f'{barcode}\n')
	f.close()

keys = "X^1234567890XXXXqwertzuiopXXXXasdfghjklXXXXXyxcvbnmXXXXXXXXXXXXXXXXXXXXXXX"
scancodes = {
    # Scancode: ASCIICode
    0: None, 1: u'ESC', 2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8',
    10: u'9', 11: u'0', 12: u'-', 13: u'=', 14: u'BKSP', 15: u'TAB', 16: u'Q', 17: u'W', 18: u'E', 19: u'R',
    20: u'T', 21: u'Y', 22: u'U', 23: u'I', 24: u'O', 25: u'P', 26: u'[', 27: u']', 28: u'CRLF', 29: u'LCTRL',
    30: u'A', 31: u'S', 32: u'D', 33: u'F', 34: u'G', 35: u'H', 36: u'J', 37: u'K', 38: u'L', 39: u';',
    40: u'"', 41: u'`', 42: u'LSHFT', 43: u'\\', 44: u'Z', 45: u'X', 46: u'C', 47: u'V', 48: u'B', 49: u'N',
    50: u'M', 51: u',', 52: u'.', 53: u'/', 54: u'RSHFT', 56: u'LALT', 100: u'RALT'
}
barCodeDeviceString = "TMS HIDKeyBoard"

devices = map(InputDevice, list_devices())

for device in devices:
    if device.name == barCodeDeviceString:
        dev = InputDevice(device.path)
   

def signal_handler(signal, frame):
    print('Stopping')
    dev.ungrab()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

dev.grab()

barcode = ""
for event in dev.read_loop():
    if event.type == ecodes.EV_KEY:
        data = categorize(event)
        if data.keystate == 1 and data.scancode != 42: # Catch only keydown, and not Enter
            if data.scancode == 28:
                print('bbb',type(barcode),barcode)
                write_csv('data/current_barcode.csv',barcode)
                barcode = ""
            else:
                barcode += keys[data.scancode]
                

