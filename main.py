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
import os
import time
import json
import pickle

import requests
import re

import telepot
from telepot.namedtuple import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

from settings import *

# Current state of the user
user_state = {}

r = requests.Session()

# Function to handle incoming messages
def handle(msg):

    content_type, chat_type, chat_id = telepot.glance(msg)

    try:    user_state[chat_id]
    except: user_state[chat_id] = 0

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

    if basics_cmds_response(chat_id, cmd_input) != 0:
        print("Ho eseguito un comando base")
    elif cmd_input == "/attempt_login" or cmd_input == "/attempt_login"+bot_name:
        print(color.CYAN + "Tentativo di connessione con |" + cred_get("username") + " - ******** |" + color.END)

        rec_response = reconnect(chat_id)
        if rec_response == 1:
            main_page = r.get(MAIN_URL)
            pattern = "<span class=\"usertext\">(.+?)</span>"
            name = re.findall(pattern, str(main_page.content))[0]
            bot.sendMessage(chat_id, "Sono riuscito a collegarmi, benvenuto *" + name + "!*", parse_mode = "Markdown")

        elif rec_response == 2:
            bot.sendMessage(chat_id, "Sei già connesso al portale.", parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))

        else:
            bot.sendMessage(chat_id, "*Errore* in fase di *login*, ritenta sostituendo le credenziali nel file _cred.json_.", parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))


    elif cmd_input == "/listen" or cmd_input == "/listen"+bot_name:
        courses_names = []
        if not os.path.isfile(fileDir + "full_courses.txt"):
            if reconnect(chat_id):
                print(color.CYAN + "Creo il file dei corsi partendo dalla lista su UNISTUDIUM." + color.END)
                main_page = r.get(MAIN_URL)

                pattern = "<h3 class=\"coursename\">(.+?)</h3>"
                courses_html = re.findall(pattern, str(main_page.content))

                courses = []
                for course_html in courses_html:
                    name_pattern = "<\w+.*?>(.+?)<\/a>"
                    url_pattern  = "href=\"(.+?)\""
                    courses.append([re.findall(name_pattern, course_html)[0], re.findall(url_pattern, course_html)[0]])

                with open(fileDir + "full_courses.txt", 'wb') as f:
                    pickle.dump(courses, f)

                for course in courses:
                    courses_names.append(course[0])
        else:
            print(color.CYAN + "Il file dei corsi è presente, non mi collego ad UNISTUDIUM." + color.END)
            courses_names = load_courses_names(fileDir + "full_courses.txt")

        # List courses
        keyboard_courses = []
        for i, course_name in enumerate(courses_names):
            keyboard_courses.append([])
            keyboard_courses[i].append(course_name)

        markup = ReplyKeyboardMarkup(keyboard=keyboard_courses)
        bot.sendMessage(chat_id, "Seleziona il corso che vuoi che ascolti per te", parse_mode = "Markdown", reply_markup = markup)
        user_state[chat_id] = 1

    elif user_state[chat_id] == 1:
        courses_names = load_courses_names(fileDir + "full_courses.txt")
        if cmd_input in courses_names:
            courses_followed = []
            if not os.path.isfile(fileDir + "courses_followed.txt"):
                print(color.CYAN + "Aggiungo il file dei corsi seguiti." + color.END)

                courses_followed.append(cmd_input)
                with open(fileDir + "courses_followed.txt", 'wb') as f:
                    pickle.dump(courses_followed, f)

                bot.sendMessage(chat_id, "🔔 Da ora in poi riceverai le notifiche di:\n\n*" + cmd_input + "* 🔔", parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
            else:
                print(color.CYAN + "Non ricreo il file dei corsi seguiti." + color.END)

                with open (fileDir + "courses_followed.txt", 'rb') as f:
                    courses_followed = pickle.load(f)

                if cmd_input not in courses_followed:
                    courses_followed.append(cmd_input)
                    with open(fileDir + "courses_followed.txt", 'wb') as f:
                        pickle.dump(courses_followed, f)

                    bot.sendMessage(chat_id, "🔔 Da ora in poi riceverai le notifiche di:\n\n*" + cmd_input + "* 🔔", parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
                else:
                    bot.sendMessage(chat_id, "Stai già seguendo il corso scelto.\n\nPuoi smettere di seguirlo con il comando /stop_listen", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))

            user_state[chat_id] = 0
        else:
            bot.sendMessage(chat_id, "Invia un corso valido utilizzando la tastiera creata.")

    elif cmd_input == "/stop_listen" or cmd_input == "/stop_listen"+bot_name:
        if not os.path.isfile(fileDir + "courses_followed.txt"):
            bot.sendMessage(chat_id, "Attualmente non stai seguendo nessun corso, puoi cominciare a seguirne uno col comando /listen", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
        else:
            courses_followed = load_courses_followed(fileDir + "courses_followed.txt")

            keyboard_courses = []
            for i, course_followed in enumerate(courses_followed):
                keyboard_courses.append([])
                keyboard_courses[i].append(course_followed)

            markup = ReplyKeyboardMarkup(keyboard=keyboard_courses)
            bot.sendMessage(chat_id, "Seleziona il corso che vuoi che smetta di ascoltare", parse_mode = "Markdown", reply_markup = markup)
            user_state[chat_id] = 2

    elif user_state[chat_id] == 2:
        courses_followed = load_courses_followed(fileDir + "courses_followed.txt")
        if cmd_input in courses_followed:
            courses_followed.remove(cmd_input)

            if courses_followed:
                with open(fileDir + "courses_followed.txt", 'wb') as f:
                    pickle.dump(courses_followed, f)
            else:
                os.remove(fileDir + "courses_followed.txt")

            bot.sendMessage(chat_id, "🔕 Da ora in poi non riceverai più notifiche da:\n\n*" + cmd_input + "* 🔕", parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
            user_state[chat_id] = 0
        else:
            bot.sendMessage(chat_id, "Il corso scelto non è valido, scegline uno dalla tastiera.")


    elif cmd_input.startswith("/"):
        bot.sendMessage(chat_id, "Il comando inserito non è valido.")

# Tries to connect to the unistudium website
def reconnect(chat_id):
    # Try to ping the server
    response = os.system("ping -c 1 www.unistudium.unipg.it > /dev/null")
    if response:
        if (cred_get("username") != "YOUR_USERNAME" and cred_get("password") != "YOUR_PASSWORD"):

            main_cont = str(r.get(MAIN_URL).content)
            if "loginpanel" in main_cont:
                payload = {
                    "username": cred_get("username"),
                    "password": cred_get("password")
                }

                # Obtaining cookie
                r.get(LOGIN_URL)
                # Trying login
                r.post(LOGIN_URL, data=payload)

                main_cont = str(r.get(MAIN_URL).content)

                if("loginpanel" in main_cont):
                    print(color.RED + "Credenziali errate" + color.END)
                else:
                    print(color.GREEN + "Connesso al portale UNISTUDIUM" + color.END)
                    return 1
            else:
                print(color.YELLOW + "Sei già connesso" + color.END)
                return 2
        else:
            print(color.RED + "Credenziali non settate" + color.END)
            bot.sendMessage(chat_id, "Non hai inserito il tuo username e/o la tua password nel file _cred.json_. Modificali e riprova.", parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
        return 0
    else:
        print(color.RED + "Server irraggiungibile" + color.END)
        bot.sendMessage(chat_id, "Non riesco a contattare il server, riprova più tardi", parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))

#fileDir + "full_courses.txt"
def load_courses_names(path):
    courses, courses_names = [], []
    with open (path, 'rb') as f:
        courses = pickle.load(f)

    for course in courses:
        courses_names.append(course[0])

    return courses_names

def load_courses_followed(path):
    courses_followed = []
    with open (path, 'rb') as f:
        courses_followed = pickle.load(f)

    return courses_followed

# Managing callback query from callback buttons in inline keyboards
def on_callback_query(msg):
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')

    print('Callback Query:', query_id, from_id, query_data)
    bot.answerCallbackQuery(query_id, text='Got it, but this will not say anything more than this until my creator will program it.')

# Standard commands input, with texts imported from settings.py file
def basics_cmds_response(chat_id, cmd_input):

    if cmd_input == "/start" or cmd_input == "/start"+bot_name:
        bot.sendMessage(chat_id, start_msg, parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
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
