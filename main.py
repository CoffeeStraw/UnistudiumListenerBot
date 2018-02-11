'''
UnistudiumListener - Telegram Bot
Author: Porchetta (clarantonio98@gmail.com)

TO DO:
- Commit iniziale contenente info e comandi base                                [V]
- Comando per effettuare un tentativo di connessione con le credenziali         [V]
- Comando per aggiungere tra i corsi di studio seguiti quelli desiderati        [ ]
- Comando per rimuovere  tra i corsi di studio seguiti quelli desiderati        [ ]
    - Invio di un messaggio contenente il nuovo aggiornamento                   [ ]
- Comando per abilitare/disabilitare le notifiche                               [ ]
'''
#!/usr/bin/python3.6
import time
import json

import requests
import re

import telepot
from telepot.namedtuple import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

from settings import *

# Current state of the user
user_state = {}

# Function to handle incoming messages
def handle(msg):

    content_type, chat_type, chat_id = telepot.glance(msg)

    try:
        user_state[chat_id]
    except:
        user_state[chat_id] = 0

    # Not assuming that every message is a text
    if content_type == 'text':
        cmd_input = msg['text']
    else:
        bot.sendMessage(chat_id, "Il messaggio che hai inviato non è valido, ritenta.")

    # Attempting to save username and full name
    try:
        username  = msg['chat']['username']
        full_name = msg['chat']['first_name'] + ' ' + msg['chat']['last_name']
    except:
        username  = "Not defined"
        full_name = "Not defined"

    print("Msg from {}@{}{}[{}]: \t\"{}{}{}\"".format(color.BOLD, username, color.END, str(chat_id), color.ITALIC, cmd_input, color.END))

    if cmd_input == "/attempt_login" or cmd_input == "/attempt_login"+bot_name:
        print(color.CYAN + "Tentativo di connessione con |" + cred_get("username") + " - " + cred_get("password") + "|" + color.END)
        if (cred_get("username") != "YOUR_USERNAME" and cred_get("password") != "YOUR_PASSWORD"):
            # Tries to connect to the unistudium website
            payload = {
                "username": cred_get("username"),
                "password": cred_get("password")
            }

            r = requests.post(LOGIN_URL, data=payload)

            try:
                pattern = "<span class=\"usertext\">(.+?)</span>"
                name = re.findall(pattern, str(r.content))[0]
                print(color.CYAN + "Connessione instaurata con successo!" + color.END)
                bot.sendMessage(chat_id, "Sono riuscito a collegarmi, benvenuto *" + name + "!*", parse_mode = "Markdown")
            except:
                print(color.RED + "Credenziali errate" + color.END)
                bot.sendMessage(chat_id, "Login errato, ritenta sostituendo le credenziali nel file _cred.json_.", parse_mode = "Markdown")
        else:
            print(color.RED + "Credenziali non settate" + color.END)
            bot.sendMessage(chat_id, "Non hai inserito il tuo username e/o la tua password nel file _cred.json_. Modificali e riprova.", parse_mode = "Markdown")

    elif cmd_input == "/listen" or cmd_input == "/listen"+bot_name:
        bot.sendMessage(chat_id, "1) _Work in Progress..._", parse_mode = "Markdown")

    elif cmd_input == "/stop_listen" or cmd_input == "/stop_listen"+bot_name:
        bot.sendMessage(chat_id, "2) _Work in Progress..._", parse_mode = "Markdown")

    elif basics_cmds_response(chat_id, cmd_input) == 0 and '/' in cmd_input:
        bot.sendMessage(chat_id, "Il comando inserito non è valido.")


# Managing callback query from callback buttons in inline keyboards
def on_callback_query(msg):
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')

    print('Callback Query:', query_id, from_id, query_data)
    bot.answerCallbackQuery(query_id, text='Got it, but this will not say anything more than this until my creator will program it.')

# Standard commands input, with texts imported from settings.py file
def basics_cmds_response(chat_id, cmd_input):

    if cmd_input == "/start" or cmd_input == "/start"+bot_name:
        bot.sendMessage(chat_id, start_msg, parse_mode = "Markdown")
        return 1

    elif cmd_input == "/help" or cmd_input == "/help"+bot_name:
        bot.sendMessage(chat_id, cmd_list, parse_mode = "Markdown")
        return 1

    elif cmd_input == "/info" or cmd_input == "/info"+bot_name:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [dict(text = 'Dona', url = 'https://placeholder.it'), dict(text = 'GitHub', url = 'https://github.com')]])
        bot.sendMessage(chat_id, info_msg,  parse_mode = "Markdown", reply_markup = keyboard)
        return 1

    else:
        return 0


def cred_get(field):
    data = json.load(open('cred.json'))
    return data[field]

# ----------------
# Start working...
# ----------------
bot = telepot.Bot(TOKEN)

updates = bot.getUpdates()
if updates:
    last_update_id = updates[-1]['update_id']
    bot.getUpdates(offset=last_update_id+1)

bot.message_loop({'chat': handle,
                  'callback_query': on_callback_query})

print(color.ITALIC + 'Da grandi poteri derivano grandi responsabilità...\n' + color.END)

while(1):
    time.sleep(10)
