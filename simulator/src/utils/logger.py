import logging
import sys

def set_log_level():
    loglevel = 'info'
    if len(sys.argv) > 1:
        for arg in sys.argv:
            if arg.startswith('--log='):
                loglevel = arg.split('=')[1]
                break
    numeric_level = getattr(logging, loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)

    logging.basicConfig(level=numeric_level,
                        stream=sys.stdout,
                        format='%(asctime)s %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

Logger = logging.getLogger(__name__)
