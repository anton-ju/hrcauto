import os
import time
from hrc import HRCAuto
import logging
from queue import PriorityQueue
from threading import Thread
from pypokertools.parsers import PSHandHistory as HHParser
from pypokertools.parsers import HRCOutput as HRCParser

SEARCH_DIR = os.path.expanduser('~/mnt/hands')
RESULT_DIR = os.path.expanduser('~/1results')

def configure_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(f'{__name__}.log')
    formatter = logging.Formatter('[%(asctime)s] %(levelname).1s %(message)s',
                                  datefmt='%Y.%m.%d %H:%M:%S')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def watch_directory(path: str, out_q: PriorityQueue):
    PRIORITY = 1
    dir_contents = set(os.listdir(SEARCH_DIR))

    while True:
        time.sleep(2)
        current_dir_contents = set(os.listdir(SEARCH_DIR))
        diff = current_dir_contents - dir_contents
        if diff:
            for d in diff:
                dir_contents = set(os.listdir(SEARCH_DIR))
                out_q.put((PRIORITY, os.path.join(SEARCH_DIR, d)))


def process_files(in_q: PriorityQueue):
    calc = HRCAuto()
    while True:
        _, file = in_q.get()
        for history in read_hh_files(file):
            parsed_hand = HHParser(history)
            logger.info(f'Hand received: {parsed_hand} {parsed_hand.hero_cards}')
            fn = os.path.join(RESULT_DIR,
                              '-'.join([parsed_hand.tid,
                                        parsed_hand.hid,
                                        parsed_hand.hero_cards]))
            # calculate and save html file fn with results
            saved = False
            while not saved:
                calc.calculate_monte(parsed_hand.hand_history, fn)
                saved = os.path.exists(fn + '.html')
                logger.debug(('saved', saved, fn))

            try:
                parsed_hrc = parse_hrc_output(fn)
                logger.info(get_hero_ev(parsed_hrc, parsed_hand))
                logger.info(get_ranges(parsed_hrc, parsed_hand))

            except (FileNotFoundError, IndexError) as e:
                logger.error(e)
                continue


def read_hh_files(file):
    with open(file, encoding='utf-8') as f:
        try:
            s = f.read()
            s = s.split('\n\n')
            for ss in s:
                if ss == '\n\n' or ss is None or ss == '':
                    continue
                yield ss

        except Exception as e:
            logger.error(e)


def update_index():
    pass


def parse_hrc_output(fn):
    with open(fn + '.html') as f:
        html = f.read()
    return HRCParser(html)


def get_hero_ev(parsed_hrc, parsed_hand):
    """
    determines hero from parsed hand and gets ev of played hand from hrc output
    :param parsed_hrc:
    :param parsed_hand:
    :return: tuple (hand, strategy, ev)
    """
    players_list = get_active_players(parsed_hand)
    logger.debug(players_list)
    if parsed_hand.hero in players_list:
        strategy = ','.join(players_list[:players_list.index(parsed_hand.hero) + 1])
        logger.debug(strategy)
        hand = parsed_hand.cards_to_hand(parsed_hand.hero_cards)
        return (hand, strategy, parsed_hrc.get_hand_ev(hand, strategy))


def get_active_players(parsed_hand):
    # players_list = parsed_hand.p_actions.items()
    # players_before_hero = players_list[:players_list.index(parsed_hand.hero) + 1]
    return [k for k, v in parsed_hand.p_actions.items() if v != ['f'] or k == parsed_hand.hero]


def get_ranges(parsed_hrc, parsed_hand):
    players_list = get_active_players(parsed_hand)
    if parsed_hand.hero in players_list:
        strategy = ','.join(players_list[:players_list.index(parsed_hand.hero) + 1])
        return parsed_hrc.get_range(strategy)


if __name__ == '__main__':

    logger = configure_logger()
    q = PriorityQueue()
    producer = Thread(target=watch_directory, args=(SEARCH_DIR, q, ))
    consumer = Thread(target=process_files, args=(q, ))
    producer.start()
    consumer.start()



