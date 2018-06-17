import logging
import signal
import subprocess
from time import sleep
import mysql.connector as mysql
import datetime

log = logging.getLogger(__name__)

running = True


def correct_badgeID(badgeID):
    try:
        conn = mysql.connect(database='skateometerdb', user='som-admin', password='pieter9810')
        cursor = conn.cursor()
        cursor.execute('SELECT BadgeID FROM skateometerdb.users WHERE BadgeID='"%s"'', (badgeID,))
        for i in cursor:
            if i[0] == badgeID:
                return True
            else:
                return False

    except Exception as e:
        log.exception("DB read failed: {!s}".format(e))


def create_session(badgeID, startijd):
    try:
        conn = mysql.connect(database='skateometerdb', user='som-admin', password='pieter9810')
        cursor = conn.cursor()
        sessionID = ""
        cursor.execute("SELECT MAX(SessionID+1) FROM skateometerdb.session")
        for session in cursor:
            sessionID = session[0]

        cursor.execute("INSERT INTO skateometerdb.session (SessionID, BadgeID, Starttime) VALUES (%s, %s, %s)",
                       (sessionID, badgeID, startijd))
        conn.commit()
        log.debug("Session created {}={} to database".format(sessionID, badgeID))
        return True
    except Exception as e:
        log.exception("DB create failed: {!s}".format(e))


def save_data(timeHM, speed):
    try:
        conn = mysql.connect(database='skateometerdb', user='som-admin', password='pieter9810')
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(SessionID) FROM skateometerdb.session")
        for session in cursor:
            sessionID = session[0]

        cursor.execute("INSERT INTO skateometerdb.data (SessionID, TimeHM, Speed) VALUES (%s, %s, %s)",
                       (sessionID, timeHM, speed))
        conn.commit()
        log.debug("Saved data {}={} to database".format(timeHM, speed))
        return True
    except Exception as e:
        log.exception("DB save failed: {!s}".format(e))


def save_session(stoptime, distance):
    try:
        conn = mysql.connect(database='skateometerdb', user='som-admin', password='pieter9810')
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(SessionID) FROM skateometerdb.session")
        for session in cursor:
            sessionID = session[0]

        cursor.execute(
            "UPDATE skateometerdb.session SET Endtime = (%s), Distance = (%s) WHERE SessionID=%s",
            (stoptime, distance, sessionID))
        conn.commit()
        log.debug("Updated session {0}-{1} to database".format(stoptime, distance))
        return True
    except Exception as e:
        log.exception("DB update failed: {!s}".format(e))
