#!/usr/bin/env python3

import os
import curses
import random
import time
import datetime
import sys
from adafruit_servokit import ServoKit

_TITLE = 'IDLE BOT'

_VERSION = 'Version 2.2.9'

_TAG_STATUS = '  STATUS: '
_TAG_INFO = '  INFO: '
_TAG_PROMPT = '  COMMAND: '
_TAG_HELP = '  HELP: '

_STATUS_STOPPED = 'STOPPED'
_STATUS_QUITTING = 'QUITTING...'
_STATUS_RELOADING = 'RELOADING...'

_COMMAND_INVALID = 'INVALID KEY'

_COLOR_NORMAL = 1
_COLOR_INVERSE = 2
_COLOR_RED = 3
_COLOR_GREEN = 4
_COLOR_BLUE = 5

class Screen:
    def __init__(self, window):
        self.window = window
        self.row_status = 6
        self.row_info = self.row_status + 3
        self.row_help = self.row_info + 3
        self.row_prompt = self.row_help + 3
        curses.init_pair(_COLOR_NORMAL, curses.COLOR_WHITE, curses.COLOR_BLACK)    
        curses.init_pair(_COLOR_INVERSE, curses.COLOR_BLACK, curses.COLOR_WHITE)    
        curses.init_pair(_COLOR_RED, curses.COLOR_RED, curses.COLOR_BLACK)    
        curses.init_pair(_COLOR_GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(_COLOR_BLUE, curses.COLOR_BLUE, curses.COLOR_BLACK)    

    def _clear(self):
        (max_y, _) = self.window.getmaxyx()
        for row in range(3, max_y - 5):
            self.window.move(row, 0)
            self.window.clrtoeol()

    def _add_header(self):
        (_, max_x) = self.window.getmaxyx()
        for row in range(0, 3):
            self.window.addstr(row, 0, ' ' * max_x, curses.color_pair(_COLOR_INVERSE))
        pos_x = int( (max_x / 2) - (len(_TITLE) / 2) )
        self.window.addstr(1, pos_x, _TITLE, curses.color_pair(_COLOR_INVERSE))

    def _add_footer(self):
        (max_y, max_x) = self.window.getmaxyx()
        for row in range(max_y - 4, max_y - 1):
            self.window.addstr(row, 0, ' ' * max_x, curses.color_pair(_COLOR_INVERSE))
        pos_x = 2
        date = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        self.window.addstr(max_y - 3, pos_x, date, curses.color_pair(_COLOR_INVERSE))
        pos_x = max_x - len(_VERSION) - 2
        self.window.addstr(max_y - 3, pos_x, _VERSION, curses.color_pair(_COLOR_INVERSE))

    def _add_status(self, status, color=_COLOR_NORMAL, bold=False):
        self.window.move(self.row_status, 0)
        self.window.clrtoeol()
        self.window.addstr(self.row_status, 0, _TAG_STATUS)
        if bold:
            color_pair = curses.color_pair(color) | curses.A_BOLD
        else:
            color_pair = curses.color_pair(color)
        if status:
            self.window.addstr(self.row_status, len(_TAG_STATUS), status, color_pair)

    def _add_info(self, info=None):
        self.window.move(self.row_info, 0)
        self.window.clrtoeol()
        self.window.addstr(self.row_info, 0, _TAG_INFO)
        if info:
            color_pair = curses.color_pair(_COLOR_NORMAL) | curses.A_BOLD
            self.window.addstr(self.row_info, len(_TAG_INFO), info, color_pair)

    def _add_prompt(self, error=None):
        self.window.move(self.row_prompt, 0)
        self.window.clrtoeol()
        self.window.addstr(self.row_prompt, 0, _TAG_PROMPT)
        if error:
            self.window.addstr(self.row_prompt, len(_TAG_PROMPT), error, curses.color_pair(_COLOR_RED) | curses.A_BOLD)

    def _add_help(self, help=None):
        self.window.move(self.row_help, 0)
        self.window.clrtoeol()
        self.window.addstr(self.row_help, 0, _TAG_HELP)

        if not help:
            return

        start_x = len(_TAG_HELP)
        
        in_key = False
        color_pair = curses.color_pair(_COLOR_NORMAL)
        for c in help:
            if c == '(':
                in_key = True
            elif c == ')':
                in_key = False
                color_pair = curses.color_pair(_COLOR_NORMAL)
            elif in_key:
                color_pair = curses.color_pair(_COLOR_BLUE) | curses.A_BOLD

            self.window.addstr(self.row_help, start_x, c, color_pair)

            start_x += 1

    def _get_allowed_keys(self, help):
        keys = []
        in_key = False
        for c in help:
            if c == '(':
                in_key = True
            elif c == ')':
                in_key = False
            elif in_key:
                keys.append(c.lower())
        return keys
        
    def main(self, status, error=None):
        self.row_help = self.row_status + 3
        self.row_prompt = self.row_help + 3
        self._add_header()
        self._add_footer()
        self._clear()
        if status == _STATUS_STOPPED:
            self._add_status(status, color=_COLOR_RED, bold=True)
            self._add_help('(R)un, Re(L)oad, (Q)uit')
            self._add_prompt(error=error)
        elif status == _STATUS_QUITTING or status == _STATUS_RELOADING:
            self._add_status(status, color=_COLOR_RED, bold=True)

        self.window.refresh()

        if status == _STATUS_QUITTING or status == _STATUS_RELOADING:
            time.sleep(1)

    def running(self, status, info=None, error=None, help=None):
        self.row_help = self.row_info + 3
        self.row_prompt = self.row_help + 3
        self._add_header()
        self._add_footer()
        self._clear()
        self._add_status(status, color=_COLOR_GREEN, bold=True)
        self._add_info(info=info)
        self._add_help(help=help)
        self._add_prompt(error=error)
        self.window.refresh()

    def moving(self, status):
        self._add_header()
        self._add_footer()
        self._clear()
        self._add_status(status, color=_COLOR_GREEN, bold=True)
        self.window.refresh()

    def get_key(self, timeout=-1):
        self.window.timeout(timeout)
        return(self.window.getch())

    def sleep_or_get_key(self, sleep, status, help):
        elapsed = 0
        start = int(time.time())
        allowed_keys = self._get_allowed_keys(help)
        while elapsed < sleep:
            info = 'Sleeping %d of %d Seconds' % (elapsed + 1, sleep)
            self.running(status, info=info, help=help)
            key = self.get_key(timeout=100)
            if key == -1:
                # timeout
                pass
            elif key not in [ord(k) for k in allowed_keys]:
                # invalid key
                self.running(status, info=info, error=_COMMAND_INVALID, help=help)
                time.sleep(.5)
            else:
                # valid key
                break
            elapsed = int(time.time()) - start
        return key

def bot(window):
    global ret
    screen = Screen(window)
    servo = 0

    while True:
        screen.main(_STATUS_STOPPED)

        key = screen.get_key(timeout=500)

        if key == ord('r'):
            while True:
                status = 'RUNNING: Servo to NEUTRAL...'
                screen.moving(status)
                move_servo(servo, servo_config[servo]['start'])

                sleep = random.randrange(45, 75)
                status = 'RUNNING: Servo NEUTRAL'
                help = '(E)ngage, (S)top, Re(L)oad, (Q)uit'
                key = screen.sleep_or_get_key(sleep, status, help)

                if key == ord('s'):
                    screen.main(_STATUS_STOPPED)
                    break
                elif key == ord('q'):
                    screen.main(_STATUS_QUITTING)
                    return
                elif key == ord('l'):
                    screen.main(_STATUS_RELOADING)
                    ret = 2
                    return

                status = 'RUNNING: Servo to ENGAGED...'
                screen.moving(status)
                move_servo(servo, servo_config[servo]['engage'])

                sleep = random.randrange(5, 10)
                status = 'RUNNING: Servo ENGAGED'
                help = '(N)eutral, (S)top, Re(L)oad, (Q)uit'
                key = screen.sleep_or_get_key(sleep, status, help)

                if key == ord('s'):
                    servo_start()
                    screen.main(_STATUS_STOPPED)
                    break
                elif key == ord('q'):
                    servo_start()
                    screen.main(_STATUS_QUITTING)
                    return
                elif key == ord('l'):
                    servo_start()
                    screen.main(_STATUS_RELOADING)
                    ret = 2
                    return

        elif key == ord('q'):
            screen.main(_STATUS_QUITTING)
            return

        elif key == ord('l'):
            screen.main(_STATUS_RELOADING)
            ret = 2
            return

        elif key != -1:
            screen.main(_STATUS_STOPPED, error=_COMMAND_INVALID)
            time.sleep(.5)
        
def servo_start():
    for servo, config in enumerate(servo_config):
        angle = config['start']
        config['current'] = angle
        kit.servo[servo].angle = angle

def move_servo(servo, end_angle):
    current_angle = servo_config[servo]['current']

    if current_angle == end_angle:
        return
    elif end_angle > current_angle:
        diff = 1
    elif end_angle < current_angle:
        diff = -1

    while current_angle != end_angle:
        current_angle += diff
        kit.servo[servo].angle = current_angle
        time.sleep(.01)

    servo_config[servo]['current'] = current_angle

kit = ServoKit(channels=16)

servo_config = [
    {
        'start':    135,
        'engage':   75,
        'current':  0,
    },
]

ret = 0

servo_start()

curses.wrapper(bot)

os.system('clear')

sys.exit(ret)
