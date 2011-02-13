from couchpotato import app
from couchpotato.api import api
from couchpotato.core.logger import CPLog
from couchpotato.core.settings import Settings
from couchpotato import web
from logging import handlers
from optparse import OptionParser
import logging
import os.path
import sys


def cmd_couchpotato(base_path):
    '''Commandline entry point.'''

    # Options
    parser = OptionParser('usage: %prog [options]')
    parser.add_option('-s', '--datadir', dest = 'data_dir', default = base_path, help = 'Absolute or ~/ path, where settings/logs/database data is saved (default ./)')
    parser.add_option('-t', '--test', '--debug', action = 'store_true', dest = 'debug', help = 'Debug mode')
    parser.add_option('-q', '--quiet', action = 'store_true', dest = 'quiet', help = "Don't log to console")
    parser.add_option('-d', '--daemon', action = 'store_true', dest = 'daemonize', help = 'Daemonize the app')

    (options, args) = parser.parse_args(sys.argv[1:])

    # Create data dir if needed
    if not os.path.isdir(options.data_dir):
        options.data_dir = os.path.expanduser(options.data_dir)
        os.makedirs(options.data_dir)

    # Create logging dir
    log_dir = os.path.join(options.data_dir, 'logs');
    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)


    # Register settings
    settings = Settings(os.path.join(options.data_dir, 'settings.conf'))
    debug = options.debug or settings.get('debug', default = False)


    # Logger
    logger = logging.getLogger()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', '%H:%M:%S')
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)

    # To screen
    if debug and not options.quiet:
        hdlr = logging.StreamHandler(sys.stderr)
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)

    # To file
    hdlr2 = handlers.RotatingFileHandler(os.path.join(log_dir, 'CouchPotato.log'), 'a', 5000000, 4)
    hdlr2.setFormatter(formatter)
    logger.addHandler(hdlr2)


    # Start logging
    log = CPLog(__name__)
    log.debug('Started with params %s' % args)


    # Load configs
    from couchpotato.core.settings.loader import SettingsLoader
    sl = SettingsLoader(root = base_path)
    sl.addConfig('couchpotato', 'core')
    sl.run()


    # Create app
    api_key = settings.get('api_key')
    url_base = '/%s/' % settings.get('url_base')

    # Basic config
    app.host = settings.get('host', default = '0.0.0.0')
    app.port = settings.get('port', default = 5000)
    app.debug = debug
    app.secret_key = api_key
    app.static_path = url_base + 'static'

    # Add static url with url_base
    app.add_url_rule(app.static_path + '/<path:filename>',
                      endpoint = 'static',
                      view_func = app.send_static_file)

    # Register modules
    app.register_module(web, url_prefix = url_base)
    app.register_module(api, url_prefix = '%sapi/%s' % (url_base, api_key))

    # Go go go!
    app.run()