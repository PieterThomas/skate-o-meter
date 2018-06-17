from RPi import GPIO
import serial
import time
import datetime
import socket

from AH3661 import AH3661
from LCD import LCD
import datatodb


# try:
#     from .AH3661 import AH3661
# except Exception:
#     from AH3361 import AH3361
#
# try:
#     from .LCD import LCD
# except Exception:
#     from LCD import LCD
#
# try:
#     from .serialRead import serialReadBadgeID
# except Exception:
#     from serialRead import serialReadBadgeID
#
# try:
#     from .showIP import get_ip_address
# except Exception:
#     from showIP import get_ip_address

# region Functions

def serialReadBadgeID(path='/dev/ttyUSB0'):
    ser = serial.Serial(path, 9600)
    _id = ""
    id_found = True
    while id_found:
        naam = ser.read_all()
        plaats = str(naam).find("UID:")
        if plaats != -1:
            uidSerial = naam[plaats + 3:plaats + 14]
            uid = str(uidSerial, 'utf-8')
            _id = uid.replace(" ", "")
            id_found = False
            print(_id)
        time.sleep(0.25)
    return _id, True


def initLCD(lcd=LCD()):
    lcd.stuur_instructie(56)  # 8-bit, 2 lines, character font 5x10
    lcd.stuur_instructie(12)  # display aan, cursor uit, cursor blink uit
    lcd.stuur_instructie(1)  # clear display en cursor home


def toon_start_info(lcd=LCD()):
    initLCD()
    lcd.stuur_tekst("Programma wordt gestart")
    time.sleep(2)

    lcd.stuur_instructie(1)
    lcd.stuur_tekst("IP adres wordt getoond in 3")
    time.sleep(1)

    lcd.stuur_instructie(0x4B | 0b10000000)
    lcd.stuur_tekst("2")
    time.sleep(1)

    lcd.stuur_instructie(0x4B | 0b10000000)
    lcd.stuur_tekst("1")
    time.sleep(1)

    lcd.stuur_instructie(1)
    lcd.stuur_tekst(str(get_ip_address()))  # Toon ip address op scherm
    time.sleep(5)

    lcd.stuur_instructie(1)


def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip_address = s.getsockname()[0]
    s.close()
    return ip_address


def buzzer(gelukt):
    if gelukt:
        GPIO.output(18, True)
        time.sleep(0.5)
        GPIO.output(18, False)
    else:
        for i in range(0, 3):
            GPIO.output(18, True)
            time.sleep(0.3)
            GPIO.output(18, False)
            time.sleep(0.2)


def init_speed_distance(lcd=LCD()):
    lcd.stuur_tekst("Snelheid:")
    lcd.stuur_instructie(0x40 | 0b10000000)
    lcd.stuur_tekst("Afstand:")
    lcd.stuur_instructie(12)


# endregion


def sessie(hall=AH3661(26)):
    GPIO.setup(18, GPIO.OUT)
    while True:
        global stop
        stop = False

        uid, found = serialReadBadgeID()  # get BadgeID
        correctuid = datatodb.correct_badgeID(uid)  #  Check badgeID

        if found is True and correctuid is True:
            init_speed_distance()  # Standard values on LCD
            buzzer(True)  # when badged, buzz

            datatodb.create_session(uid, datetime.datetime.now())  # Create session

            hall.create_event() # create event

            uid2, stop = serialReadBadgeID() # get badgeID
            correctuid2 = datatodb.correct_badgeID(uid2)  # Check badgeID
            if found is stop and correctuid2 is True:
                buzzer(True) # when badged, buzz

                eind = datetime.datetime.now()
                print("sessie is gedaan")
                datatodb.save_session(eind, round(hall.distance, 2))
                hall.remove_event()  # delete session
                lcd = LCD()
                lcd.stuur_instructie(1)
                break
        else:
            buzzer(False)  # when badged, buzz
            pass


def main():
    GPIO.setmode(GPIO.BCM)
    try:
        toon_start_info()
        while True:
            sessie()
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.setwarnings(False)  # get rid of warning when no GPIO pins set up
        GPIO.cleanup()


if __name__ == '__main__':
    main()
