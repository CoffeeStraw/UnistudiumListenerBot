'''
UnistudiumListener - Telegram Bot
Author: Porchetta (clarantonio98@gmail.com)

TO DO:
- Commit iniziale contenente info e comandi base                                [V]
- Comando per effettuare un tentativo di connessione con le credenziali         [V]
- Comando per aggiungere tra i corsi di studio seguiti quelli desiderati        [V]
- Comando per rimuovere  tra i corsi di studio seguiti quelli desiderati        [V]
- Migliorare gestione liste (in courses_followed salva urls)                    [V]
- Migliorare invio lista files (max 4096 UTF8 characters)                       [V]
- Invio di un messaggio contenente l'aggiornamento della lista dei files        [V]
- Creazione comando /settings                                                   [V]
    - Aggiunta opzione per il download automatico di TUTTI i files              [V]
    - Aggiunta opzione per il download automatico degli ultimi files aggiunti   [V]
    - Aggiunta opzione per la selezione della lingua (Italiano/English)         [V]
- Modificare comando /settings (migliore gestione del singolo utente)           [V]
- Ottenere News dall'apposita sezione presente in ogni corso                    [V]
- Creare funzione per lettura corretta di un testo utf-8                        [ ]
- Creare funzione per inserimento escape nella stringa per Markdown             [ ]
- Gestire eccezione urllib3.exceptions.ReadTimeoutError (connessione lenta)     [ ]
'''

#!/usr/bin/python3.
import os
import sys
import time
import json
import pickle
import gettext
from tqdm import tqdm

import requests
import re

import telepot
from telepot.namedtuple import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

from settings import *

# Current state of the user
user_state = {}

current_session = requests.Session()

