import os
import time
from hrc import HRCAuto
from hhparser import HHParser

DIR = '/mnt/hands'
RESULT_DIR = '~/1results'


def watch_directory(path):

    while True:
        dir_contents = set(os.listdir(DIR))

        time.sleep(2)
        current_dir_contents = set(os.listdir(DIR))
        diff = current_dir_contents - dir_contents
        if diff:
            for d in diff:
                yield os.path.join(DIR, d)


def read_hh_files(files):
    for file in files:
        with open(file, encoding='utf-8') as f:
            try:
                s = f.read()
                s = s.split('\n\n')
                for ss in s:
                    if ss == '\n\n' or ss == None or ss == '':
                        continue
                    yield ss

            except:
                continue


def update_index():
    pass


calc = HRCAuto()
for history in read_hh_files(watch_directory(DIR)):

    hand = HHParser(history)
    print(hand)
    fn = os.path.join(RESULT_DIR, '-'.join([hand.tid, hand.hid, hand.hero_cards]))
    calc.calculate_basic(hand.hand_history, fn)