import os
import time
import threading
import signal
import pjsua as pj


class softPhone():  # set up an instance of a telephone

    def __init__(self, testData, telephone_number, answeredCall, intendedDisposition):

        def startThread():
            self.logger.info(
                "[%s:%s] [START] Thread started for %s" % (self.thread_id, self.telephone_number, self.thread_id))

        self.answeredCall = answeredCall
        self.logger = testData['logger']
        testData['thread_id'] += 1
        self.thread_id = testData['thread_id']
        self.telephone_number = telephone_number
        self.t = threading.Thread(target=startThread)
        self.intendedDisposition = intendedDisposition.upper()
        self.logger.info(
            "[%s:%s] [INIT] Thread '%d' initialised" % (self.thread_id, self.telephone_number, self.thread_id))
        self.logger.info("[%s:%s] [INIT] Telephone number for this instance is %s" % (
        self.thread_id, self.telephone_number, telephone_number))
        self.callLength = int(testData['callLength'])
        self.results = []






    def playSound(self, testData):
        ''' Play a sound file during the call and confirm that call has been connected '''
        if self.thread_id == 1: sound_file = execution_data + "00_Generic/Yamaha-TG500-CH-Ghost-C4.wav"
        if self.thread_id == 2: sound_file = execution_data + "00_Generic/Crazed-Bells.wav"

        self.logger.debug(
            "[%s:%s] [PLAY SOUND] Sound file has been set to: %s" % (self.thread_id, self.telephone_number, sound_file))
        if self.call.is_valid() == 1:
            self.call_slot_number = self.call.info().conf_slot  # get the slot number of the 'call'
            self.logger.debug("[%s:%s] [PLAY SOUND] call_slot_number = %s" % (
            self.thread_id, self.telephone_number, self.call_slot_number))
            self.player_id = testData['pjsipLib'].create_player(sound_file, loop=True)  # create a media player
            self.logger.debug(
                "[%s:%s] [PLAY SOUND] player_id = %s" % (self.thread_id, self.telephone_number, self.player_id))
            self.media_player_slot_number = testData['pjsipLib'].player_get_slot(
                self.player_id)  # get player slot number
            self.logger.debug("[%s:%s] [PLAY SOUND] media_slot_number = %s" % (
            self.thread_id, self.telephone_number, self.media_player_slot_number))
            if self.call.is_valid() == 1:
                testData['pjsipLib'].conf_connect(self.media_player_slot_number,
                                                  self.call_slot_number)  # connect the dialler instance and the media player to play the sound (similar to a conference call)
                self.logger.info("[%s:%s] [PLAY SOUND] Conf connect completed, we are now playing sound on the call" % (
                self.thread_id, self.telephone_number))
        else:
            self.logger.info(
                "[%s:%s] [PLAY SOUND] The 'playSound' function was not able to play a sound to the call. This is probably because the call is no longer valid (perhaps it was not answered?)" % (
                self.thread_id, self.telephone_number))

    def stopSound(self, testData):
        ''' Disconnect the conference call connection and hang up '''
        self.logger.debug("[%s:%s] [STOP SOUND] Preparing to disconnect the conf connection" % (
        self.thread_id, self.telephone_number))
        try:
            testData['pjsipLib'].conf_disconnect(self.media_player_slot_number,
                                                 self.call_slot_number)  # disconnect the conf connection
            self.logger.debug(
                "[%s:%s] [STOP SOUND] Conf connect disconnected" % (self.thread_id, self.telephone_number))
            testData['pjsipLib'].player_destroy(self.player_id)  # close the media player
            self.logger.debug("[%s:%s] [STOP SOUND] Media player closed" % (self.thread_id, self.telephone_number))
        except:
            self.logger.info(
                "[%s:%s] [STOP SOUND] Unable to disconnect the media player (was it even created in the first place?)" % (
                self.thread_id, self.telephone_number))

    def pressKeypad(self, digits):
        '''	Send DTMF keypad tones to the call '''
        self.logger.debug(
            "[%s:%s] [DTMF] Attempting to press DTMF key tones '%s'" % (self.thread_id, self.telephone_number, digits))
        try:
            self.call.dial_dtmf(digits)
            self.logger.info(
                "[%s:%s] [DTMF] Keypad tones sent for numbers '%s'" % (self.thread_id, self.telephone_number, digits))
        except Exception as e:
            self.logger.error("[%s:%s] [DTMF] Unable to send the DTMF Key tones for numbers '%s'" % (
            self.thread_id, self.telephone_number, digits))
            self.results.append("ERROR")