def handle(msg):
    """
    Function to handle incoming messages
    """
    content_type, chat_type, chat_id = telepot.glance(msg)
    user_id  = msg['from']['id']
    reply_id = msg['message_id']

    if chat_id not in user_state:
        user_state[chat_id] = {}
    if user_id not in user_state[chat_id]:
        user_state[chat_id][user_id] = 0

    # Get user language from settings
    try:
        language = getlist_fromfile(configDir+str(chat_id)+".txt")[0]
    except FileNotFoundError:
        print(color.YELLOW + "[INFO] Nessun file di configurazione trovato per {}, uso quello di default".format(str(chat_id)) + color.END)
        language = def_config[0]

    if language == 0:
        lang_it.install()
    elif language == 1:
        lang_en.install()

    # Checking content_type of the msg
    if content_type == 'text':
        cmd_input = msg['text']

    elif content_type == 'new_chat_member':
        cmd_input = 'Aggiunta ad un gruppo'
        bot.sendMessage(chat_id, _('add_to_group_msg'), parse_mode = "Markdown")
        # Adds configuration file of this new chat to the folder
        if not os.path.isfile(configDir+str(chat_id)+".txt"):
            writelist_infile(configDir+str(chat_id)+".txt", def_config)
            print(color.DARKCYAN + "[FILE] Ho aggiunto il file /UserPref/ChatConfig/" + str(chat_id) + ".txt" + color.END)

    elif content_type == 'left_chat_member':
        cmd_input = 'Rimozione da un gruppo'
        # Remove configuration file
        if os.path.isfile(configDir+str(chat_id)+".txt"):
            os.remove(configDir+str(chat_id)+".txt")

    else: # The user has sent an image or something unexpected, the bot will not say anything
        cmd_input = ''

    # Attempting to save username and/or full name
    try:    username  = msg['from']['username']
    except: username  = "Not defined"

    try:    full_name = msg['from']['first_name'] + ' ' + msg['from']['last_name']
    except: full_name = "Not defined"

    if username == "Not defined":
        username = full_name

    # Prints msg from the user
    if chat_id != user_id:  print("Msg from {}@{}{}[{}][{}]: \"{}{}{}\"".format(color.BOLD, username.ljust(16), color.END, user_id, chat_id, color.ITALIC, cmd_input, color.END))
    else:                   print("Msg from {}@{}{}[{}]: \"{}{}{}\"".format(color.BOLD, username.ljust(16), color.END, user_id, color.ITALIC, cmd_input, color.END))

    ############################################################################
    if basics_cmds_response(chat_id, cmd_input) != 0:
        pass
    ############################################################################
    elif cmd_input == "/trylogin" or cmd_input == "/trylogin"+bot_name:
        print(color.CYAN + "[CONNECTION] Tentativo di connessione con |" + cred_get("username") + " - ********|" + color.END)

        rec_response = reconnect(report_to_user = True, chat_id = chat_id)
        if rec_response == 1:
            main_page = current_session.get(MAIN_URL)

            pattern = "<span class=\"usertext\">(.+?)</span>"
            name = re.findall(pattern, str(main_page.content))[0]

            bot.sendMessage(chat_id, _('connected_msg').format(name), reply_to_message_id = reply_id, parse_mode = "Markdown")
        elif rec_response == 2:
            bot.sendMessage(chat_id, _('already_connected_msg'), reply_to_message_id = reply_id, parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
    ############################################################################
    elif cmd_input == "/listen" or cmd_input == "/listen"+bot_name:
        reconnected = 1

        if not os.path.isfile(coursesFullDir + str(chat_id) + ".txt"):
            reconnected = reconnect(report_to_user = True, chat_id = chat_id)
            if reconnected:
                dl_courseslist(coursesFullDir + str(chat_id) + ".txt")

        if reconnected:
            # List courses
            keyboard_courses = []
            for course_x in getlist_fromfile(coursesFullDir + str(chat_id) + ".txt"):
                if os.path.isfile(coursesFollowedDir + str(chat_id) + ".txt"):
                    if course_x not in getlist_fromfile(coursesFollowedDir + str(chat_id) + ".txt"):
                        keyboard_courses.append([ course_x[0] ])
                else:
                    keyboard_courses.append([ course_x[0] ])

            markup = ReplyKeyboardMarkup(keyboard=keyboard_courses, selective=True)
            bot.sendMessage(chat_id, _('choose_course_add_msg'), reply_to_message_id = reply_id, parse_mode = "Markdown", reply_markup = markup)['message_id']
            user_state[chat_id][user_id] = 1

    elif user_state[chat_id][user_id] == 1:
        for course_x in getlist_fromfile(coursesFullDir + str(chat_id) + ".txt"):
            if cmd_input == course_x[0]:
                # If we don't have yet a file list with all the courses followed
                if not os.path.isfile(coursesFollowedDir + str(chat_id) + ".txt"):
                    dl_fileslist_fromcourse(course_x[1])

                    writelist_infile(coursesFollowedDir + str(chat_id) + ".txt", [course_x])
                    print(color.CYAN + "[FILE] Aggiunto file courses_followed.txt" + color.END)
                    bot.sendMessage(chat_id, _('notification_course_on_msg').format(cmd_input), reply_to_message_id = reply_id, parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
                else:
                    courses_followed = getlist_fromfile(coursesFollowedDir + str(chat_id) + ".txt")
                    for course_y in courses_followed:
                        if course_x[0] != course_y[0]:
                            dl_fileslist_fromcourse(course_x[1])

                            courses_followed.append(course_x)
                            writelist_infile(coursesFollowedDir + str(chat_id) + ".txt", courses_followed)

                            bot.sendMessage(chat_id, _('notification_course_on_msg').format(cmd_input), reply_to_message_id = reply_id, parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
                            break
                    else:
                        bot.sendMessage(chat_id, _('err_already_following_msg'), reply_to_message_id = reply_id, reply_markup = ReplyKeyboardRemove(remove_keyboard = True))

                user_state[chat_id][user_id] = 0
                break
        else:
            bot.sendMessage(chat_id, _('err_course_not_found'), reply_to_message_id = reply_id,)
    ############################################################################
    elif cmd_input == "/stoplisten" or cmd_input == "/stoplisten"+bot_name:
        if not os.path.isfile(coursesFollowedDir + str(chat_id) + ".txt"):
            bot.sendMessage(chat_id, _('err_not_following_any_course_msg'), reply_to_message_id = reply_id, reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
        else:
            keyboard_courses = []
            for course_x in getlist_fromfile(coursesFollowedDir + str(chat_id) + ".txt"):
                keyboard_courses.append([ course_x[0] ])

            markup = ReplyKeyboardMarkup(keyboard=keyboard_courses, selective=True)
            bot.sendMessage(chat_id, _('choose_course_rem_msg'), reply_to_message_id = reply_id, parse_mode = "Markdown", reply_markup = markup)

            user_state[chat_id][user_id] = 11

    elif user_state[chat_id][user_id] == 11:
        courses_followed = getlist_fromfile(coursesFollowedDir + str(chat_id) + ".txt")
        for course_x in courses_followed:
            if cmd_input == course_x[0]:
                os.remove(fileslistDir + get_course_ID(course_x[1]) + ".txt")
                print(color.CYAN + "[FILE] Rimosso file /Download/FilesList/" + get_course_ID(course_x[1]) + ".txt" + color.END)

                courses_followed.remove(course_x)
                # If the list isn't still empty
                if courses_followed:
                    writelist_infile(coursesFollowedDir + str(chat_id) + ".txt", courses_followed)
                else:
                    os.remove(coursesFollowedDir + str(chat_id) + ".txt")
                    print(color.CYAN + "[FILE] Rimosso file courses_followed.txt" + color.END)

                bot.sendMessage(chat_id, _('notification_course_off_msg').format(cmd_input), reply_to_message_id = reply_id, parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
                user_state[chat_id][user_id] = 0
                break
        else:
            bot.sendMessage(chat_id, _('err_course_not_found'))
    ############################################################################
    elif cmd_input == "/viewfiles" or cmd_input == "/viewfiles"+bot_name:
        if not os.path.isfile(coursesFollowedDir + str(chat_id) + ".txt"):
            bot.sendMessage(chat_id, _('err_viewfiles_msg'), reply_to_message_id = reply_id, reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
        else:
            keyboard_courses = []
            for course_x in getlist_fromfile(coursesFollowedDir + str(chat_id) + ".txt"):
                keyboard_courses.append([ course_x[0] ])

            markup = ReplyKeyboardMarkup(keyboard=keyboard_courses, selective=True)
            bot.sendMessage(chat_id, _('choose_course_view_msg'), reply_to_message_id = reply_id, parse_mode = "Markdown", reply_markup = markup)
            user_state[chat_id][user_id] = 21

    elif user_state[chat_id][user_id] == 21:
        for course_x in getlist_fromfile(coursesFollowedDir + str(chat_id) + ".txt"):
            if cmd_input == course_x[0]:
                if reconnect(report_to_user = True, chat_id = chat_id):
                    dl_fileslist_fromcourse(course_x[1])

                custom_mex = _('course_filelist_head_msg').format(cmd_input) + "\n\n"
                filename = fileslistDir + get_course_ID(course_x[1]) + ".txt"
                mexs = get_formatted_fileslist(custom_mex, getlist_fromfile(filename))

                for mex in mexs:
                    bot.sendMessage(chat_id, mex, parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))

                user_state[chat_id][user_id] = 0
                break
        else:
            bot.sendMessage(chat_id, _('err_course_not_found'), reply_to_message_id = reply_id)
    ############################################################################
    elif cmd_input == "/viewnews" or cmd_input == "/viewnews"+bot_name:
        if not os.path.isfile(coursesFollowedDir + str(chat_id) + ".txt"):
            bot.sendMessage(chat_id, _('err_viewfiles_msg'), reply_to_message_id = reply_id, reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
        else:
            keyboard_courses = []
            for course_x in getlist_fromfile(coursesFollowedDir + str(chat_id) + ".txt"):
                keyboard_courses.append([ course_x[0] ])

            markup = ReplyKeyboardMarkup(keyboard=keyboard_courses, selective=True)
            bot.sendMessage(chat_id, _('Seleziona il corso di cui vuoi vedere le news'), reply_to_message_id = reply_id, parse_mode = "Markdown", reply_markup = markup)
            user_state[chat_id][user_id] = 31

    elif user_state[chat_id][user_id] == 31:
        for course_x in getlist_fromfile(coursesFollowedDir + str(chat_id) + ".txt"):
            if cmd_input == course_x[0]:
                if reconnect(report_to_user = True, chat_id = chat_id):
                    course_news = dl_forum_news(get_course_ID(course_x[1]), course_x[2])

                    if course_news:
                        keyboard_news = []
                        for new_news in course_news:
                            keyboard_news.append([ new_news[0] + " (" + new_news[1] + ")" ])

                        markup = ReplyKeyboardMarkup(keyboard=keyboard_news, selective=True)
                        bot.sendMessage(chat_id, _('Seleziona la news di cui vuoi vedere il contenuto'), reply_to_message_id = reply_id, reply_markup = markup)

                        user_state[chat_id][user_id] = 32
                    else:
                        bot.sendMessage(chat_id, "Non è stata trovata nessuna notizia nella materia scelta", reply_to_message_id = reply_id, parse_mode = "Markdown")
                        user_state[chat_id][user_id] = 0
                break
        else:
            bot.sendMessage(chat_id, _('err_course_not_found'), reply_to_message_id = reply_id)

    elif user_state[chat_id][user_id] == 32:
        try:
            pattern = "\((.+?)\)"
            link_url = re.findall(pattern, cmd_input)[0]
        except IndexError:
            link_url = "Error"

        if link_url != "Error":
            bot.sendMessage(admin_chat_id, get_news_msg(link_url), parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
            user_state[chat_id][user_id] = 0
        else:
            bot.sendMessage(chat_id, _('La news indicata non esiste, riprova'), reply_to_message_id = reply_id)
    ############################################################################
    elif cmd_input == "/settings" or cmd_input == "/settings"+bot_name:
        # Creates a new config file if it doesn't exist
        if not os.path.isfile(configDir+str(chat_id)+".txt"):
            writelist_infile(configDir+str(chat_id)+".txt", def_config)
            print(color.DARKCYAN + "[FILE] Ho aggiunto il file /UserPref/ChatConfig/" + str(chat_id) + ".txt" + color.END)

        settings_options = [
            _('set_opt_1'),
            _('set_opt_2'),
            _('set_opt_3')
        ]

        keyboard = []
        for opt in settings_options:
            keyboard.append([ opt ])

        markup = ReplyKeyboardMarkup(keyboard=keyboard, selective=True)
        bot.sendMessage(chat_id, _('settings_initial_msg'), reply_to_message_id = reply_id, reply_markup = markup)
        user_state[chat_id][user_id] = 41

    elif user_state[chat_id][user_id] == 41:
        settings_options = [
            _('set_opt_1'),
            _('set_opt_2'),
            _('set_opt_3')
        ]

        if cmd_input == settings_options[0]:
            config = getlist_fromfile(configDir+str(chat_id)+".txt")

            lang_options = [
                "Italiano",
                "English"
            ]

            lang_list = lang_options[:]
            del lang_list[config[0]]

            keyboard = []
            for opt in lang_list:
                keyboard.append([ opt ])

            markup = ReplyKeyboardMarkup(keyboard=keyboard, selective=True)
            bot.sendMessage(chat_id, _('choose_lang_msg'), reply_to_message_id = reply_id, parse_mode = "Markdown", reply_markup = markup)
            user_state[chat_id][user_id] = 42

        elif cmd_input == settings_options[1]:
            config = getlist_fromfile(configDir+str(chat_id)+".txt")

            notification_options = [
                _('set_disable'),
                _('set_enable')
            ]

            noti_list = notification_options[:]
            del noti_list[config[1]]

            keyboard = []
            for opt in noti_list:
                keyboard.append([ opt ])

            markup = ReplyKeyboardMarkup(keyboard=keyboard, selective=True)
            bot.sendMessage(chat_id, _('choose_noti_msg'), reply_to_message_id = reply_id, parse_mode = "Markdown", reply_markup = markup)
            user_state[chat_id][user_id] = 43

        elif cmd_input == settings_options[2]:
            config = getlist_fromfile(configDir+str(chat_id)+".txt")

            dl_options = [
                _('set_disable'),
                _('set_enable1'),
                _('set_enable2')
            ]

            dl_list = dl_options[:]
            del dl_list[config[2]]

            keyboard = []
            for opt in dl_list:
                keyboard.append([ opt ])

            markup = ReplyKeyboardMarkup(keyboard=keyboard, selective=True)
            bot.sendMessage(chat_id, _('choose_dl_msg'), reply_to_message_id = reply_id, parse_mode = "Markdown", reply_markup = markup)
            user_state[chat_id][user_id] = 44

        else:
            bot.sendMessage(chat_id, _('err_settings_msg'), reply_to_message_id = reply_id)

    elif user_state[chat_id][user_id] == 42:
        lang_options = [
            "Italiano",
            "English"
        ]

        if cmd_input in lang_options:
            # Updating language
            language = lang_options.index(cmd_input)
            update_config('lang', language, chat_id)

            if language == 0:
                lang_it.install()
            elif language == 1:
                lang_en.install()

            bot.sendMessage(chat_id, _('lang_set_msg'), reply_to_message_id = reply_id, parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
            user_state[chat_id][user_id] = 0
        else:
            bot.sendMessage(chat_id, _('err_settings_set_msg'), reply_to_message_id = reply_id,)

    elif user_state[chat_id][user_id] == 43:
        notification_options = [
            _('set_disable'),
            _('set_enable')
        ]

        if cmd_input in notification_options:
            update_config('noti', notification_options.index(cmd_input), chat_id)
            bot.sendMessage(chat_id, _('noti_set_msg'), reply_to_message_id = reply_id, parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
            user_state[chat_id][user_id] = 0
        else:
            bot.sendMessage(chat_id, _('err_settings_set_msg'), reply_to_message_id = reply_id)

    elif user_state[chat_id][user_id] == 44:
        dl_options = [
            _('set_disable'),
            _('set_enable1'),
            _('set_enable2')
        ]

        if cmd_input in dl_options:
            update_config('dl', dl_options.index(cmd_input), chat_id)
            bot.sendMessage(chat_id, _('dl_set_msg'), reply_to_message_id = reply_id, parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
            user_state[chat_id][user_id] = 0
        else:
            bot.sendMessage(chat_id, _('err_settings_set_msg'), reply_to_message_id = reply_id,)

    ############################################################################
    elif cmd_input.startswith("/") and chat_id == user_id:
        bot.sendMessage(chat_id, _('cmd_input_err_msg'), reply_to_message_id = reply_id)

def on_callback_query(msg):
    """
    Function to manage callback query from callback buttons in inline keyboards
    """
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')

    print('Callback Query:', query_id, from_id, query_data)

    if query_data == 'donate':
        bot.answerCallbackQuery(query_id, text = _('donate_msg'))
    else:
        bot.answerCallbackQuery(query_id, text='Gotcha, but this will not say anything more than this until my creator will program it.')

def basics_cmds_response(chat_id, cmd_input):
    """
    Managing standard commands input, with texts imported from settings.py file
    """
    if cmd_input == "/start" or cmd_input == "/start"+bot_name:
        # Set an initial config file for the chat
        if not os.path.isfile(configDir+str(chat_id)+".txt"):
            writelist_infile(configDir+str(chat_id)+".txt", def_config)
            print(color.DARKCYAN + "[FILE] Ho aggiunto il file /UserPref/ChatConfig/" + str(chat_id) + ".txt" + color.END)

        bot.sendMessage(chat_id, _('start_msg'), parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
        return 1

    elif cmd_input == "/help" or cmd_input == "/help"+bot_name:
        bot.sendMessage(chat_id, _('help_msg'), parse_mode = "Markdown")
        return 1

    elif cmd_input == "/info" or cmd_input == "/info"+bot_name:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [dict(text = _('donate_inline'), callback_data = 'donate'),
             dict(text = 'GitHub', url = 'https://github.com/Porchetta/UnistudiumListenerBot')]
            ])
        bot.sendMessage(chat_id, _('info_msg'),  parse_mode = "Markdown", reply_markup = keyboard)
        return 1

    else:
        return 0

def update():
    """
    Checks after tot time if there is any update for the courses choosen
    """

    # First I get all courses from various courses_followed files, so that I can
    # check just one time the course for all the users
    if not os.listdir(configDir):
        print(color.YELLOW + "Nessun file di configurazione rilevato, eseguire /start in chat con il bot" + color.END)
    else:
        all_courses_followed = []
        for courses_followed_file in os.listdir(coursesFollowedDir):
            for course in getlist_fromfile(coursesFollowedDir + courses_followed_file):
                if course not in all_courses_followed:
                    all_courses_followed.append(course)

        if reconnect(report_to_user = False):
            print(color.CYAN + "Controllo per nuovi updates..." + color.END)
            for course in all_courses_followed:
                if not os.path.isfile(fileslistDir + get_course_ID(course[1]) + ".txt"):
                    # If we don't have a files list yet, we just download it for the next check
                    dl_fileslist_fromcourse(course[1])
                else:
                    #If we have a file, we download the new version and we try to find all the diffs
                    dl_fileslist_fromcourse(course[1], "temp.txt")

                    old_file_path = fileslistDir + get_course_ID(course[1]) + ".txt"
                    new_file_path = fileslistDir + "temp.txt"

                    old_file = getlist_fromfile(old_file_path)
                    new_file = getlist_fromfile(new_file_path)

                    def find_diff(first_list, second_list):
                        diffs = []
                        for first_sec in first_list:
                            for second_sec in second_list:
                                if first_sec[0] == second_sec[0]:
                                    file_diffs = []
                                    for file2 in first_sec[1]:
                                        for file1 in second_sec[1]:
                                            if file2 == file1:
                                                break
                                        else:
                                            file_diffs.append(file2)
                                    if file_diffs:
                                        diffs.append([first_sec[0], file_diffs])
                                    break
                            else:
                                diffs.append(first_sec)
                        return diffs

                    additions = find_diff(new_file, old_file)
                    removes   = find_diff(old_file, new_file)

                    # Checks if we have some forum news Updates
                    new_newslist_path = newslistDir + get_course_ID(course[1]) + ".txt"

                    news_add  = []
                    if not os.path.isfile(new_newslist_path):
                        dl_forum_news(get_course_ID(course[1]), course[2])
                    else:
                        old_file = getlist_fromfile(new_newslist_path)

                        if old_file:
                            new_file = dl_forum_news(get_course_ID(course[1]), course[2], "temp.txt")

                            # Checks diff between the two lists
                            for new_news in new_file:
                                for old_news in old_file:
                                    if new_news == old_news:
                                        break
                                else:
                                    news_add.append( new_news[1] )

                    if additions or removes or news_add:
                        print(color.GREEN + "Ho trovato nuovi updates nel corso di " + course[0] + color.END)

                        # Getting all chat_ids of the users that want to receive the notification
                        chat_ids = []
                        for config_file in os.listdir(configDir):
                            config = getlist_fromfile(configDir + config_file)
                            chat_id = config_file.replace(".txt", "")
                            courses_followed_filename = coursesFollowedDir + str(chat_id) + ".txt"
                            if config[1] == 1 and os.path.isfile(courses_followed_filename):
                                for course_fol in getlist_fromfile(courses_followed_filename):
                                    if course == course_fol:
                                        chat_ids.append(chat_id)
                                        break

                        for config_file in os.listdir(configDir):
                            config = getlist_fromfile(configDir + config_file)
                            chat_id = config_file.replace(".txt", "")

                            # Get user language from settings
                            if config[0] == 0:
                                lang_it.install()
                            elif config[0] == 1:
                                lang_en.install()

                            # If there is at least one user that has requested to download the files
                            if config[2] >= 1 and chat_id in chat_ids:
                                files_course_path = filesDir + course[0].replace("/", "-") + "/"
                                if not os.path.exists(files_course_path):
                                    os.makedirs(files_course_path)
                                    print(color.DARKCYAN + "[FOLDER] Ho aggiunto la cartella /Download/Files/" + course[0] + "/" + color.END)

                                if removes:
                                    for sec in removes:
                                        for deleted_file in sec[1]:
                                            for file_dl in os.listdir(files_course_path):
                                                if file_dl.split(".")[0] == deleted_file[1]:
                                                    os.remove(files_course_path + file_dl)
                                                    break
                                            else: #Error
                                                print(color.CYAN + "[ERROR] Ho provato a rimuovere {}, ma non l'ho trovato...".format(deleted_file[1]) + color.END)

                                if additions:
                                    for sec in additions:
                                        for file_added in sec[1]:
                                            # If the file is already in the directory, we don't download it
                                            # because if it is an updated file it will be first removed by
                                            # precedent for
                                            for file_dl in os.listdir(files_course_path):
                                                if file_dl.split(".")[0] == file_added[1]:
                                                    break
                                            else:
                                                dl_file(files_course_path, file_added)

                                break

                        os.remove(old_file_path)
                        os.rename(new_file_path, old_file_path)

                        os.remove(new_newslist_path)
                        os.rename(newslistDir + "temp.txt", new_newslist_path)

                        if additions and removes:
                            custom_mex = _('new_upd_msg').format(course[0]) + "\n\n" + _('new_upd_add_msg')
                            mexs = get_formatted_fileslist(custom_mex, additions)

                            for chat_id in chat_ids:
                                for mex in mexs:
                                    bot.sendMessage(chat_id, mex, parse_mode = "Markdown")

                            custom_mex = _('new_upd_rem_msg')
                            mexs = get_formatted_fileslist(custom_mex, removes)

                            for chat_id in chat_ids:
                                for mex in mexs:
                                    bot.sendMessage(chat_id, mex, parse_mode = "Markdown")

                        elif additions:
                            custom_mex = _('new_upd_msg').format(course[0]) + "\n\n" + _('new_upd_add_msg') + "\n"
                            mexs = get_formatted_fileslist(custom_mex, additions)

                            for chat_id in chat_ids:
                                for mex in mexs:
                                    bot.sendMessage(chat_id, mex, parse_mode = "Markdown")

                        elif removes:
                            custom_mex = _('new_upd_msg').format(course[0]) + "\n\n" + _('new_upd_rem_msg') + "\n"
                            mexs = get_formatted_fileslist(custom_mex, removes)

                            for chat_id in chat_ids:
                                for mex in mexs:
                                    bot.sendMessage(chat_id, mex, parse_mode = "Markdown")

                        if news_add:
                            custom_mex = _('new_upd_news_msg').format(course[0]) + "\n\n"
                            for chat_id in chat_ids:
                                for url_news in news_add:
                                    bot.sendMessage(chat_id, custom_mex + get_news_msg(url_news), parse_mode = "Markdown")
                    else:
                        os.remove(new_file_path)
                        print(color.YELLOW + "Nessun update trovato per \"{b}{s}{e}\",\nnuovo tentativo in {b}{f:.2f}{e} min...".format(b = color.BOLD, s=course[0], e = color.END + color.YELLOW, f=update_time/60) + color.END)

    time.sleep(update_time)

def reconnect(report_to_user, chat_id = 0):
    """
    Tries to connect to the unistudium website, saving the cookie in current_session
    """
    if chat_id != 0:
        bot.sendChatAction(chat_id, "typing")

    # Ping the server
    if (cred_get("username") != "YOUR_USERNAME" and cred_get("password") != "YOUR_PASSWORD"):
        if requests.head(LOGIN_URL).status_code == 200:
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

                if "loginpanel" in main_cont:
                    print(color.RED + "[CONNECTION] Credenziali errate" + color.END)
                else:
                    print(color.GREEN + "[CONNECTION] Connessione al portale UNISTUDIUM effettuata con successo" + color.END)
                    return 1
            else:
                print(color.YELLOW + "[CONNECTION] Connessione già instaurata" + color.END)
                return 2
        else:
            print(color.RED + "[CONNECTION] Server irraggiungibile" + color.END)
            if report_to_user == True:
                bot.sendMessage(chat_id, _('err_server_unavailable_msg'), parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
    else:
        print(color.RED + "[CONNECTION] Credenziali non settate" + color.END)
        if report_to_user == True:
            bot.sendMessage(chat_id, _('err_login_msg'), parse_mode = "Markdown", reply_markup = ReplyKeyboardRemove(remove_keyboard = True))
    return 0

def dl_courseslist(path):
    """
    Function to download courses from Unistudium if not present
    """
    main_page = current_session.get(MAIN_URL)

    pattern = "<h3 class=\"coursename\">(.+?)</h3>"
    courses_html = re.findall(pattern, str(main_page.content))

    courses = []
    for course_html in courses_html:
        name_pattern = "<\w+.*?>(.+?)<\/a>"
        url_pattern  = "href=\"(.+?)\""

        name      = re.findall(name_pattern, course_html)[0]
        url       = re.findall(url_pattern, course_html)[0]
        forum_url = get_forum_url(url)

        courses.append([name, url, forum_url])

    writelist_infile(path, courses)
    print(color.CYAN + "[FILE] Aggiunto file " + path + color.END)

def dl_fileslist_fromcourse(course_url, custom_name = ""):
    """
    Downloads files list from the course given
    """
    course_page = current_session.get(course_url)

    pattern = "<li id=\"section-[0-9]+\"(.+?)<\/ul><\/div><\/li>"
    sections = re.findall(pattern, str(course_page.content))

    files_list = []
    for i, section in enumerate(sections):
        pattern = "<h3 class=\"sectionname\">(.+?)</h3>"
        try:               section_name = re.findall(pattern, str(section))[0]
        except IndexError: section_name = "Introduzione"

        files_list.append([section_name, []])

        pattern = "<div class=\"activityinstance\">(.+?)<\/div>"
        files_html = re.findall(pattern, str(section))

        for file_html in files_html:
            try:
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
            except IndexError:
                pass

    filename = get_course_ID(course_url) + ".txt"
    if custom_name != "":
        filename = custom_name

    if not os.path.isfile(fileslistDir + filename):
        if custom_name != "temp.txt":
            print(color.CYAN + "[FILE] Aggiunto file Download/FilesList/"  + filename + color.END)
    else:
        print(color.CYAN + "[FILE] Ho sovrascritto il file Download/FilesList/" + filename + color.END)

    if files_list == []:
        print(color.RED + "[ERROR] Non sono riuscito a scrivere il file!" + color.END)

    writelist_infile(fileslistDir + filename, files_list)

def dl_file(files_course_path, my_file):
    """
    Downloads and saves the file specified into the directory files_course_path
    TO DO:
    - Generico: salvare la pagina in html                                       [V]
    - Se è una cartella, cerca tutti i file all'interno e scarica tutto         [ ]
    - Se è un URL, lo salva come collegamento (anche appelli)                   [ ]
    """
    response = current_session.get(my_file[2], stream=True)

    total_size = int(response.headers.get('content-length', 0));
    chunk_size = 32*1024

    # If we don't know the extension of the file from url, we just take it as html
    if len(response.url.split('/')[-1].split('.')) == 1 or response.url.split('/')[-1].split('.')[-1].startswith("php"):
        ext = "html"
    else:
        ext = response.url.split('/')[-1].split('.')[-1]

    if ext != "html":
        with open(files_course_path + my_file[1] + "." + ext, "wb") as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc="DL: "+my_file[1]) as pbar:
                for data in response.iter_content(chunk_size):
                    f.write(data)
                    pbar.update(len(data))
    else:
        print("DL: " + my_file[1] + " in corso...")

        pattern = "<section id=\"region-main\" class=\"span8 pull-right\">(.+?)</section>"
        file_html = re.findall(pattern, str(response.content))[0]

        with open(files_course_path + my_file[1] + "." + ext, "w") as f:
            f.write(bytes(file_html, encoding='ascii').decode('unicode-escape').encode('latin-1').decode('utf-8'))

def get_formatted_fileslist(custom_mex, my_list):
    """
    Returns a formatted message generated by the list given
    """
    i = 0
    mexs = [custom_mex]

    for sec in my_list:
        sec_string =  _('sec_msg').format(sec[0]) + "\n"
        if len(mexs[i] + sec_string) > 4096:
            i += 1
            mexs.append("")
        mexs[i] += sec_string

        for file_downloaded in sec[1]:
            if file_downloaded[0] not in type_to_sym:
                print(color.RED + "[ERROR] Risolvere eccezione simbolo: " + file_downloaded[0] + color.END)
                type_to_sym[file_downloaded[0]] = "⁉️"

            file_string = type_to_sym[file_downloaded[0]] + " [" + file_downloaded[1].replace("_", "\_") + "](" + file_downloaded[2] + ")\n"
            if len(mexs[i] + file_string) > 4096:
                i += 1
                mexs.append("")
            mexs[i] += file_string

        mexs[i] += "\n"

    return mexs

def get_forum_url(course_url_link):
    """
    Get the forum news url froum the course link
    """
    course_page = current_session.get(course_url_link)
    pattern = "<a class=\"\" onclick=\"\" href=\"(.+?)\"><img src"
    try: return re.findall(pattern, str(course_page.content))[0]
    except IndexError: "https://www.unistudium.unipg.it/unistudium/error/"

def dl_forum_news(course_id, forum_link_url, custom_name = ""):
    """
    Attempt to get a list of all the forum news from a course url and saves them to a file
    [ ["nome della news", "url"], [...] ]
    """
    course_page_content = current_session.get(forum_link_url).content
    try:
        pattern   = "<tr class=(.+?)<\/tr>"
        news_msg  = re.findall(pattern, str(course_page_content))

        news = []
        for new_news in news_msg:
            pattern = "<td class=\"topic starter\"><a href=\"(.+?)\">"
            url     = re.findall(pattern, new_news)[0]

            pattern = "<td class=\"topic starter\"><a href=\".+\">(.+?)</a>.+<td class=\"picture\">"
            name    = re.findall(pattern, new_news)[0].encode('ascii').decode('unicode-escape').encode('latin-1').decode('utf-8')

            news.append([name, url])

        if not custom_name:
            print(color.CYAN + "[FILE] Aggiunto file Download/NewsList/"  + str(course_id) + ".txt" + color.END)
            custom_name = str(course_id) + ".txt"

        writelist_infile(newslistDir + custom_name, news)

        return news

    except IndexError:
        return []

def get_news_msg(link_news):
    """
    Access to a news from url given and returns the content of the news
    """
    news_content = current_session.get(link_news).content

    pattern = "<div class=\"author\".+?</div>"
    head    = re.findall(pattern, str(news_content))[0]

    pattern = ">(.+?)<"
    head    = re.findall(pattern, head)

    author = head[1].title()
    date   = head[2].replace(" - ", "").encode('ascii').decode('unicode-escape').encode('latin-1').decode('utf-8').title()

    pattern  = "<div class=\"posting fullpost\".+?<p>(.+?)</p><div class=\"attachedimages\""
    news_msg = re.findall(pattern, str(news_content))[0].encode('ascii').decode('unicode-escape').encode('latin-1').decode('utf-8')

    news_msg = news_msg.replace("</p><p>", "\n").replace("<br />", "")

    final_mex = _('news_post_msg').format(author,date,news_msg)

    return final_mex

def update_config(param, val, chat_id):
    """
    Updates config file
    """
    filename = configDir + str(chat_id) + ".txt"
    upd_config = getlist_fromfile(filename)

    if   param == 'lang':
        upd_config[0] = val
    elif param == 'noti':
        upd_config[1] = val
    elif param == 'dl':
        upd_config[2] = val

    writelist_infile(filename, upd_config)

def get_course_ID(course_url):
    """
    Returns the ID of a given course
    """
    pattern = "id=(.+)"
    return re.findall(pattern, course_url)[0]

def getlist_fromfile(path):
    """
    Reads a list from a file and returns it
    """
    return pickle.load(open(path, 'rb'))

def writelist_infile(path, my_list):
    """
    Write a list to a file
    """
    pickle.dump(my_list, open(path, 'wb'))

def cred_get(field):
    """
    Read the credentials in the json file and returns the one specified in the field
    """
    data = json.load(open('cred.json'))
    return data[field]

# -----------------
# Starts working...
# -----------------
pid = str(os.getpid())

# Check if PID exist
if os.path.isfile(pidfile):
    print(("{}[EXIT] Il processo {} è ancora attivo (usa fg per riaprirlo){}").format(color.RED, pidfile, color.END))
    sys.exit()
else:
    f = open(pidfile, 'w')
    f.write(pid)

# Loading languages
lang_en = gettext.translation("messages", localedir="locales", languages=["en_US"], fallback=True)
lang_it = gettext.translation("messages", localedir="locales", languages=["it_IT"], fallback=True)

# Checks if all the dirs exist
if not os.path.exists(dlDir):
    os.makedirs(dlDir)
    print(color.DARKCYAN + "[FOLDER] Ho aggiunto la cartella /Download/" + color.END)

if not os.path.exists(fileslistDir):
    os.makedirs(fileslistDir)
    print(color.DARKCYAN + "[FOLDER] Ho aggiunto la cartella /Download/FilesList/" + color.END)

if not os.path.exists(newslistDir):
    os.makedirs(newslistDir)
    print(color.DARKCYAN + "[FOLDER] Ho aggiunto la cartella /Download/NewsList/" + color.END)

if not os.path.exists(filesDir):
    os.makedirs(filesDir)
    print(color.DARKCYAN + "[FOLDER] Ho aggiunto la cartella /Download/Files/" + color.END)

if not os.path.exists(userDir):
    os.makedirs(userDir)
    print(color.DARKCYAN + "[FOLDER] Ho aggiunto la cartella /UserPref/" + color.END)

if not os.path.exists(configDir):
    os.makedirs(configDir)
    print(color.DARKCYAN + "[FOLDER] Ho aggiunto la cartella /UserPref/ChatConfig/" + color.END)

if not os.path.exists(coursesFullDir):
    os.makedirs(coursesFullDir)
    print(color.DARKCYAN + "[FOLDER] Ho aggiunto la cartella /UserPref/CoursesFull/" + color.END)

if not os.path.exists(coursesFollowedDir):
    os.makedirs(coursesFollowedDir)
    print(color.DARKCYAN + "[FOLDER] Ho aggiunto la cartella /UserPref/CoursesFollowed/" + color.END)

try:
    bot = telepot.Bot(TOKEN)

    updates = bot.getUpdates()
    if updates:
        last_update_id = updates[-1]['update_id']
        bot.getUpdates(offset=last_update_id+1)

    bot.message_loop({'chat':           handle,
                      'callback_query': on_callback_query})

    print(color.ITALIC + 'Da grandi poteri derivano grandi responsabilità...\n' + color.END)

    while(1):
        update()
finally:
    os.unlink(pidfile)
