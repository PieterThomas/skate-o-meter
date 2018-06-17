from time import sleep
from RPi import GPIO

GPIO.setmode(GPIO.BCM)
lcd_rs = 23
lcd_en = 24
lcd_d0 = 5
lcd_d1 = 6
lcd_d2 = 12
lcd_d3 = 13
lcd_d4 = 16
lcd_d5 = 19
lcd_d6 = 20
lcd_d7 = 21


class LCD:
    def __init__(self, lcd_rs=23, lcd_en=24, lcd_d0=5, lcd_d1=6, lcd_d2=12, lcd_d3=13, lcd_d4=16, lcd_d5=19, lcd_d6=20,
                 lcd_d7=21):
        self.lcd_rs = lcd_rs
        self.lcd_en = lcd_en
        self.lcd_d0 = lcd_d0
        self.lcd_d1 = lcd_d1
        self.lcd_d2 = lcd_d2
        self.lcd_d3 = lcd_d3
        self.lcd_d4 = lcd_d4
        self.lcd_d5 = lcd_d5
        self.lcd_d6 = lcd_d6
        self.lcd_d7 = lcd_d7

        # region Setup
        GPIO.setup(self.lcd_en, GPIO.OUT)
        GPIO.setup(self.lcd_rs, GPIO.OUT)
        GPIO.setup(self.lcd_d0, GPIO.OUT)
        GPIO.setup(self.lcd_d1, GPIO.OUT)
        GPIO.setup(self.lcd_d2, GPIO.OUT)
        GPIO.setup(self.lcd_d3, GPIO.OUT)
        GPIO.setup(self.lcd_d4, GPIO.OUT)
        GPIO.setup(self.lcd_d5, GPIO.OUT)
        GPIO.setup(self.lcd_d6, GPIO.OUT)
        GPIO.setup(self.lcd_d7, GPIO.OUT)
        # endregion

    def stuur_instructie(self, instr):
        GPIO.output(self.lcd_en, GPIO.HIGH)
        GPIO.output(self.lcd_rs, GPIO.LOW)
        self.set_GPIO_bits(instr)
        sleep(0.005)
        GPIO.output(self.lcd_en, GPIO.LOW)

    def stuur_teken(self, waarde):
        ascii = ord(waarde)
        GPIO.output(self.lcd_en, GPIO.HIGH)
        GPIO.output(self.lcd_rs, GPIO.HIGH)
        self.set_GPIO_bits(ascii)
        sleep(0.005)
        GPIO.output(self.lcd_en, GPIO.LOW)  # Bij low wordt data verwerkt.

    def stuur_tekst(self, tekst):
        secondline = False

        for i in range(len(tekst)):
            self.stuur_teken(tekst[i])
            if (tekst[i] == " ") and (" " not in tekst[(i + 1):16]) and (tekst[15] != " ") and secondline == False:
                instructie = int(0x40 | 0b10000000)  # een ddram moet je bit 7 toevoegen
                self.stuur_instructie(instructie)  # volgende lijn. set ddram cursor position 0x40
                secondline = True
            if (i == 15 and secondline == False):
                instructie = int(0x40 | 0b10000000)  # een ddram moet je bit 7 toevoegen
                self.stuur_instructie(instructie)  # volgende lijn. set ddram cursor position 0x40
                secondline = True

    def set_GPIO_bits(self, byte):
        list_digits = [lcd_d0, lcd_d1, lcd_d2, lcd_d3, lcd_d4, lcd_d5, lcd_d6, lcd_d7]
        for i in range(0, 8):
            if (byte & (2 ** i)) == 0:
                GPIO.output(list_digits[i], GPIO.LOW)
            else:
                GPIO.output(list_digits[i], GPIO.HIGH)
