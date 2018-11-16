# -*- coding: utf-8 -*-
"""
Created on Tue Aug  9 14:02:58 2016

@author: ThaiSSD
"""
import re
import numpy as np
import itertools
from datetime import datetime

ACTIONS = {
    'calls': 'c',
    'raises': 'r',
    'folds': 'f',
    'bets': 'b',
    'checks': 'x'
}


class cached_property(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls=None):
        result = instance.__dict__[self.func.__name__] = self.func(instance)
        return result

class Actions(enumerate):
    pass


class HandHistoryParser:
    PRIZE = []
    POSITIONS = ['BB', 'SB', 'BU', 'CO', 'MP2', 'MP1', 'UTG3', 'UTG2', 'UTG1']
    UNCALLED_REGEX = "Uncalled.*\((?P<bet>\d+)\).*to (?P<player>.*)"
    UNCALLED_DICT = {'player': 'bet'}
    CHIPWON_REGEX = "(?P<player>.*) collected (?P<chipwon>\d+)"
    CHIPWON_DICT = {'player': 'chipwon'}
    FINISHES_REGEX = "(?P<player>.*?) (?:finished.*in (?P<place>\d+)(?:nd|rd|th)|wins the tournament)"
    PRIZE_WON_REGEX = "(?P<player>.*) (?:wins|finished).*and (?:received|receives) \$(?P<prize>\d+\.\d+)(?:.|\s)"
    BLINDS_ANTE_REGEX = "(?P<player>.*): posts .*?(?P<bet>\d+)"
    BOUNTY_WON_REGEX = "(?P<player>.*) wins the \$(?P<bounty>.*) bounty"
    RIVER_REGEX = "RIVER.*\[(?:.*)\] \[(?P<river>.{2})\]"
    TURN_REGEX = "TURN.*\[(?:.*)\] \[(?P<turn>.{2})\]"
    ANTE_REGEX = "(?P<player>.*): posts the ante (?P<bet>\d+)"
    BLINDS_REGEX = "(?P<player>.*): posts (?:small|big) blind (?P<bet>\d+)"
    BLINDS_ANTE_DICT = {'player': 'bet'}
    SB_PLAYER_REGEX = "(?P<player>.*):\sposts small"
    BB_PLAYER_REGEX = "(?P<player>.*):\sposts big"
    P_ACTIONS_REGEX = "(?P<player>.*):\s(?P<action>calls|raises|folds|checks)"
    ACTIONS_REGEX = "(?P<player>.*):\s(?P<action>calls|raises|bets|folds|checks)"
    ACTIONS_DICT = {'player': 'action'}
    ACTIONS_AMOUNTS_REGEX = "(?P<player>.*?): (?:calls|raises.*to|bets|checks) (?P<amount>\d+)?"
    ACTIONS_AMOUNTS_DICT = {'player': 'amount'}
    AI_PLAYERS_REGEX = "(?P<player>.*):.* all-in"
    KNOWN_CARDS_REGEX = "Seat \d: (?P<player>.*?)\s?(?:\(button\) showed|\(small blind\) showed|\(button\) \(small blind\) showed|\(big blind\) showed| showed)\s\[(?P<knowncards>.*)\]"
    KNOWN_CARDS_DICT = {'player': 'knowncards'}
    FLOP_REGEX = "FLOP.*\[(?P<flop>.*)\]"
    POT_LIST_REGEX = "(Total|Main|Side) (pot|pot-1|pot-2|pot-3|pot-4|pot-5)\s(?P<pot>\d*)"
    DATETIME_REGEX = "(?P<datetime>\d{4}/\d{2}/\d{2}\s\d{1,2}:\d{1,2}:\d{1,2})\sET"
    TID_REGEX = "Tournament #(?P<tid>\d+)"
    HID_REGEX = "Hand #(?P<hid>\d+)"
    HERO_REGEX = r"Dealt to (?P<hero>.*)\s\["
    HERO_CARDS_REGEX = r"Dealt to .*\s\[(?P<cards>.*)]"
    BI_BOUNTY_RAKE_REGEX = "Tournament\s#\d+,\s\$(?P<bi>\d+?\.\d+)(?:\+\$)?(?P<bounty>\d+?\.\d+)?\+\$(?P<rake>\d+?\.\d+)"

    def _process_regexp(
            self,
            pattern,
            text,
            *args,
            type_func=lambda x: x,
            reslist=False,
            default_value=0,
            **kwargs):
        """

        :param pattern: regex
        :param text: text
        :param args: list with group name to extract, if you want to extract values into list
        :param type_func: function for type casting
        :param reslist: boolean -> if you want to get dict with list values else same key will results will be added
        :param default_value: for reslist
        :param kwargs: dict with group names to extract
        :return:
        """
        # extracts named groups from result of re and converts it into dict or list
        it = re.finditer(pattern, text)

        res = []
        for x in args:
            for i in it:
                try:
                    res.append(type_func(i.groupdict().get(x)))
                except TypeError:
                    res.append(i.groupdict().get(x))
            if reslist:
                return res
            else:
                return default_value if len(res) == 0 else res[0]
        res = {}
        for k, v in kwargs.items():
            for i in it:
                key = i.groupdict().get(k)
                value = i.groupdict().get(v)
                try:
                    if reslist:
                        if res.get(key):
                            res[key].append(type_func(value))
                        else:
                            res[key] = [type_func(value)]
                    else:
                        if res.get(key):
                            res[key] += type_func(value)
                        else:
                            res[key] = type_func(value)
                except TypeError:
                    if reslist:
                        if res.get(key):
                            res[key].append(value)
                        else:
                            res[key] = [value]
                    else:
                        res[key] = value
            return res


