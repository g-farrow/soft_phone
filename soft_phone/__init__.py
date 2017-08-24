import logging

logger = logging.getLogger(__name__).addHandler(logging.NullHandler())
logging.addLevelName(5, "TRACE")
