#!/usr/bin/env python3
# convert Lekato cube turner events to GENERAL MIDI CC 
# note that Lekato in Apple mode sends keybord events
# in android mode sends touch events

import argparse
import sys

import evdev
from evdev import ecodes

import mido
from mido import Message

kcodes = ecodes.ecodes
keyMap = {
    kcodes['KEY_LEFT']:16,
    kcodes['KEY_RIGHT']:17,
    kcodes['KEY_UP']:18,
    kcodes['KEY_DOWN']:19,
}

args = None

def key_code_to_midi_note(code):
    try:
        return keyMap[code]
    except KeyError:
        return None

def _list_devices():
    print("Devices:")
    devs = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
    for dev in devs:
        print("    %s %s" % (dev.path, dev.name))

def _find_lekato_dev():
    devs = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
    for dev in devs:
        if dev.name == "CubeTurner Keyboard":
            return dev
            break

    return None


def parse_channel(string):
    val = int(string)
    if val < 1 or val > 16:
        raise argparse.ArgumentTypeError("Invalid channel number %r" % string)
    return val - 1

def _send_message(port, msg):
    if args.verbose:
        print("Sent", msg)
    port.send(msg)

def main():
    parser = argparse.ArgumentParser(description="Lekato turner to MIDI")

    parser.add_argument(
        '-d', '--device', help="imput device pat eg: /dev/input/event15",
        dest='device_path')

    parser.add_argument(
        '-l', '--list', help="List MIDI input ports, input devices and quit",
        dest='list', action='store_true')

    parser.add_argument('-n', '--port-name', help="MIDI output port name to create",
        dest='port_name', default="lekatoMidiPort")

    parser.add_argument('-c', '--channel', help="MIDI channel number (1-16)",
        dest='channel', type=parse_channel, default=10)

    parser.add_argument('-g', '--grab', help="Grab input device, swallow input events",
        dest='grab', action='store_true')

    parser.add_argument('-v', '--verbose', help="Print MIDI messages",
        dest='verbose', action='store_true')

    global args
    args = parser.parse_args()

    if args.list:
        _list_devices()
        sys.exit(0)

    if args.device_path is None:
        lekato_dev = _find_lekato_dev()
        if lekato_dev is None:
            print('Lekato dev not found!')
            parser.print_help()
            sys.exit(1)
        else:
            args.device_path = lekato_dev.path

    midiout = port = mido.open_output(args.port_name, virtual=True)
    dev = evdev.InputDevice(args.device_path)

    if args.grab:
        dev.grab()

    for ev in dev.read_loop():
        if ev.type == evdev.ecodes.EV_KEY:
            note = key_code_to_midi_note(ev.code)
            if note is not None:
                if ev.value == 0:
                    if args.verbose:
                        print(f'note off: {note}')
                    _send_message(midiout, Message('control_change', channel=args.channel , control=note , value=0))
                else:
                    if args.verbose:
                        print(f'note on: {note}')
                    _send_message(midiout, Message('control_change', channel=args.channel , control=note , value=127))

    if args.grab:
        dev.ungrab()

if __name__ == '__main__':
    try:
       ret = main()
    except (KeyboardInterrupt, EOFError):
        ret = 0
    sys.exit(ret)