class TournamentSummary(HandHistoryParser):

    FINISHES_REGEX = "You finished in (?P<place>\d+)(?:nd|rd|th|st)"
    PRIZE_WON_REGEX = "(?:\d+):\s(?P<player>.*)\s\(.*\),\s\$(?P<prize>\d+\.\d+)"

    def __init__(self, ts_text):
        self.ts_text = ts_text

    def __str__(self):
        return f"Tournament: #{self.tid} Finish: {self.finishes} Prize:{self.prize_won}"

    @cached_property
    def tid(self):
        return self._process_regexp(self.TID_REGEX, self.ts_text, 'tid')

    @cached_property
    def finishes(self):
        return self._process_regexp(self.FINISHES_REGEX,
                                                   self.ts_text,
                                                   type_func=lambda x: int(x),
                                                   *['place'])

    @cached_property
    def prize_won(self):
        return self._process_regexp(self.PRIZE_WON_REGEX,
                                                  self.ts_text,
                                                  type_func=lambda x: float(x),
                                                  **{'player':'prize'})


class HHParser(HandHistoryParser):

    def __str__(self):
        return f"Hand: #{self.hid} Tournament: #{self.tid} \${self.bi} [{self.datetime}]"

    def __init__(self, hh):
        #       todo проверка является ли строка hand history
        self.hand_history = hh

        #       split the original hand histoty into logical sections preflop flop ...
        hist_text = self.hand_history

        self.summary_str = hist_text[hist_text.find("*** SUMMARY ***"):]
        hist_text = hist_text[:hist_text.find("*** SUMMARY ***")]

        self.showdown_str = hist_text[hist_text.find("*** SHOW DOWN ***"):]
        hist_text = hist_text[:hist_text.find("*** SHOW DOWN ***")]

        self.river_str = hist_text[hist_text.find("*** RIVER ***"):]
        hist_text = hist_text[:hist_text.find("*** RIVER ***")]

        self.turn_str = hist_text[hist_text.find("*** TURN ***"):]
        hist_text = hist_text[:hist_text.find("*** TURN ***")]

        self.flop_str = hist_text[hist_text.find("*** FLOP ***"):]
        hist_text = hist_text[:hist_text.find("*** FLOP ***")]

        self.preflop_str = hist_text[hist_text.find("*** HOLE CARDS ***"):]
        hist_text = hist_text[:hist_text.find("*** HOLE CARDS ***")]

        self.caption_str = hist_text

        self.sb = 0
        self.bb = 0
        self._stacks_list = []
        self.players = []
        self.small_blind = 0
        self.big_blind = 0
        self.preflop_order = []  # чем больше число чем позже принимает решение


        #        regex_ps =  "\s?PokerStars\s+?Hand"
        #        regex_888 = "\s?888poker\s+?Hand"
        #        t = re.compile(regex_ps)
        #        if t.match(self.hand_history):
        #            print("poker stars hand detected")
        regex = "Seat\s?[0-9]:\s(.*)\s\(\s?\$?(\d*,?\d*)\s(?:in\schips)?"
        sbplayer_regex = "(.*)?:\sposts small"
        bbplayer_regex = "(.*)?:\sposts big"
        blinds_regex = "Level\s.+\s\((?P<sb>\d+)/(?P<bb>\d+)\)"

        #        t = re.search(regex)

        self.PRIZE = np.array([0.50, 0.50])

        tupples = re.findall(regex, self.hand_history)

        self.players = [x[0] for x in tupples]
        self._stacks_list = [float(x[1].replace(",", "")) for x in tupples]
        self._stacks = {x[0]: float(x[1].replace(",", "")) for x in tupples}
        #       удаление нулевых стэков
        try:
            self._stacks_list.index(0.0)
            print(self._stacks_list.index(0.0))
            while self._stacks_list.index(0.0) + 1:
                n = self._stacks_list.index(0.0)
                self._stacks_list.remove(0.0)
                self.players.pop(n)
        except ValueError:
            pass
        finally:
            pass

        res = re.search(bbplayer_regex, self.hand_history)
        if res:
            self.big_blind = self.players.index(res.group(1))
            self.preflop_order = self.players[self.big_blind + 1:] + self.players[:self.big_blind + 1]
        else:
            res = re.search(sbplayer_regex, self.hand_history)
            if res:
                self.small_blind = self.players.index(res.group(1))
                self.preflop_order = self.players[self.small_blind + 1:] + self.players[:self.small_blind + 1]

        # в префлоп ордер теперь содержится порядок действия игроков как они сидят префлоп от утг до бб

        res = re.search(blinds_regex, self.hand_history)
        if res:
            self.sb = int(res.groupdict().get('sb', '10'))
            self.bb = int(res.groupdict().get('bb', '20'))





    def p1p(self, ind, place):
        #       вероятность place го места для игрока ind

        #       s - список стэков игроков
        #       ind - индекс стэка для которого считаестя вероятность
        #       place - место целое число, должно быть не больше чем длина списка s

        sz = self.players_number()

        #
        if place > sz:
            return 0
        if ind + 1 > sz:
            return 0
        #       если стэк 0 сразу вернем 0

        if self.getStack(ind) == 0:
            if sz - 1 >= np.size(self.PRIZE):
                return 0
            else:
                return self.PRIZE[sz - 1]

        p = []

        # получаем все возможные варианты распределения мест
        #           индекс в списке соответствует месту игрока
        for i in itertools.permutations(range(sz), sz):
            #               выбираем только те распределения где игрок ind на месте place
            if i[place - 1] == ind:
                #                    из списка издексов с распределением мест,
                #                    формируем список со значениями стеков
                si = []
                for j in i:
                    si.append(self.getStack(j))
                #                    with Profiler() as pr:
                pi = 1
                for j in range(sz):
                    sum_ = sum(si[j:])
                    if sum_ != 0:
                        pi = pi * si[j] / sum_

                p.append(pi)

        result = sum(p)
        return result

    def icm_eq(self, stacks=None):
        if stacks is not None:
            SZ = np.size(stacks)
        else:
            SZ = np.size(self._stacks_list)
            stacks = np.copy(self._stacks_list)

        #        place_probe = np.zeros(SZ, 3)

        #       end p1p()

        #       perm = itertools.permutations(range(SZ), SZ)

        ind1 = range(0, SZ)

        min_place = min(SZ, np.size(self.PRIZE))
        p1 = np.zeros(shape=(min_place, SZ))
        ind2 = range(0, min_place)
        # p1 строка - занятое место, столбец - номер игрока
        for i in ind1:
            for j in ind2:
                p1[j, i] = self.p1p(i, j + 1)
                # в функции место нумеруются с 1 до 3, в матрице с 0 до 2  

        #
        eq = np.dot(self.PRIZE[:min_place], p1)
        return eq

    def icm_eq_dict(self, stacks=None):
        if stacks is not None:
            SZ = np.size(stacks)
        else:
            SZ = np.size(self._stacks_list)
            stacks = np.copy(self._stacks_list)
        ind1 = range(0, SZ)
        min_place = min(SZ, np.size(self.PRIZE))
        p1 = np.zeros(shape=(min_place, SZ))
        ind2 = range(0, min_place)
        # p1 строка - занятое место, столбец - номер игрока
        for i in ind1:
            for j in ind2:
                p1[j, i] = self.p1p(i, j + 1)
                # в функции место нумеруются с 1 до 3, в матрице с 0 до 2
        #
        eq = np.dot(self.PRIZE[:min_place], p1)
        return {self.players[i]: round(eq[i], 4) for i in range(SZ)}

    def tie_factor(self):
        eq = self.icm_eq()
        st = np.array(self._stacks_list)
        sz = np.size(st)
        result = np.zeros((sz, sz))
        for i in range(sz):
            for j in range(sz):
                if i == j:
                    continue

                stacks_win = np.copy(st)
                stacks_lose = np.copy(st)
                if st[i] > st[j]:
                    stacks_win[i] = st[i] + st[j]
                    stacks_win[j] = 0
                    stacks_lose[i] = st[i] - st[j]
                    stacks_lose[j] = st[j] * 2
                else:
                    stacks_win[i] = st[i] * 2
                    stacks_win[j] = st[j] - st[i]
                    stacks_lose[i] = 0
                    stacks_lose[j] = st[i] + st[j]
                eq_win = self.icm_eq(stacks_win)
                eq_lose = self.icm_eq(stacks_lose)
                #                print(stacks_win)
                #                print(stacks_lose)
                #                print(eq_win)
                #                print(eq_lose)
                #
                #                print(i, j)
                bubble_factor = (eq[i] - eq_lose[i]) / (eq_win[i] - eq[i])
                result[i, j] = bubble_factor / (1 + bubble_factor)
        #                if i > 1 and j > 1: return result
        return result

    def tournamentPosition(self, player):

        try:
            i = self.players.index(player)
        except ValueError:
            #            print("no player " + player)
            return -1

        sp = self._stacks_list[i]
        result = 1
        #
        for s in self._stacks_list:
            if s > sp:
                result += 1

        return result

    def tablePosition(self, player):
        # сколько еще игроков будут действовать на префлопе после игрока
        return self.preflop_order

    def flg_chiplead(self, player):

        if self.tournamentPosition(player) == 1:
            return True
        else:
            return False

    def tournamentPositionL(self, player):
        # позиция игрока среди игроков сидящих слева т.е. действующих на префлопе после него

        if self.big_blind:
            if self.big_blind == self.players.index(player):
                return self.tournamentPosition(player)

        try:
            i = self.players.index(player)

        except ValueError:
            print("no player " + player)
            return -1

        sp = self._stacks_list[i]
        result = 1

        i = self.preflop_order.index(player)
        for s in [self._stacks_list[ind1] for ind1 in [self.players.index(p) for p in self.preflop_order[i:]]]:
            if s > sp:
                result += 1

        return result

    def getStack(self, player):
        #       возвращает стэк игрока
        #       player - номер игрока int или имя игрока str
        #
        sp = 0
        if type(player) is str:
            try:
                i = self.players.index(player)
            except ValueError:
                print("no player " + player)
                return -1

            sp = self._stacks_list[i]

        if type(player) is int:
            try:
                sp = self._stacks_list[player]
            except IndexError:
                print("no such index " + player)
                return -1

        return sp

    def stacks(self):
        # returns dict {player: stack}
        return self._stacks

    def stack_list(self):
        #       возвращает сисок стэков
        #
        return self._stacks_list

    def flg_chiplead_left(self, player):

        if self.tournamentPositionL(player) == 1:
            return True
        else:
            return False

    def players_number(self):
        #   возвращает число игроков
        #
        return len(self._stacks_list)

    # def getPlayerDict(self):
    #     #   returns dict {position: playername}
    #     return {self.POSITIONS[i]: self.preflop_order[::-1][i] for i in range(len(self.preflop_order))}

    def flg_knockout(self):
        return True if self.bounty > 0 else False

    # def getStackDict(self):
    #     #       returns dict {position: stack}
    #     return {self.POSITIONS[i]: self.getStack(self.preflop_order[::-1][i]) for i in range(len(self.preflop_order))}

    def getBlinds(self):
        return [self.sb, self.bb]

    @cached_property
    def bi(self):
        res = self._process_regexp(
            self.BI_BOUNTY_RAKE_REGEX,
            self.caption_str,
            'bi',
            type_func=lambda x: float(x),
        )
        res = res + self.bounty + self.rake
        return res


    @cached_property
    def bounty(self):
        res = self._process_regexp(
            self.BI_BOUNTY_RAKE_REGEX,
            self.caption_str,
            'bounty',
            type_func=lambda x: float(x),
        )
        return res if res else 0

    @cached_property
    def rake(self):
        return self._process_regexp(
            self.BI_BOUNTY_RAKE_REGEX,
            self.caption_str,
            'rake',
            type_func=lambda x: float(x),
        )

    def flgRFIOpp(self, player):
        #       returns true if player has opportunity of first action
        rfi_regex = f'(folds\s{player}|]\s{player})'
        if re.search(rfi_regex, self.hand_history):
            return True
        return False

    def flgFacedAI(self, player):
        return False

    @cached_property
    def tid(self):
        return self._process_regexp(self.TID_REGEX, self.caption_str, 'tid')

    @cached_property
    def hid(self):
        return self._process_regexp(
            self.HID_REGEX,
            self.caption_str,
            'hid'
        )

    @cached_property
    def datetime(self):
        res = self._process_regexp(
            self.DATETIME_REGEX,
            self.caption_str,
            'datetime'
        )
        dt_str_format = '%Y/%m/%d %H:%M:%S'
        try:
            res = datetime.strptime(res, dt_str_format)
        except:
            pass
        return res


    @cached_property
    def p_actions(self):
        return self._process_regexp(
            self.ACTIONS_REGEX,
            self.preflop_str,
            type_func=lambda x: ACTIONS[x],
            reslist=True,
            **self.ACTIONS_DICT
        )

    @cached_property
    def f_actions(self):
        return self._process_regexp(
            self.ACTIONS_REGEX,
            self.flop_str,
            type_func= lambda x: ACTIONS[x],
            reslist=True,
            **self.ACTIONS_DICT
        )

    @cached_property
    def t_actions(self):
        return self._process_regexp(
            self.ACTIONS_REGEX,
            self.turn_str,
            type_func= lambda x: ACTIONS[x],
            reslist=True,
            **self.ACTIONS_DICT
        )

    @cached_property
    def r_actions(self):
        return self._process_regexp(self.ACTIONS_REGEX,
                                                  self.river_str,
                                                   type_func= lambda x: ACTIONS[x],
                                                   reslist=True,
                                                   **self.ACTIONS_DICT)

    @cached_property
    def p_ai_players(self):
        # todo сюда не попадают игроки которые заколили или поставили игрока под аи оставив в своем стэке фишки

        #       returns list of players which is all in preflop
        return self._process_regexp(self.AI_PLAYERS_REGEX,
                                                     self.preflop_str,
                                                    'player',
                                                      reslist=True)

    @cached_property
    def f_ai_players(self):
        #       returns list of players which is all in preflop
        return self._process_regexp(self.AI_PLAYERS_REGEX,
                                                     self.flop_str,
                                                    'player',
                                                      reslist=True)

    @cached_property
    def t_ai_players(self):
        #       returns list of players which is all in preflop
        return self._process_regexp(self.AI_PLAYERS_REGEX,
                                                     self.turn_str,
                                                    'player',
                                                      reslist=True)

    @cached_property
    def r_ai_players(self):
        #       returns list of players which is all in preflop
        return self._process_regexp(self.AI_PLAYERS_REGEX,
                                                     self.river_str,
                                                    'player',
                                                      reslist=True)

    @cached_property
    def pot_list(self):
        #       returns list with 1st item is total pot and all af the side pots if presents
        return self._process_regexp(
                                                  self.POT_LIST_REGEX,
                                                  self.summary_str,
                                                  'pot',
                                                  reslist=True,
                                                  type_func=lambda x: int(x)
                                                  )

    @cached_property
    def p_actions_amounts(self):
        return self._process_regexp(self.ACTIONS_AMOUNTS_REGEX,
                                                  self.preflop_str,
                                                   type_func= lambda x: int(x),
                                                   reslist=True,
                                                   **self.ACTIONS_AMOUNTS_DICT)

    @cached_property
    def f_actions_amounts(self):
        return self._process_regexp(self.ACTIONS_AMOUNTS_REGEX,
                                                  self.flop_str,
                                                   type_func= lambda x: int(x),
                                                   reslist=True,
                                                   **self.ACTIONS_AMOUNTS_DICT)

    @cached_property
    def t_actions_amounts(self):
        return self._process_regexp(self.ACTIONS_AMOUNTS_REGEX,
                                                  self.turn_str,
                                                   type_func= lambda x: int(x),
                                                   reslist=True,
                                                   **self.ACTIONS_AMOUNTS_DICT)

    @cached_property
    def r_actions_amounts(self):
        return self._process_regexp(self.ACTIONS_AMOUNTS_REGEX,
                                                  self.river_str,
                                                   type_func= lambda x: int(x),
                                                   reslist=True,
                                                   **self.ACTIONS_AMOUNTS_DICT)

    def total_bets_amounts(self):
        # total bets sum on every street including blinds and antes
        res = {}

        for k in list(self._stacks.keys()):

            actions = self.p_actions.get(k, [0])
            if 'r' in actions:
                last_raise_pos =  - actions[::-1].index('r') - 1
                p_total_bets = sum(self.p_actions_amounts.get(k, [0])[last_raise_pos:])
            else:
                p_total_bets = sum(self.p_actions_amounts.get(k, [0])) + self.blinds.get(k, 0)

            actions = self.f_actions.get(k, [0])
            if 'r' in actions:
                last_raise_pos = - actions[::-1].index('r') - 1
                f_total_bets = sum(self.f_actions_amounts.get(k, [0])[last_raise_pos:])
            else:
                f_total_bets = sum(self.f_actions_amounts.get(k, [0]))

            actions = self.t_actions.get(k, [0])
            if 'r' in actions:
                last_raise_pos = - actions[::-1].index('r') - 1
                t_total_bets = sum(self.t_actions_amounts.get(k, [0])[last_raise_pos:])
            else:
                t_total_bets = sum(self.t_actions_amounts.get(k, [0]))

            actions = self.r_actions.get(k, [0])
            if 'r' in actions:
                last_raise_pos = - actions[::-1].index('r') - 1
                r_total_bets = sum(self.r_actions_amounts.get(k, [0])[last_raise_pos:])
            else:
                r_total_bets = sum(self.r_actions_amounts.get(k, [0]))

            res[k] = p_total_bets + f_total_bets + t_total_bets + r_total_bets + self.antes.get(k, 0)

        return res

    def p_last_action(self):
        res = {}
        for k in list(self._stacks.keys()):
            p_actions = self.p_actions.get(k, '')
            if p_actions:
                res[k] = p_actions[len(p_actions) - 1]
        return res

    def f_last_action(self):
        res = {}
        for k in list(self._stacks.keys()):
            actions = self.f_actions.get(k, '')
            if actions:
                res[k] = actions[len(actions) - 1]
        return res

    def t_last_action(self):
        res = {}
        for k in list(self._stacks.keys()):
            actions = self.t_actions.get(k, '')
            if actions:
                res[k] = actions[len(actions) - 1]
        return res

    def r_last_action(self):
        res = {}
        for k in list(self._stacks.keys()):
            actions = self.r_actions.get(k, '')
            if actions:
                res[k] = actions[len(actions) - 1]
        return res

    @cached_property
    def hero(self):
        #       returns hero name
        return self._process_regexp(
                self.HERO_REGEX,
                self.preflop_str,
                'hero'
            )

    @cached_property
    def hero_cards(self):
        return self._process_regexp(
                self.HERO_CARDS_REGEX,
                self.preflop_str,
                'cards'
            )

    @cached_property
    def known_cards(self):
            return self._process_regexp(self.KNOWN_CARDS_REGEX,
                                                     self.summary_str,
                                                     # type_func=lambda x: ''.join(x.split()),
                                                     **self.KNOWN_CARDS_DICT,
                                                     )

    @cached_property
    def flop(self):
        return self._process_regexp(self.FLOP_REGEX,
                                              self.flop_str,
                                              'flop',
                                              # type_func=lambda x: ''.join(x.split()),
                                              )

    @cached_property
    def turn(self):
        return self._process_regexp(self.TURN_REGEX,
                                              self.turn_str,
                                              'turn')

    @cached_property
    def river(self):
        return self._process_regexp(self.RIVER_REGEX,
                                              self.river_str,
                                              'river')

    @cached_property
    def bounty_won(self):
        #   bounty won in hand
        res = self._process_regexp(self.BOUNTY_WON_REGEX,
                                                   self.showdown_str,
                                                   type_func=lambda x: float(x),
                                                   **{'player':'bounty'})
        # 1 more bounty for the 1st place
        for player, place in self.finishes.items():
            if place == 1:
                res[player] = res.get(player, 0) + self.bounty
        return res

    @cached_property
    def prize_won(self):
        return self._process_regexp(self.PRIZE_WON_REGEX,
                                                  self.showdown_str,
                                                  type_func=lambda x: float(x),
                                                  **{'player':'prize'})

    @cached_property
    def chip_won(self):
        return self._process_regexp(self.CHIPWON_REGEX,
                                                 self.showdown_str + self.preflop_str,
                                                 type_func=lambda x: int(x),
                                                 reslist=True,
                                                 **self.CHIPWON_DICT)

    @cached_property
    def finishes(self):
        res = self._process_regexp(self.FINISHES_REGEX,
                                                   self.showdown_str,
                                                   type_func=lambda x: int(x),
                                                   **{'player':'place'})
        if res:
            for k,v in res.items():
                if v is None:
                    res[k] = 1
        return res

    @cached_property
    def blinds_antes(self):
        #returns dict {player: bet before preflop}
        res = re.findall(self.BLINDS_ANTE_REGEX, self.caption_str)
        dic = {}
        if res:
            for x in res:
                if dic.get(x[0], 0) == 0:
                    dic[x[0]] = int(x[1])
                else:
                    dic[x[0]] = dic.get(x[0]) + int(x[1])

        return dic

    @cached_property
    def blinds(self):
        #returns dict {player: blind bet}
        return self._process_regexp(self.BLINDS_REGEX,
                                                 self.caption_str,
                                                 type_func=lambda x: int(x),
                                                 **self.BLINDS_ANTE_DICT)

    @cached_property
    def antes(self):
        #returns dict {player: ante}

        return self._process_regexp(self.ANTE_REGEX,
                                                 self.caption_str,
                                                 type_func=lambda x: int(x),
                                                 **self.BLINDS_ANTE_DICT)

    @cached_property
    def uncalled(self):
        #returns dict {player: bet}
        return self._process_regexp(self.UNCALLED_REGEX,
                                                 self.hand_history,
                                                 type_func=lambda x: int(x),
                                                 **self.UNCALLED_DICT)

    def positions(self):
        #returns dict{player: position}
        return {self.preflop_order[::-1][i]: self.POSITIONS[i] for i in range(len(self.preflop_order))}

    def flg_showdown(self):
        return True if self.showdown_str.strip() else False

    def last_actions(self):
        # returns last actions
        if self.r_actions:
            return self.r_actions
        elif self.t_actions:
            return self.t_actions
        elif self.f_actions:
            return self.f_actions
        else:
            return self.p_actions

    def last_actions_amounts(self):
        if self.r_actions_amounts():
            return self.r_actions_amounts()
        elif self.t_actions_amounts():
            return self.t_actions_amounts()
        elif self.f_actions_amounts():
            return self.f_actions_amounts()
        else:
            return self.p_actions_amounts()

    def _process_regexp(
            self,
            pattern,
            text,
            *args,
            type_func=lambda x: x,
            reslist=False,
            default_value=0,
            **kwargs):
        """

        :param pattern: regex
        :param text: text
        :param args: list with group name to extract, if you want to extract values into list
        :param type_func: function for type casting
        :param reslist: boolean -> if you want to get dict with list values else same key will results will be added
        :param default_value: for reslist
        :param kwargs: dict with group names to extract
        :return:
        """
        # extracts named groups from result of re and converts it into dict or list
        it = re.finditer(pattern, text)

        res = []
        for x in args:
            for i in it:
                try:
                    res.append(type_func(i.groupdict().get(x)))
                except TypeError:
                    res.append(i.groupdict().get(x))
            if reslist:
                return res
            else:
                return default_value if len(res) == 0 else res[0]
        res = {}
        for k, v in kwargs.items():
            for i in it:
                key = i.groupdict().get(k)
                value = i.groupdict().get(v)
                try:
                    if reslist:
                        if res.get(key):
                            res[key].append(type_func(value))
                        else:
                            res[key] = [type_func(value)]
                    else:
                        if res.get(key):
                            res[key] += type_func(value)
                        else:
                            res[key] = type_func(value)
                except TypeError:
                    if reslist:
                        if res.get(key):
                            res[key].append(value)
                        else:
                            res[key] = [value]
                    else:
                        res[key] = value
            return res

