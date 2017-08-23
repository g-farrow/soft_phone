import pjsua as pj
import time
import logging
from soft_phone.callbacks import IncomingCallCallback, CallCallback
from soft_phone.exceptions import PhoneCallNotInProgress
from datetime import datetime

logger = logging.getLogger(__name__)
logging.addLevelName(5, "TRACE")


class SoftPhone:
    """
    'Soft Phone' to act as a device for making or receiving phone calls
    """
    account = None
    call = None
    call_slot_number = None
    audio_player_id = None
    audio_player_slot_id = None

    def __init__(self, pjsip_client, pbx_ip, pbx_account_name, pbx_password, answer_audio=None, loop=True,
                 action_on_incoming_call="ANSWER"):
        """
        :param pjsip_client: Established instance of PJSip Lib
        :param pbx_account_name: String - the telephone number to register as
        :param answer_audio: String - File path of a WAV file which should be played once an incoming call is answered
        :param loop: Boolean - Indicate if the audio file should be looped (True), or played once (False)
        """
        self.lib = pjsip_client.lib
        self.pbx_ip = pbx_ip
        self.pbx_account_name = pbx_account_name
        self.pbx_password = pbx_password
        self.answer_audio = answer_audio
        self.loop = loop
        self.action_on_incoming_call = action_on_incoming_call

    def _register_thread(self):
        """
        Register the thread with PJSip
        """
        logger.debug("[{}] Registering thread with PJSip".format(self.pbx_account_name))
        self.lib.thread_register(self.pbx_account_name)
        logger.info("[{}] Thread registered with PJSip".format(self.pbx_account_name))

    def _create_and_register_account_with_pbx(self):
        """
        Create and register an account for the phone instance with the PBX
        """
        logger.debug("[{}] Creating account with domain = {}, username = {} and password = {}".format(
            self.pbx_account_name, self.pbx_ip, self.pbx_account_name, self.pbx_password))
        account = pj.AccountConfig(self.pbx_ip, self.pbx_account_name, self.pbx_password)
        self.account = self.lib.create_account(
            account, cb=IncomingCallCallback(account, self, action_on_incoming_call=self.action_on_incoming_call,
                                             audio_playback_file=self.answer_audio, loop=self.loop)
        )
        logger.log(5, "[{}] Registration info - {}".format(self.pbx_account_name, vars(self.account.info())))
        logger.info("[{}] Account created".format(self.pbx_account_name))

    def register_soft_phone(self):
        """
        Start the phone's thread (allowing it to be run in parallel to the main process thread
        then register the account and set the 'receiver callback'
        """

        self._register_thread()
        self._create_and_register_account_with_pbx()
        start_time = time.time()
        for i in range(0, 10):
            if self.account.info().reg_status == 200:
                logger.debug("[{}] [RUN] Account is now registered".format(self.pbx_account_name))
                break
            time.sleep(1.0 - ((time.time() - start_time) % 1.0))

    def _wait_for_soft_phone_registration_to_end(self, time_out=10):
        """
        Wait for the Soft Phone's registration status to be False
        """
        logger.debug("[{}] Waiting for registration status to be False".format(self.pbx_account_name))
        logger.log(5, "[{}] Registration info - {}".format(self.pbx_account_name, vars(self.account.info())))
        start_time = datetime.now()
        while (datetime.now() - start_time).seconds <= time_out:
            if self.account.info().reg_expires == -1:
                logger.log(5, "[{}] Registration status is now False".format(self.pbx_account_name))
                break
            time.sleep(0.5)
            logger.log(5, "[{}] Registration info - {}".format(
                self.pbx_account_name, vars(self.account.info())))

    def unregister_soft_phone(self):
        """
        Unregister and delete the account when the call has ended
        """
        logger.info("[{}] Unregistering phone".format(self.pbx_account_name))
        logger.log(5, "[{}] Registration info - {}".format(
            self.pbx_account_name, vars(self.account.info())))
        self.account.set_registration(False)
        logger.debug("[{}] Deleting account".format(self.pbx_account_name))
        self._wait_for_soft_phone_registration_to_end()
        self.account.delete()  # delete account
        if self.call:
            logger.debug("[{}] Attempting to delete the call object".format(self.pbx_account_name))
            del self.call  # need to delete the call object after it is finished.
            logger.debug("[{}] Call object has been deleted".format(self.pbx_account_name))
        logger.info("[{}] Sip Phone has been unregistered".format(self.pbx_account_name))

    def _wait_for_active_media_state_on_call(self, time_out=10, required_media_state=1):
        """
        Wait for the duration of the timeout for a call to become 'valid'
        :param time_out: Int - Number of seconds to wait for the required media state
        :param required_media_state: Int - "1" for connected call, "0" for other media state, e.g. busy
        """
        for i in range(time_out):
            if str(self.call.is_valid()) == "1":
                if self.call.info().media_state == pj.MediaState.ACTIVE:
                    logger.info("[{}] MediaState ACTIVE".format(self.pbx_account_name))
                    logger.log(5, "[{}] Call info - %s".format(self.pbx_account_name, vars(self.call.info())))
                    break
                logger.debug("[{}] Waiting for MediaState ACTIVE (ringing)".format(self.pbx_account_name))
                logger.log(5, "[{}] Call info - %s".format(self.pbx_account_name, vars(self.call.info())))
            else:
                logger.debug("[{}] Call is not valid".format(self.pbx_account_name))
                if required_media_state == 0:
                    logger.info("[{}] Required call media state (0) has occurred".format(self.pbx_account_name))
                    return
                else:
                    logger.error("[{}] Expected call to be answered, but it was dropped".format(self.pbx_account_name))
                    return
            time.sleep(0.1)
        # TODO This needs some better testing and evaluation

    def make_call(self, number_to_dial, protocol="sip"):
        """
        Dial a number/start a call
        """
        logger.debug("[{}] Making call to {}".format(self.pbx_account_name, number_to_dial))
        self.call = self.account.make_call("{}:{}@{}".format(protocol, number_to_dial, self.pbx_ip, CallCallback()))
        logger.log(5, "[{}] Call info: {}".format(self.pbx_account_name, vars(self.call.info())))

        for i in range(1, 120):
            if self.call.info().state_text == "CONFIRMED":  # dialler and AGI have established a connection
                logger.log(5, "[{}] Call info - {}".format(self.pbx_account_name, vars(self.call.info())))
                logger.info("[{}] Number dialled and connected (call in progress)".format(self.pbx_account_name))
                break
            logger.debug("[{}] Waiting for call state to be CONFIRMED".format(self.pbx_account_name))
            logger.log(5, "[{}] Call info - {}".format(self.pbx_account_name, vars(self.call.info())))
            time.sleep(0.1)
        if self.call.info().state_text != "CONFIRMED":
            logger.log(5, "[{}] Call state is '{}'".format(self.pbx_account_name, self.call.info().state_text))

    def _validate_phone_call_in_progress(self):
        """
        Check to see if the Phone Call is in progress and raise an exception if it is not.
        """
        if not self.call:
            raise PhoneCallNotInProgress("The call does not exist")

    def get_call_length(self):
        """
        Return the length of the call connection and the total length of the call (in seconds)
        :return call_length, total_length: Tuple (Call Connection length (seconds), Total Length (seconds))
        """
        self._validate_phone_call_in_progress()
        call_length = self.call.info().call_time
        total_length = self.call.info().total_time
        # logger.debug("[{}] Call duration information found: connection '{}' second/s, total '{}' "
        #              "second/s".format(self.pbx_account_name, call_length, total_length))
        return call_length, total_length

    def wait_for_specific_call_connection_length(self, desired_call_length):
        """
        Wait until a phone call has reached a specific Call Connection duration
        :param desired_call_length: Int - Seconds
        """
        self._validate_phone_call_in_progress()
        loop_delay = 0.1
        last_log_time = datetime.now()
        while True:
            call_connection_length, call_total_length = self.get_call_length()
            if call_connection_length >= desired_call_length:
                logger.debug("[{}] The desired call connection duration ({} seconds) has been "
                             "reached".format(self.pbx_account_name, desired_call_length))
                return True
            time.sleep(loop_delay)
            if (datetime.now() - last_log_time).total_seconds() >= 5:
                last_log_time = datetime.now()
                logger.debug("[{}] Waiting for the call connection time ({} seconds) to reach the desired {} seconds"
                             "".format(self.pbx_account_name, round(call_connection_length), desired_call_length))

    @staticmethod
    def _round_up_current_datetime_seconds(round_value=5):
        """
        Get the current datetime seconds, rounded up to the nearest 'rounded_value'
        :param round_value: Int - What to round the result up by
        :return: Int - Number of seconds in "now" rounded up to the nearest 'rounded_value'
        """
        return int(round_value * round(float(int(datetime.now().strftime("%S"))) / round_value))

    def wait_for_a_call_to_occur(self, time_out=60):
        """
        Wait for a call to happen, then continue when it does (with a time out)
        :param time_out: Int - The maximum number of seconds to wait for a call to happen
        """
        logger.info("[{}] Waiting for a call to happen".format(self.pbx_account_name))
        start_time = datetime.now()
        log_seconds = self._round_up_current_datetime_seconds()
        while (datetime.now() - start_time).seconds <= time_out:
            if self.call:
                logger.info("[{}] Call appears to have occurred, moving on".format(self.pbx_account_name))
                break
            candidate_log_seconds = self._round_up_current_datetime_seconds()
            if log_seconds != candidate_log_seconds:
                log_seconds = candidate_log_seconds
                logger.debug("[{}] Waiting for an incoming call...".format(self.pbx_account_name))
            time.sleep(0.1)

    def wait_for_existing_call_to_end(self, time_out=60):
        """
        Wait for an existing call to end, then continue when it does (with a time out)
        :param time_out: Int - The maximum number of seconds to wait for a call to happen
        """
        if not self.call:
            raise PhoneCallNotInProgress("Cannot wait for call to end, as it has not started!")
        logger.info("Waiting for a call to end")
        start_time = datetime.now()
        log_seconds = self._round_up_current_datetime_seconds()
        while (datetime.now() - start_time).seconds <= time_out:
            if not self.call.is_valid():
                logger.info("[{}] Call has ended, moving on".format(self.pbx_account_name))
                break
            candidate_log_seconds = self._round_up_current_datetime_seconds()
            if log_seconds != candidate_log_seconds:
                log_seconds = candidate_log_seconds
                logger.debug("[{}] Waiting for the call to end...".format(self.pbx_account_name))
            time.sleep(0.1)

    def hang_up(self):
        """
        End an in progress call
        """
        logger.debug("[{}] Hang up call requested".format(self.pbx_account_name))
        if self.call.is_valid() == 1:
            self.call.hangup()
            logger.info("[{}] Call has now hung up".format(self.pbx_account_name))
            if self.audio_player_id:  # if audio playback is on, stop it
                self.stop_audio_playback()
        else:
            logger.info("[{}] Call was already disconnected".format(self.pbx_account_name))

    def send_dtmf_key_tones(self, digits):
        """
        Send DTMF keypad tones to the call
        :param digits: String - Digits to send over the call
        """
        logger.debug("[{}] Sending DTMF key tones '{}'".format(self.pbx_account_name, digits))
        self.call.dial_dtmf(digits)
        logger.debug("[{}] DTMF tones sent".format(self.pbx_account_name))

    def start_audio_playback(self, audio_file_path, loop=True):
        """
        Play audio (WAV) on the call
        :param audio_file_path: String - path to the audio (WAV) file to be  played on the call
        :param loop: Boolean - Should the audio file be played in a loop (True), or just once (False)
        """
        logger.debug("[{}] Attempting to play audio from {}".format(self.pbx_account_name, audio_file_path))
        import os
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError("[{}] Cannot find your audio file: {}".format(self.pbx_account_name,
                                                                                  audio_file_path))
        if not os.path.isfile(audio_file_path):
            raise FileNotFoundError("[{}] Your audio file is not a file: {}".format(self.pbx_account_name,
                                                                                    audio_file_path))
        self.call_slot_number = self.call.info().conf_slot
        self.audio_player_id = self.lib.create_player(audio_file_path, loop=loop)
        self.audio_player_slot_id = self.lib.player_get_slot(self.audio_player_id)
        self.lib.conf_connect(self.audio_player_slot_id, self.call_slot_number)
        logger.debug("[{}] Audio file '{}' is now being played on the call".format(self.pbx_account_name,
                                                                                   audio_file_path))

    def stop_audio_playback(self):
        """
        Stop the audio playback on the call
        """
        self.lib.conf_disconnect(self.audio_player_slot_id, self.call_slot_number)
        self.lib.player_destroy(self.audio_player_id)
        logger.debug("[{}] Audio playback on the call has ben stopped".format(self.pbx_account_name))
