#
# Copyright (C) 2010-2012 Vinay Sajip.
# All rights reserved. Licensed under the new BSD license.
#
import logging
import logging.handlers

from logutils.colorize import ColorizingStreamHandler


def setup_logging(logger, debug=False):

    fmt_str = "%(asctime)s: %(levelname)s:" \
              " %(module)s.%(funcName)s():%(lineno)d: %(message)s"
    ColorizingStreamHandler.level_map = {
        logging.DEBUG: (None, 'blue', False),
        logging.INFO: (None, 'green', False),
        logging.WARNING: (None, 'yellow', False),
        logging.ERROR: (None, 'red', False),
        logging.CRITICAL: ('red', 'white', True),
    }
    console_handler = ColorizingStreamHandler()
    console_handler.setFormatter(logging.Formatter(fmt_str))
    logger.handlers = []
    logger.addHandler(console_handler)
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)


def clogging_main():
    root = logging.getLogger()
    setup_logging(root, debug=True)

    logging.debug('DEBUG')
    logging.info('INFO')
    logging.warning('WARNING')
    logging.error('ERROR')
    logging.critical('CRITICAL')


if __name__ == '__main__':
    clogging_main()
