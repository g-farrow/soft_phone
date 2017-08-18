import pjsua as pj
import logging
import time

logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] [%(module)s] [%(funcName)s] [%(levelname)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


def log_cb(level, str, len):
    """
    Logging Callback
    """
    print(str,)


class CallCallback(pj.CallCallback):
    """
    Callback to receive events from Call
    """

    def __init__(self, call=None):
        pj.CallCallback.__init__(self, call)


class IncomingCallCallback(pj.AccountCallback):
    """
    Callback to answer incoming Calls
    """

    def __init__(self, account, sip_phone, action_on_incoming_call, audio_playback_file=None, loop=True):
        pj.AccountCallback.__init__(self, account)
        self.action_on_incoming_call = action_on_incoming_call
        self.sip_phone = sip_phone
        self.audio_playback_file = audio_playback_file
        self.loop = loop

    def on_incoming_call(self, call):
        """
        Receiver reaction dictates whether the call is to be answered or not
        """
        logger.debug("[{}] [INCOMING] Incoming call has been detected...".format(self.sip_phone.pbx_account_name))
        self.sip_phone.call = call
        if self.action_on_incoming_call.upper() == "ANSWER":  # ANSWERED
            logger.debug("[{}] [INCOMING] The intended disposition of this call is 'answered', answering the incoming"
                         " call...".format(self.sip_phone.pbx_account_name))
            time.sleep(1)
            call.answer()
            logger.info("[{}] [INCOMING] Call answered".format(self.sip_phone.pbx_account_name))
            if self.audio_playback_file:
                self.sip_phone.start_audio_playback(self.audio_playback_file, self.loop)

        elif self.action_on_incoming_call.upper() == "BUSY":  # destination number rejects the call before it is answered
            logger.debug("[{}] [INCOMING] The intended disposition of this call is 'busy', rejecting the incoming "
                         "call...".format(self.sip_phone.pbx_account_name))
            # https://en.wikipedia.org/wiki/List_of_SIP_response_codes
            call.answer(486)  # busy status
            logger.info("[{}] [INCOMING] The intended disposition of this call is 'busy' - busy tone was "
                        "returned".format(self.sip_phone.pbx_account_name))
        else:
            logger.error("[{}] [INCOMING] Could not handle incoming call".format(self.sip_phone.pbx_account_name))
