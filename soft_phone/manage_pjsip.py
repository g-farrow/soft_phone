import pjsua as pj
import logging
from .callbacks import log_cb

logging.basicConfig(level=logging.DEBUG, format='[%(asctime)s] [%(funcName)s] [%(levelname)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


class PJSipClient:
    """
    Manage the PJSip instance
    """

    def __init__(self):
        self.lib = pj.Lib()  # Create library instance
        self.lib.init(log_cfg=pj.LogConfig(level=6, callback=log_cb,
                                           filename="/tmp/pjsip.log"))  # Init library with default config
        self.lib.create_transport(pj.TransportType.UDP)  # Create UDP transport which listens to any available port
        self.lib.set_null_snd_dev()  # disable the sound card

    def start(self):
        """ Startup the PJSIP instance ready for use """
        logger.debug("Starting the PJSIP instance")

        self.lib.start()  # Start the library
        logger.debug("PJSIP instance successfully started")

    def stop(self):
        logger.debug("Preparing to destroy PJSip")
        self.lib.destroy()
        logger.info("PJSip instance has been destroyed")
