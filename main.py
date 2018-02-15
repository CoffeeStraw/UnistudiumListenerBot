'''
UnistudiumListener - Telegram Bot
Author: Porchetta (clarantonio98@gmail.com)

TO DO:
- Commit iniziale contenente info e comandi base                                [V]
- Comando per effettuare un tentativo di connessione con le credenziali         [V]
- Comando per aggiungere tra i corsi di studio seguiti quelli desiderati        [V]
- Comando per rimuovere  tra i corsi di studio seguiti quelli desiderati        [V]
    - Invio di un messaggio contenente il nuovo aggiornamento                   [ ]
- Migliorare gestione liste (in courses_followed salva urls)                    [V]
- Migliorare invio lista files (max 4096 UTF8 characters)                       [ ]
'''
#!/usr/bin/python3.6
import os
import sys
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

current_session = requests.Session()

# Function to handle incoming messages
def handle(msg):

    content_type, chat_type, chat_id = telepot.glance(msg)

    try:    user_state[chat_id]
    except: user_state[chat_id] = 0

    # Not assuming that every message is a text
    if content_type == 'text':
        cmd_input = msg['text']
    else:
        bot.sendMessage(chat_id, "Il messaggio che hai inviato non è valido, ritenta")

    # Attempting to save username and full name
    try:
        username  = msg['chat']['username']
        full_name = msg['chat']['first_name'] + ' ' + msg['chat']['last_name']
    except:
        username  = "Not defined"
        full_name = "Not defined"

    # Prints msg from the user
    print("Msg from {}@{}{}[{}]: \t\"{}{}{}\"".format(color.BOLD, username, color.END, str(chat_id), color.ITALIC, cmd_input, color.END))

    if basics_cmds_response(chat_id, cmd_input) != 0:
        pass
    ############################################################################
    elif cmd_input == "/attempt_login" or cmd_input == "/attempt_login"+bot_name:
        print(color.CYAN + "[CONNECTION] Tentativo di connessione con |" + cred_get("username") + " - ********|" + color.END)

        rec_response = reconnect(chat_id)
        if rec_response == 1:
            main_page = current_session.get(MAIN_URL)

            pattern = "<span class=\"usertext\">(.+?)</span>"
            name = re.findall(pattern, str(main_page.content))[0]

            bot.sendMessage(chat_id, "Sono riuscito a collegarmi, benvenuto *" + name + "*!", parse_mode = "Markdown")
        elif rec_response == 2:
            bot.sendMessage(chat_id, "Sei già connesso al portale", parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
        else:
            bot.sendMessage(chat_id, "*Errore* in fase di *login*, ritenta sostituendo le credenziali nel file _cred.json_", parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
    ############################################################################
    elif cmd_input == "/listen" or cmd_input == "/listen"+bot_name:
        if not os.path.isfile(coursesFile):
            if reconnect(chat_id):
                dl_courses_list(coursesFile)

        # List courses
        keyboard_courses = []
        for course_x in getlist_fromfile(coursesFile):
            keyboard_courses.append([ course_x[0] ])

        markup = ReplyKeyboardMarkup(keyboard=keyboard_courses)
        bot.sendMessage(chat_id, "Seleziona il corso che vuoi che ascolti per te", parse_mode = "Markdown", reply_markup = markup)
        user_state[chat_id] = 1

    elif user_state[chat_id] == 1:
        for course_x in getlist_fromfile(coursesFile):
            if cmd_input == course_x[0]:
                if not os.path.isfile(coursesFollowedFile):
                    writelist_infile(coursesFollowedFile, [course_x])
                    print(color.CYAN + "[FILE CREATE] Aggiunto file courses_followed.txt" + color.END)
                    bot.sendMessage(chat_id, "🔔 Da ora in poi riceverai le notifiche di:\n\n*" + cmd_input + "*", parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
                else:
                    courses_followed = getlist_fromfile(coursesFollowedFile)
                    for course_y in courses_followed:
                        if course_x[0] != course_y[0]:
                            courses_followed.append(course_x)
                            writelist_infile(coursesFollowedFile, courses_followed)

                            bot.sendMessage(chat_id, "🔔 Da ora in poi riceverai le notifiche di:\n\n*" + cmd_input + "*", parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
                            break
                    else:
                        bot.sendMessage(chat_id, "Stai già seguendo il corso scelto.\n\nPuoi smettere di seguirlo con il comando /stop_listen", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))

                user_state[chat_id] = 0
                break
        else:
            bot.sendMessage(chat_id, "Il corso scritto non è presente tra quelli trovati, riprova")
    ############################################################################
    elif cmd_input == "/stop_listen" or cmd_input == "/stop_listen"+bot_name:
        if not os.path.isfile(coursesFollowedFile):
            bot.sendMessage(chat_id, "Attualmente non stai seguendo nessun corso, puoi cominciare a seguirne uno col comando /listen", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
        else:
            keyboard_courses = []
            for course_x in getlist_fromfile(coursesFollowedFile):
                keyboard_courses.append([ course_x[0] ])

            markup = ReplyKeyboardMarkup(keyboard=keyboard_courses)
            bot.sendMessage(chat_id, "Seleziona il corso che vuoi che smetta di ascoltare", parse_mode = "Markdown", reply_markup = markup)

            user_state[chat_id] = 2

    elif user_state[chat_id] == 2:
        courses_followed = getlist_fromfile(coursesFollowedFile)
        for course_x in courses_followed:
            if cmd_input == course_x[0]:
                courses_followed.remove(course_x)

                if courses_followed:
                    writelist_infile(coursesFollowedFile, courses_followed)
                else:
                    os.remove(coursesFollowedFile)
                    print(color.CYAN + "[FILE DELETE] Rimosso file courses_followed.txt" + color.END)

                bot.sendMessage(chat_id, "🔕 Da ora in poi non riceverai più notifiche da:\n\n*" + cmd_input + "*", parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
                user_state[chat_id] = 0
                break
        else:
            bot.sendMessage(chat_id, "Il corso scelto non è valido, scegline uno dalla tastiera.")
    ############################################################################
    elif cmd_input == "/viewfiles" or cmd_input == "/viewfiles"+bot_name:
        if not os.path.isfile(coursesFollowedFile):
            bot.sendMessage(chat_id, "Attualmente non stai seguendo nessun corso per cui io possa mostrarti i files.\n\nPuoi cominciare a seguirne uno col comando /listen", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
        else:
            keyboard_courses = []
            for course_x in getlist_fromfile(coursesFollowedFile):
                keyboard_courses.append([ course_x[0] ])

            markup = ReplyKeyboardMarkup(keyboard=keyboard_courses)
            bot.sendMessage(chat_id, "Seleziona il corso di cui vuoi vedere i files caricati", parse_mode = "Markdown", reply_markup = markup)
            user_state[chat_id] = 3

    elif user_state[chat_id] == 3:
        for course_x in getlist_fromfile(coursesFollowedFile):
            if cmd_input == course_x[0]:
                if reconnect(chat_id):
                    dl_fileslist_fromcourse(course_x[1])

                mex = ""
                filename = filesDir + get_course_ID(course_x[1]) + ".txt"
                for sec in getlist_fromfile(filename):
                    mex += "Nelle sezione *" + sec[0] + "*:\n"
                    for file_downloaded in sec[1]:
                        mex += type_to_sym[file_downloaded[0]] + " " + file_downloaded[1] + " (" + file_downloaded[2] + ")\n"
                    mex += "\n"

                try:
                    bot.sendMessage(chat_id, "Ecco tutti i file che ho trovato nel corso di *" + cmd_input + "*:\n\n" + mex, parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
                except telepot.exception.TelegramError:
                    bot.sendMessage(chat_id, "Il corso desiderato ha troppi files per cui non posso inviarteli tutti in questo messaggio", parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))

                user_state[chat_id] = 0
                break
        else:
            bot.sendMessage(chat_id, "Il corso scelto non è valido, scegline uno dalla tastiera")
    ############################################################################
    elif cmd_input.startswith("/"):
        bot.sendMessage(chat_id, "Il comando inserito non è valido\nProva ad usare /help per una lista dei comandi disponibili")

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
            [dict(text = 'Dona', url = 'https://google.it'),
             dict(text = 'GitHub', url = 'https://github.com/Porchetta/UnistudiumListenerBot')]
            ])
        bot.sendMessage(chat_id, info_msg,  parse_mode = "Markdown", reply_markup = keyboard)
        return 1

    else:
        return 0

# Tries to connect to the unistudium website, saving the cookie in the current_session
def reconnect(chat_id):
    bot.sendChatAction(chat_id, "typing")

    # Ping the server
    response = os.system("ping -c 1 www.unistudium.unipg.it > /dev/null")
    if response:
        if (cred_get("username") != "YOUR_USERNAME" and cred_get("password") != "YOUR_PASSWORD"):
            main_cont = str(current_session.get(MAIN_URL).content)
            if "loginpanel" in main_cont:
                payload = {
                    "username": cred_get("username"),
                    "password": cred_get("password")
                }

                # Obtaining cookie
                current_session.get(LOGIN_URL)
                # Trying login
                current_session.post(LOGIN_URL, data=payload)

                main_cont = str(current_session.get(MAIN_URL).content)

                if("loginpanel" in main_cont):
                    print(color.RED + "[CONNECTION] Credenziali errate" + color.END)
                else:
                    print(color.GREEN + "[CONNECTION] Connessione al portale UNISTUDIUM effettuata con successo" + color.END)
                    return 1
            else:
                print(color.YELLOW + "[CONNECTION] Connessione già instaurata" + color.END)
                return 2
        else:
            print(color.RED + "[CONNECTION] Credenziali non settate" + color.END)
            bot.sendMessage(chat_id, "Non hai inserito il tuo username e/o la tua password nel file _cred.json_. Modificali e riprova.", parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
    else:
        print(color.RED + "[CONNECTION] Server irraggiungibile" + color.END)
        bot.sendMessage(chat_id, "Non riesco a contattare il server, riprova più tardi", parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
    return 0

# Function to download courses from Unistudium if not present
def dl_courses_list(path):
    main_page = current_session.get(MAIN_URL)

    pattern = "<h3 class=\"coursename\">(.+?)</h3>"
    courses_html = re.findall(pattern, str(main_page.content))

    courses = []
    for course_html in courses_html:
        name_pattern = "<\w+.*?>(.+?)<\/a>"
        url_pattern  = "href=\"(.+?)\""
        courses.append([re.findall(name_pattern, course_html)[0], re.findall(url_pattern, course_html)[0]])

    writelist_infile(coursesFile, courses)
    print(color.CYAN + "[FILE CREATE] Aggiunto file courses_list.txt" + color.END)

def dl_fileslist_fromcourse(course_url):
    course_page = current_session.get(course_url)

    pattern = "<li id=\"section-[^0]\"(.+?)<\/ul><\/div><\/li>"
    sections = re.findall(pattern, str(course_page.content))

    files_list = []
    for i, section in enumerate(sections):
        pattern = "<h3 class=\"sectionname\">(.+?)</h3>"
        section_name = re.findall(pattern, str(section))[0]

        files_list.append([section_name, []])

        pattern = "<div class=\"activityinstance\">(.+?)<\/div>"
        files_html = re.findall(pattern, str(section))

        for file_html in files_html:
            pattern = "<a class=\"\" onclick=\".*\" href=\"(.+?)\""
            file_link = re.findall(pattern, str(file_html))[0]

            pattern = "<span class=\"instancename\">(.+?)</span>"
            file_name_and_type = re.findall(pattern, str(file_html))[0]

            pattern = "(.+?)<span class=\"accesshide \" >"
            file_name = re.findall(pattern, str(file_name_and_type))[0]
            file_name = bytes(file_name, encoding='ascii').decode('unicode-escape').encode('latin-1').decode('utf-8')

            pattern = "<span class=\"accesshide \" > (.+)"
            file_type = re.findall(pattern, str(file_name_and_type))[0]

            files_list[i][1].append([file_type, file_name, file_link])

    filename = filesDir + get_course_ID(course_url) + ".txt"
    if not os.path.isfile(filename):
        print(color.CYAN + "[FILE CREATE] Aggiunto file " + filename + color.END)
    writelist_infile(filename, files_list)

def get_course_ID(course_url):
    pattern = "id=(.+)"
    return re.findall(pattern, course_url)[0]

def getlist_fromfile(path):
    return pickle.load(open(path, 'rb'))

def writelist_infile(path, my_list):
    pickle.dump(my_list, open(path, 'wb'))

def cred_get(field):
    data = json.load(open('cred.json'))
    return data[field]

# ----------------
# Start working...
# ----------------
pid = str(os.getpid())

# Check if PID exist
if os.path.isfile(pidfile):
    print(("{}[EXIT] Il processo {} è ancora attivo (usa fg per riaprirlo){}").format(color.RED, pidfile, color.END))
    sys.exit()
else:
    f = open(pidfile, 'w')
    f.write(pid)

# Check if dlDir exists
if not os.path.exists(dlDir):
    os.makedirs(dlDir)
    print(color.DARKCYAN + "[FOLDER CREATE] Ho aggiunto la cartella /Download/" + color.END)

if not os.path.exists(filesDir):
    os.makedirs(filesDir)
    print(color.DARKCYAN + "[FOLDER CREATE] Ho aggiunto la cartella /Download/Files/" + color.END)

try:
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
finally:
    os.unlink(pidfile)
