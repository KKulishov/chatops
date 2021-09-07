from os import getenv, path
import logging

# This is a minimal configuration to get you started with the Text mode.
# If you want to connect Errbot to chat services, checkout
# the options in the more complete config-template.py from here:
# https://raw.githubusercontent.com/errbotio/errbot/master/errbot/config-template.py

#BACKEND = 'Text'  # Errbot will start in text mode (console only mode) and will answer commands from there.
#BACKEND = 'Telegram'
ERRBOT_ENV = getenv("ERRBOT_ENV")

if ERRBOT_ENV == "PROD":
    BACKEND = 'Telegram'
    BOT_TOKEN = getenv("BOT_TOKEN")
    BOT_IDENTITY = {
        'token': BOT_TOKEN,
    }
    CHATROOM_PRESENCE = ()
    BOT_LOG_LEVEL = logging.WARNING
elif ERRBOT_ENV == "DEV":
    BACKEND = 'Text'
    BOT_LOG_LEVEL = logging.DEBUG
else:
    print('Переменная ERRBOT_ENV не задана или задано, но она несоотвествует значением PROD или DEV')


current_dir = path.dirname(path.realpath(__file__))

BOT_DATA_DIR = current_dir + r'/data'
BOT_EXTRA_PLUGIN_DIR = current_dir + r'/plugins'

BOT_LOG_FILE = current_dir + r'/errbot.log'

BOT_ALT_PREFIXES = ('Bot', '/')
BOT_ALT_PREFIX_SEPARATORS = (',', ';')

#BOT_ADMINS = ('@CHANGE_ME', )  # !! Don't leave that to "@CHANGE_ME" if you connect your errbot to a chat system !!
BOT_ADMINS = ('@you_admin_name', 'you_admin_id')
