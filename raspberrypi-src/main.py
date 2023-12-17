import network
import urequests
import usocket as socket
import time
import machine


try:
    import ustruct as struct
except:
    import struct


URL = "YOUR WEBHOOK URL"
UTC_OFFSET = 9
ssid = 'YOUR SSID'
password = 'YOUR PASSWORD'

INTERVAL = 30

card_newone = '''
{
    "type": "AdaptiveCard",
    "body": [
        {
            "type": "TextBlock",
            "size": "large",
            "weight": "bolder",
            "text": "誰か来たみたい(=^・・^=)"
        },
        {
            "type": "TextBlock",
            "text": "らずぱいがドアが開いたのを検知したよ!!!",
            "wrap": true
        }
    ],
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "version": "1.5"
}
'''

card_deactive = '''
{
    "type": "AdaptiveCard",
    "body": [
        {
            "type": "TextBlock",
            "size": "Large",
            "weight": "Bolder",
            "text": "誰もいないかも…（´・ω・｀）"
        },
        {
            "type": "TextBlock",
            "text": "{start}から{last}の期間の間にドアが{times}回開かれたよ!!\n\nこれ以降{inter}分間ドアの開閉が無かったから、誰もいないのかな…?\n",
            "wrap": true
        }
    ],
    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
    "version": "1.5"
}
'''

def convert_time2rtc(tpl):
    rtn = tpl
    rtn = list(tpl)
    rtn[3] = tpl[-2]
    for i in range(3, 6):
        rtn[i + 1] = tpl[i]
    rtn[7] = 0
    return rtn


def ntptime():
    NTP_DELTA = 2208988800
    # ntp server
    # ntp_host = "ntp.nict.jp"
    # ntp_host = "time-c.nist.gov"
    # ntp_host = "time.cloudflare.com"
    # ntp_host = "time.google.com"
    ntp_host = "timeserver.cc.tsukuba.ac.jp"
    
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1b
    addr = socket.getaddrinfo(ntp_host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # s.settimeout(1)
    res = s.sendto(NTP_QUERY, addr)
    msg = s.recv(48)
    s.close()
    val = struct.unpack("!I", msg[40:44])[0]
    return val - NTP_DELTA


def get_timetuple():
    # (year, month, day, hour, minute, second, day_of_the_week, day_of_the_year)
    t=ntptime()
    t = t + 9*60*60
    #print(t)
    datetimetuple = time.gmtime(t)
    return datetimetuple


def connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while wlan.isconnected() == False:
        print('Waiting for connection...')
        time.sleep(1)
    ip = wlan.ifconfig()[0]
    print(f'Connected on {ip}')
    return ip


def webhook(empty = False): # empty = True: newone, empty = False: deactive
    global card_empty, card_someone, count, start_time, end_time, last_time, INTERVAL, white
    white.high()
    print('webhook called')
    if empty:
        card = card_newone
        summary = '誰か来たみたい(=^・・^=)'
    else:
        start = time.localtime(start_time)
        last = time.localtime(last_time)
        start = str(f'{start[3]}:{start[4]:02}')
        last = str(f'{last[3]}:{last[4]:02}')
        card = card_deactive.replace('{times}', str(count)).replace('{start}', start).replace('{last}', last).replace('{inter}', str(INTERVAL))
        summary = '誰もいないかも…（´・ω・｀）'
    payload = '''{
        "type":"message",
        "summary":"{summary}",
        "attachments":[
            {
            "contentType":"application/vnd.microsoft.card.adaptive",
            "contentUrl":null,
            "content": {card}
            }
        ]
        }'''.replace('{card}', card).replace('{summary}', summary)
    responce = urequests.post(URL, headers={"Content-Type": "application/json; charset=utf-8"}, data=payload.encode())
    print(responce.status_code)
    print(responce.text)
    responce.close()
    print('webhook sent')
    white.low()
    

def timer_init():
    # don't use
    global start_time, end_time
    start_time = time.localtime(time.time())
    left_mi = (60 - start_time[4]) % 30 - 1
    left_se = 60 - start_time[5]
    end_time = time.localtime(time.mktime(start_time) + left_mi * 60 + left_se)


def init_endtime():
    global end_time
    end_time = time.time() + 10 * 24 * 60 * 60


def set_timer():
    global end_time, last_time
    last_time = time.time()
    end_time = last_time + INTERVAL * 60


def reset_timer():
    global start_time, end_time
    start_time = time.time()
    end_time = time.time() + INTERVAL * 60


def wake(e):
    global door_open
    print(door_open)
    door_open = True


def door_fn():
    print('door open')
    global empty, count, blue, end_time, door_open, last_time, yellow
    yellow.low()
    set_timer()
    blue.high()
    if empty:
        webhook(empty=True)
        reset_timer()
    else:
        time.sleep(5)
    time.sleep(5)
    door_open = False
    empty = False
    count += 1
    blue.low()


def door_reset():
    global door_open, empty, count, yellow
    door_open = False
    empty = True
    yellow.high()
    count = 0


def addup():
    global count, yellow
    print('addup')
    webhook(empty=False)
    door_reset()
    init_endtime()


def loop():
    global empty, end_time, door_open, blue
    print('into loop')
    while True:
        blue.low()
        if door_open:
            door_fn()
        if time.time() - end_time > 0:
            addup()


def set_time():
    global rtc
    now = get_timetuple()
    rtc_fmt = convert_time2rtc(now)
    rtc.datetime(rtc_fmt)
    print('Time set from NTP')


def pin_init():
    global white, yellow, blue, red
    white = machine.Pin(3, machine.Pin.OUT)
    yellow = machine.Pin(4, machine.Pin.OUT)
    blue = machine.Pin(5, machine.Pin.OUT)
    red = machine.Pin(6, machine.Pin.OUT)
    white.low()
    yellow.low()
    blue.low()
    red.low()


def door_init():
    global door, door_open, count
    door = machine.Pin(27, machine.Pin.IN, machine.Pin.PULL_UP)
    door.irq(handler=wake, trigger=machine.Pin.IRQ_FALLING)
    count = 0
    door_open = False


def time_init():
    global rtc
    rtc = machine.RTC()
    set_time()


try:
    print('Booting...')
    pin_init()
    
    white.high()
    connect()
    time_init()
    init_endtime()
    door_init()
    white.low()
    
    empty = True
    yellow.high()
    loop()
except:
    pass

red.high()