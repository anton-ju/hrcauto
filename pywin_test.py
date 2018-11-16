# импортируем модули для работы с windows оберткой
import win32api
import win32con
import win32gui
import time
import win32com.client
# from tkinter import Tk
import pyperclip
import hhparser as hh
from hand_storage import HandStorage
import logging

HISTORY = """
PokerStars Hand #189807795760: Tournament #2380726500, $4.79+$4.79+$0.42 USD Hold'em No Limit - Level VII (60/120) - 2018/08/12 19:53:24 MSK [2018/08/12 12:53:24 ET]
Table '2380726500 1' 6-max Seat #1 is the button
Seat 1: dimitriskous (1676 in chips)
Seat 4: MM7000k (544 in chips)
Seat 5: DiggErr555 (780 in chips)
dimitriskous: posts the ante 12
MM7000k: posts the ante 12
DiggErr555: posts the ante 12
MM7000k: posts small blind 60
DiggErr555: posts big blind 120
*** HOLE CARDS ***
Dealt to DiggErr555 [Td Kc]
dimitriskous: folds
MM7000k: raises 412 to 532 and is all-in
DiggErr555: calls 412
*** FLOP *** [Jc 6c 6h]
*** TURN *** [Jc 6c 6h] [Js]
*** RIVER *** [Jc 6c 6h Js] [7d]
*** SHOW DOWN ***
MM7000k: shows [Ad 4d] (two pair, Jacks and Sixes)
DiggErr555: shows [Td Kc] (two pair, Jacks and Sixes - lower kicker)
MM7000k collected 1100 from pot
*** SUMMARY ***
Total pot 1100 | Rake 0
Board [Jc 6c 6h Js 7d]
Seat 1: dimitriskous (button) folded before Flop (didn't bet)
Seat 4: MM7000k (small blind) showed [Ad 4d] and won (1100) with two pair, Jacks and Sixes
Seat 5: DiggErr555 (big blind) showed [Td Kc] and lost with two pair, Jacks and Sixes
"""
logging.basicConfig(level = logging.DEBUG)
logger = logging.getLogger(__name__)

# hs = HandStorage('hands/debug/test_hand')
hs = HandStorage('C:\\Users\\user\\code\\python\\hrcauto\\test')


# c = Tk()
# c.withdraw()
# c.clipboard_clear()
# c.clipboard_append('rrrr')
# c.update()
# c.destroy()

# c = Tk()
# c.withdraw()
# clip = c.clipboard_get()
# c.update()
# c.destroy()
# print(clip)



# функция клика в определенном месте
def click(x, y):
    # сначала выставляем позицию
    win32api.SetCursorPos((x, y))
    time.sleep(0.2)
    # а потом кликаем (небольшая задержка для большей человечности)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    time.sleep(0.3)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)


# данная функция - фильтр по выбору нужного окна (по названию этого окна)
def openItNow(hwnd, windowText):
    if windowText in win32gui.GetWindowText(hwnd):
        win32gui.SetForegroundWindow(hwnd)


# приступим


def hrcauto(hid):

    # выбираем среди открытых окон то, которое содержит название Notepad
    # заметьте что используется фильтр, описанный выше
    win32gui.EnumWindows(openItNow, 'HoldemResources Calculator')

    # нажимать на клавиши будет с помощью shell
    shell = win32com.client.Dispatch("WScript.Shell")

    # метод SendKeys программно нажимает на клавиши, поэтому далее записана последовательность нажатий
    shell.SendKeys("%")
    time.sleep(0.1)

    shell.SendKeys("{DOWN}")
    time.sleep(0.1)

    shell.SendKeys("{ENTER}")
    time.sleep(1)


    # win32gui.EnumWindows(openItNow, 'New')
    shell.SendKeys('{ENTER}')
    time.sleep(0.1)

    shell.SendKeys('{ENTER}')
    time.sleep(0.1)

    shell.SendKeys("{TAB 18}")
    time.sleep(0.1)

    shell.SendKeys('{ENTER}')
    # shell.SendKeys('{TAB}')
    # shell.SendKeys('222')
    # shell.SendKeys('{TAB}')
    # shell.SendKeys('333')
    # shell.SendKeys('{TAB}')
    # shell.SendKeys('444')
    #
    # # win32gui.EnumWindows(openItNow, 'Basic Hand Setup')
    shell.SendKeys('{ENTER}')
    # # time.sleep(0.1)
    #cчитается рука
    shell.SendKeys('{ENTER}')
    time.sleep(5)
    #
    # # вызов диалога экспорта руки
    shell.SendKeys("%")
    #
    shell.SendKeys("{RIGHT}")
    shell.SendKeys("{DOWN}")
    shell.SendKeys("{DOWN}")
    #
    #
    shell.SendKeys("{ENTER}")
    time.sleep(1)
    #
    # # сохранение
    shell.SendKeys("{UP}")
    shell.SendKeys("{ENTER}")
    time.sleep(1)
    #
    # # ввод имени файла
    shell.SendKeys(hid)
    shell.SendKeys("{ENTER}")
    time.sleep(1)


for history in hs.read_hand():
    hand = hh.HHParser(history)

    if hand.players_number() == 3:
        print(hand)
        hid = hand.hid()
        pyperclip.copy(history)
        hrcauto(hid)

