
import logging
import os
import psutil
import subprocess
import re
import pyperclip
import hhparser as hh
import time
from hand_storage import HandStorage
from itertools import chain
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# TODO check if wmctrl and xdotool installed


class HRCAuto:
    PROCESS_NAME = 'calculator'
    MAIN_WINDOW_TITLE = 'HoldemResources Calculator '
    BASIC_HAND_TITLE = 'Basic Hand Setup '
    CMD_ACTIVATE_MAIN = ['wmctrl', '-R', MAIN_WINDOW_TITLE]
    CMD_ACTIVATE_BASIC = ['wmctrl', '-R', BASIC_HAND_TITLE]
    CMD_BASIC_HAND = [
        ['xdotool', 'key', 'ctrl+w', 'key', 'p', 'sleep', '2']
    ]
    CMD_PASTE_CALCULATE = [[
        'xdotool', 'mousemove', '421', '617',
        'sleep', '0.5', 'click', '1', 'key', 'Tab', 'sleep', '0.5', 'key', 'Return',
        'sleep', '2', 'key', 'Return', 'sleep', '2'
    ]]
    NAME = 'default'
    CMD_SAVE_DIALOG = [
        ['xdotool', 'key', 'alt+h', 'sleep', '1', 'key', 'e', 'sleep', '1',
         'key', 'Up', 'sleep', '1', 'key', 'Return', 'sleep', '3']]
    CMD_RETURN_SAVE = [
        ['xdotool', 'sleep', '1', 'key', 'Down', 'key', 'Down', 'key', 'Return', 'sleep', '2']]

    CMD_CLOSE_TAB = [
        ['xdotool', 'key', 'ctrl+F4']
    ]

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

    def _run_command(self, cmd, **kwargs):
        root = subprocess.Popen(cmd, stdout=subprocess.PIPE, **kwargs)
        if kwargs.get('shell') is None:
            stdout, stderr = root.communicate()
            if stdout:
                self._out.append(stdout)

            if stderr:
                self._errors.append(stderr)

    def _start_hrc(self):
        try:
            self._run_command(self.hrc_path, shell=True)
            logger.info('Starting HRC')

        except:
            self._errors.append('HRC opening error')
            raise RuntimeError('HRC opening error')
        time.sleep(15)
        self._current_title = self.MAIN_WINDOW_TITLE

    def is_active(self):
        if self._get_active_window_title() == self._current_title:
            return True
        else:
            return False

    def _run_command_list(self, cmdlist, activate=True):
        if isinstance(cmdlist, list):
            for cmd in cmdlist:
                if self._find_procs_by_name(self.PROCESS_NAME):
                    if activate:
                        self._run_command(self._cmd_activate)
                    self._run_command(cmd)
                    self._last_cmd = cmd
                else:
                    raise RuntimeError('HRC crashed!')
                    break

    def __init__(self, hrc_path='/home/ant/holdemresources/calculator'):

        self._current_title = self.MAIN_WINDOW_TITLE
        self._cmd_activate = ['wmctrl', '-R', self._current_title]
        self._last_cmd = []
        self._errors = []
        self._out = []
        self.hrc_path = hrc_path

        if not os.path.exists(self.hrc_path):
            raise ValueError('Invalid path to HRC')

        self._run_command(self._cmd_activate)
        time.sleep(1)
        if not self.is_active():
            self._start_hrc()
            if self.check_errors() or not self.is_active():
                raise ValueError('HRC opening error')

    def calculate_basic(self, history, file_name):
        cmd_type = [['xdotool', 'type', file_name]]
        pyperclip.copy(history)

        for trials in range(0, 2):

            try:
                # trying calculate hand 3 times if no errors loop breaks
                self._current_title = self.MAIN_WINDOW_TITLE
                self._run_command(self._cmd_activate)
                if not self.is_active():
                    self._start_hrc()

                self._run_command_list(self.CMD_BASIC_HAND)
                self._current_title = self.BASIC_HAND_TITLE
                self._run_command_list(self.CMD_PASTE_CALCULATE)

                # loop waiting until calculatinon done
                for i in range(0, 40):
                    time.sleep(3)
                    if not self.is_calculating():
                        break

                self._current_title = self.MAIN_WINDOW_TITLE
                self._run_command_list(self.CMD_SAVE_DIALOG)
                cmd_save_close = chain(cmd_type, self.CMD_RETURN_SAVE)

                self._run_command_list(list(cmd_save_close), activate=False)
                self._run_command_list(self.CMD_CLOSE_TAB)
            except Exception as e:
                self.check_errors()
                logger.error(e.args)
                logger.error(f'Error while saving hand: {file_name}')


            if not self.check_errors():
                logger.info(f'Hand: {file_name} saved')
                break
            else:
                logging.error(f'Error while saving hand: {file_name}')

    def is_calculating(self):
        self._run_command(self.CMD_ACTIVATE_BASIC)
        time.sleep(1)
        if self._get_active_window_title() == self.BASIC_HAND_TITLE:
            return True
        else:
            return False

    def check_errors(self):
        """
        printing errors via logger
        :return: True if where were errors
        """
        if self._errors or self._out:
            for error in self._errors:
                logger.error(error)

            for out in self._out:
                logger.error(out)

            self._errors.clear()
            self._out.clear()
            return True
        else:
            return False


if __name__ == '__main__':

    hs = HandStorage('test/')
    calc = HRCAuto()
    for history in hs.read_hand():
        hand = hh.HHParser(history)

        print(hand)

        fn = os.path.join('~', '1results', '-'.join([hand.tid, hand.hid, hand.hero_cards]))
        calc.calculate_basic(hand.hand_history, fn)











