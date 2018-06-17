from RPi import GPIO
import time
import datetime
import datatodb
from LCD import LCD


class AH3661():
    def __init__(self, hall=26):
        self.pin = hall

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.__start = datetime.datetime.now()
        self.__prevdistance = 0.0000000
        self.__pulsetime = 0
        self.__timepassed = 0
        self.__wheel_m = 0.00169646003293848834876982742697
        self.__distance = 0
        self.__speed = 0.00
        self.__pulse = 0
        self.__averagespeed = 0

    @property
    def distance(self):
        return self.__distance

    @distance.setter
    def distance(self, value):
        if value != -1:
            self.__distance += value
        else:
            self.__distance = 0
    @property
    def speed(self):
        return self.__speed

    @speed.setter
    def speed(self, value):
        self.__speed = value

    def create_event(self):
        GPIO.add_event_detect(self.pin, GPIO.FALLING, callback=self._callback_pulse, bouncetime=2)

    def _callback_pulse(self, pin):
        self.__pulsetime = datetime.datetime.now()  # Tijd opvragen van wanneer de pulse plaat vindt
        self.__timepassed = self.__pulsetime - self.__start  # Nodig om snelheid te berekenen

        self.speed = 3600 * self.__wheel_m / self.__timepassed.total_seconds()  # Snelheid berekenen

        self.distance = self.__wheel_m  # Distance optellen met omtrek voor het wiel
        self.__start = self.__pulsetime

        self.__averagespeed += self.__speed

        self.__pulse += 1
        if self.__pulse == 3:
            datatodb.save_data(self.__pulsetime, round((self.__averagespeed / self.__pulse), 2))
            self.__pulse, self.__averagespeed = 0, 0

        self.show_on_lcd()

        # print("Seconds: " + str(self.__timepassed.total_seconds()))
        # print("Speed: " + str(round(self.speed, 2)))
        # print("Afstand: " + str(round(self.__distance, 2)))
        print("f")

    def show_on_lcd(self):
        lcd = LCD()
        lcd.stuur_instructie(0x0C | 0b10000000)
        lcd.stuur_tekst(str(round(self.speed, 2)))
        lcd.stuur_instructie(0x4C | 0b10000000)
        lcd.stuur_tekst(str(round(self.distance,2)))
        lcd.stuur_instructie(12)

    def remove_event(self):
        self.distance = -1
        self.speed = 0
        GPIO.remove_event_detect(self.pin)
