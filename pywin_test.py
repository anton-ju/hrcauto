
import logging
import os
import psutil
import subprocess
import re
import pyperclip
import hhparser as hh
import time
from hand_storage import HandStorage
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class HRCAuto:
    MAIN_WINDOW_TITLE = 'HoldemResources Calculator '
    BASIC_HAND_TITLE = 'Basic Hand Setup '
    CMD_ACTIVATE_MAIN = ['wmctrl', '-R', MAIN_WINDOW_TITLE]
    CMD_ACTIVATE_BASIC = ['wmctrl', '-R', BASIC_HAND_TITLE]
    CMD_BASIC_HAND = [
        ['xdotool', 'key', 'ctrl+w'],
        ['xdotool', 'key', 'p', 'sleep', '2']
    ]
    CMD_PASTE_CALCULATE = [
        'xdotool', 'mousemove', '421', '617',
        'sleep', '0.5', 'click', '1', 'key', 'Tab', 'sleep', '0.5', 'key', 'Return',
        'sleep', '2', 'key', 'Return', 'sleep', '2'
    ]
    NAME = 'default'
    CMD_SAVE_CLOSE = [
        ['xdotool', 'key', 'alt+h', 'sleep', '1'],
        ['xdotool', 'key', 'e', 'sleep', '1'],
        ['xdotool', 'key', 'Up', 'sleep', '1'],
        ['xdotool', 'key', 'Return', 'sleep', '3'],
        ['xdotool', 'type', NAME],
        ['xdotool', 'sleep', '1', 'key', 'Down', 'key', 'Down', 'key', 'Return', 'sleep', '1'],
        # ['xdotool', 'key', 'ctrl+F4']
    ]

    def __init__(self, hrc_path):
        self.errors = []
        self.out = []
        if not os.path.exists(hrc_path):
            raise ValueError('Invalid path to HRC')
        if not self.is_active():
            try:
                self._run_command(hrc_path)

            except:
                self.errors.append('HRC opening error')
            time.sleep(15)
            if self.check_errors() or not self.is_active():
                raise ValueError('HRC opening error')

    def calculate_basic(self, history, hid):
        # TODO how to do better and not change const???
        self.CMD_SAVE_CLOSE[4] = ['xdotool', 'type', hid]
        pyperclip.copy(history)
        if self.is_active():
            self._run_command_list(self.CMD_BASIC_HAND)
            self._run_command(self.CMD_PASTE_CALCULATE)

            for i in range(0, 40):
                time.sleep(3)
                if not self.is_calculating():
                    break
            if self.is_active():
                self._run_command_list(self.CMD_SAVE_CLOSE)
            else:
                self.errors.append('Error while saving hand')

        else:
            raise RuntimeError('Activation Error: HRC is not running')
        self.check_errors()

    def is_calculating(self):
        self._run_command(self.CMD_ACTIVATE_BASIC)
        time.sleep(1)
        if self._get_active_window_title() == self.BASIC_HAND_TITLE:
            return True
        else:
            return False

    def is_active(self):
        self._run_command(self.CMD_ACTIVATE_MAIN)
        time.sleep(1)
        if self._get_active_window_title() == self.MAIN_WINDOW_TITLE:
            return True
        else:
            return False

    def _run_command_list(self, cmdlist):
        if isinstance(cmdlist, list):
            for cmd in cmdlist:
                self._run_command(cmd)

    def _run_command(self, cmd):
        root = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        stdout, stderr = root.communicate()
        if stdout:
            self.out.append(stdout)

        if stderr:
            self.errors.append(stderr)

    @staticmethod
    def _find_procs_by_name(name):

        ls = []
        for p in psutil.process_iter(attrs=['name']):
            if p.info['name'] == name:
                ls.append(p)
        return ls

    @staticmethod
    def _get_active_window_title():
        root = subprocess.Popen(['xprop', '-root', '_NET_ACTIVE_WINDOW'], stdout=subprocess.PIPE)
        stdout, stderr = root.communicate()

        m = re.search(b'^_NET_ACTIVE_WINDOW.* ([\w]+)$', stdout)
        if m != None:
            window_id = m.group(1)
            window = subprocess.Popen(['xprop', '-id', window_id, 'WM_NAME'], stdout=subprocess.PIPE)
            stdout, stderr = window.communicate()
        else:
            return None

        match = re.match(b"WM_NAME\(\w+\) = (?P<name>.+)$", stdout)
        if match != None:
            return match.group("name").strip(b'"').decode('utf-8')

        return None

    def check_errors(self):
        if self.errors or self.out:
            for error in self.errors:
                logging.error(error)

            for out in self.out:
                logging.error(out)
            return True
        else:
            return False


if __name__ == '__main__':

    hs = HandStorage('test/')
    hrc = HRCAuto('/home/ant/holdemresources/calculator')
    for history in hs.read_hand():
        hand = hh.HHParser(history)

        print(hand)

        hrc.calculate_basic(hand.hand_history, hand.hid)











