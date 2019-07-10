#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UnistudiumListener - Telegram Bot
Author: CoffeeStraw
"""
import os
import re
import time
import requests
import threading

import logging
import colorama
from colorama import Fore, Style

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove,
                      InlineKeyboardButton, InlineKeyboardMarkup, ChatAction, ParseMode)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler, CallbackQueryHandler, PicklePersistence)

import unistudium_framework as uni
from settings import TOKEN, UPD_TIME, MAIN_URL

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Create PicklePersistence object
pp = PicklePersistence(filename='ul_data.pickle', on_flush=True)



def start(update, context):
    start_msg = "*Benvenuto a* @UnistudiumListenerBot.\n"\
        "Questo bot ti terrà aggiornato in tempo reale sui nuovi caricamenti effettuati dai docenti "\
        "nei rispettivi corsi presenti sulla piattaforma Unistudium.\n\n"\
        "_Il bot è da considerarsi non ufficiale, né KITLab né Unipg sono responsabili in alcun modo._"

    update.message.reply_markdown(start_msg)

    # We have a new user, add it to the pickle file
    pp.flush()

    return ConversationHandler.END


def help_list(update, context):
    help_msg = "Questa è una lista degli attuali *comandi* presenti nel bot:\n\n"\
        "- /cancel: Annulla un comando in esecuzione\n\n"\
        "- /info: Informazioni utili sul bot e sulla pagina ufficiale GitHub\n\n"\
        "- /login: Effettua il Login sul portale Unistudium chiedendo le credenziali\n\n"\
        "- /logout: Cancella ogni dato personale raccolto dal Bot, compresa la sessione corrente ed effettuando quindi il Logout dal portale\n\n"\
        "- /notifications: Permette di selezionare un corso e abilitare/disabilitare le sue notifiche\n\n"\
        "- /viewfiles: Permette di visualizzare una lista di tutti i files presenti in un determinato corso\n\n"\
        "- /viewnews: Permette di visualizzare una lista delle news presenti nella sezione \"Annunci\" di un corso e leggerne il contenuto"
    update.message.reply_markdown(help_msg)

    return ConversationHandler.END


def info(update, context):
    info_msg = "*UnistudiumListener* è il miglior metodo per tenerti sempre aggiornato sugli ultimi argomenti "\
               "caricati dai docenti su *Unistudium.*\nL'intero codice sorgente è totalmente open ed è "\
               "consultabile sulla pagina GitHub del creatore di questo bot.\n\n"
    keyboard = [[InlineKeyboardButton("GitHub", url='https://github.com/CoffeeStraw/UnistudiumListenerBot')]]
    update.message.reply_markdown(info_msg, reply_markup=InlineKeyboardMarkup(keyboard))

    return ConversationHandler.END


def login(update, context):
    """
    Command to perform a login on the Unistudium Portal
    """
    send_user_pwd = 'Inserisci il tuo *username* e la tua *password* nel seguente formato (con un solo spazio in mezzo):\n\n'\
                    'username password\n\n'\
                    '_Si ricorda che il bot cancellerà immediatamente il messaggio inviato non appena sarà stato effettuato il login, per questioni di Privacy._'

    update.message.reply_markdown(send_user_pwd)
    return 1


def login_1(update, context):
    # Save credentials
    context.user_data['credentials'] = {}

    # Getting username and password from message's text
    user_pass = update.message.text.split(' ')

    # Delete user message
    context.bot.delete_message(chat_id=update.effective_message.chat_id, message_id=update.message.message_id)

    if len(user_pass) == 2:
        context.user_data['credentials']['username'], context.user_data['credentials']['password'] = user_pass
    else:
        update.message.reply_markdown("Non hai *formattato correttamente* le tue credenziali, riprova.", reply_markup=ReplyKeyboardRemove())
        return 1

    # Send a message to the user to let him wait
    update.message.reply_text("Tentativo di connessione in corso, attendere...")
    context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)

    # Try login
    response = uni.reconnect(context.user_data)
    if response != "OK":
        update.message.reply_markdown(response, reply_markup=ReplyKeyboardRemove())
        return 1

    # Getting Name and Surname of the user just to show that login was performed correctly
    main_page = context.user_data['session'].get(MAIN_URL)

    pattern = "<span class=\"usertext\">(.+?)</span>"
    name = re.findall(pattern, str(main_page.content))[0]

    update.message.reply_markdown("Sono riuscito a collegarmi, benvenuto *%s*!" % name.title())
    
    # Update pickle file
    pp.flush()

    return ConversationHandler.END


def logout(update, context):
    """
    Remove all the user's data from the pickle file
    """
    # Delete all
    for key in list(context.user_data):  # Using a list to prevent RuntimeError, since user_data could change during iterations
        del context.user_data[key]

    # Update pickle file
    pp.flush()

    # Notification message
    update.message.reply_markdown("Tutti i dati che erano presenti (credenziali, corsi seguiti, preferenze) sono stati rimossi con successo.\n\n"\
                                  "_Questo comporta anche che non riceverai più alcuna notifica nel caso seguissi precedentemente qualche corso._")
    return ConversationHandler.END


def notifications(update, context):
    # If the user hasn't requested the list of the courses already, we get it using the unistudium framework
    response = uni.reconnect(context.user_data)
    if response != "OK":
        # Error
        update.message.reply_markdown(response, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    # Check if the list of the courses is available
    if 'courses' not in context.user_data:
        context.user_data['courses'] = uni.get_courseslist(context.user_data)

    # Send message with list of courses to the user
    choose_course_view_files = 'Seleziona il corso di cui vuoi abilitare/disabilitare notifiche'
    reply_keyboard = [["%s %s" % (context.user_data['courses'][course_name]['followed'], course_name)] for course_name in context.user_data['courses'].keys()]
    update.message.reply_text(choose_course_view_files, reply_markup=ReplyKeyboardMarkup(reply_keyboard))
    
    # Update pickle file
    pp.flush()
    
    return 1


def notifications_1(update, context):
    course_name = update.message.text[2:]

    # Check for course name validity
    try:
        if context.user_data['courses'][course_name]['followed'] == '🔕':
            context.user_data['courses'][course_name]['followed'] = '🔔'
            update.message.reply_markdown('Riprenderai a ricevere le notifiche dal corso di ' + course_name, reply_markup=ReplyKeyboardRemove())
        else:
            context.user_data['courses'][course_name]['followed'] = '🔕'
            update.message.reply_markdown('Non riceverai più notifiche dal corso di ' + course_name, reply_markup=ReplyKeyboardRemove())
    except KeyError:
        no_course = 'Non è presente un corso con quel nome, riprova.'
        update.message.reply_text(no_course)
        return 1

    return ConversationHandler.END


def viewfiles(update, context):
    """
    Request a list of files of a specific course in Unistudium
    """
    # If the user hasn't requested the list of the courses already, we get it using the unistudium framework
    response = uni.reconnect(context.user_data)
    if response != "OK":
        # Error
        update.message.reply_markdown(response, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    # Check if the list of the courses is available
    if 'courses' not in context.user_data:
        context.user_data['courses'] = uni.get_courseslist(context.user_data)

    # Send message with list of courses to the user
    choose_course_view_files = 'Seleziona il corso di cui vuoi vedere i files caricati'
    reply_keyboard = [["%s %s" % (context.user_data['courses'][course_name]['followed'], course_name)] for course_name in context.user_data['courses'].keys()]
    update.message.reply_text(choose_course_view_files, reply_markup=ReplyKeyboardMarkup(reply_keyboard))
    
    # Update pickle file
    pp.flush()
    
    return 1


def viewfiles_1(update, context):
    course_name = update.message.text[2:]

    # Check for course name validity
    try:
        course_urls = context.user_data['courses'][course_name]
    except KeyError:
        no_course = 'Non è presente un corso con quel nome, riprova.'
        update.message.reply_text(no_course)
        return 1

    # Get list of files from Unistudium website
    files_list = uni.get_course_fileslist(context.user_data, course_urls['url'])
    context.user_data['courses'][course_name]['fileslist'] = files_list
    
    # Format the fileslist
    custom_mex = 'Ecco tutti i file che ho trovato nel corso di *%s*:\n\n' % course_name
    mexs = uni.get_formatted_fileslist(files_list, custom_mex)

    # Send list of files to the user
    for mex in mexs:
        update.message.reply_markdown(mex, reply_markup=ReplyKeyboardRemove())

    # Save in the pickle file
    pp.flush()

    return ConversationHandler.END


def viewnews(update, context):
    """
    view news from unistudium
    """
    # If the user hasn't requested the list of the courses already, we get it using the unistudium framework
    response = uni.reconnect(context.user_data)
    if response != "OK":
        # Error
        update.message.reply_markdown(response, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    # Check if the list of the courses is available
    if 'courses' not in context.user_data:
        context.user_data['courses'] = uni.get_courseslist(context.user_data)

    # Send message with list of courses to the user
    choose_course_view_news = 'Seleziona il corso di cui vuoi vedere le news caricate'
    reply_keyboard = [["%s %s" % (context.user_data['courses'][course_name]['followed'], course_name)] for course_name in context.user_data['courses'].keys()]
    update.message.reply_text(choose_course_view_news, reply_markup=ReplyKeyboardMarkup(reply_keyboard))

    # Save in the pickle file
    pp.flush()

    return 1


def viewnews_1(update, context):
    course_name = update.message.text[2:]

    # Check for course name validity
    try:
        course_urls = context.user_data['courses'][course_name]
    except KeyError:
        no_course = 'Non è presente un corso con quel nome, riprova.'
        update.message.reply_text(no_course)
        return 1

    # Check news availability
    course_news = uni.get_forum_news(context.user_data, course_urls['forum_url'])
    context.user_data['courses'][course_name]['newslist'] = course_news
    if not course_news:
        no_news = 'Non è presente alcuna notizia nella pagina della materia scelta.'
        update.message.reply_text(no_news, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    # Save course selected for the next step
    context.user_data['course_selected'] = course_name

    # Send message to the user
    choose_news = 'Seleziona la news di cui vuoi vedere il contenuto'
    reply_keyboard = [[news_name] for news_name in course_news.keys()]
    update.message.reply_text(choose_news, reply_markup=ReplyKeyboardMarkup(reply_keyboard))

    # Save in the pickle file
    pp.flush()

    return 2


def viewnews_2(update, context):
    news_name = update.message.text
    
    try:
        course_name = context.user_data['course_selected']
        news = context.user_data['courses'][course_name]['newslist'][news_name]
        del context.user_data['course_selected']
    except KeyError:
        no_news = 'La notizia indicata non esiste, riprova.'
        update.message.reply_text(no_news)
        return 2
    
    news_msg = uni.get_news_msg(context.user_data, news)
    update.message.reply_text(news_msg, reply_markup=ReplyKeyboardRemove())

    # Save in the pickle file
    pp.flush()

    return ConversationHandler.END


def cancel(update, context):
    """
    Undo any command which is going on
    """
    update.message.reply_text('Ok, comando annullato.',reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def error(update, error):
    """
    Log Errors caused by Updates
    """
    logger.warning('Update "%s" caused error "%s"', update, error)


def callback_query(update, context):
    query = update.callback_query
    query.answer("Done")


def listen(bot, dp, upd_time):
    """
    Listen for updates of files and news on Unistudium
    """
    while True:
        print(Fore.CYAN + "Controllo per nuovi updates...")

        for uid in dp.user_data:
            # To Debug the listen function, uncomment carefully these lines
            # del dp.user_data[uid]['courses']['INGEGNERIA DEL SOFTWARE (2018/19)']['fileslist'][0][1][3]
            # dp.user_data[uid]['courses']['INGEGNERIA DEL SOFTWARE (2018/19)']['fileslist'][1][1] = []
            # quit()

            # Check if the server is online and the credentials are valid
            response = uni.reconnect(dp.user_data[uid])
            if response != "OK":
                continue

            # Download courses list if it doesn't exist
            if 'courses' not in dp.user_data[uid]:
                dp.user_data[uid]['courses'] = uni.get_courseslist(dp.user_data[uid])
                pp.flush()

            for course in dp.user_data[uid]['courses']:
                if dp.user_data[uid]['courses'][course]['followed'] == '🔕':
                    # Skip this course for this user
                    continue

                # Get the most updated files list
                new_files_list = uni.get_course_fileslist(dp.user_data[uid], dp.user_data[uid]['courses'][course]['url'])
                
                # Check if I don't have a previous version
                if not 'fileslist' in dp.user_data[uid]['courses'][course]:
                    dp.user_data[uid]['courses'][course]['fileslist'] = new_files_list
                    pp.flush()
                    continue
                    
                old_files_list = dp.user_data[uid]['courses'][course]['fileslist']
                
                # Find the differences between these two lists
                def find_diff(first_list, second_list):
                    diffs = []
                    # Iterate over the sections
                    for first_sec in first_list:
                        for second_sec in second_list:
                            # If the section name is the same, we could find diffs
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
                            # This is a new section, add it to the diffs
                            diffs.append(first_sec)
                    return diffs

                # Find additions and removes
                additions = find_diff(new_files_list, old_files_list)
                removes   = find_diff(old_files_list, new_files_list)

                # Get the most updated forum news
                # TO DO

                # Notify all the users "registered" of the updates
                if additions or removes:
                    # Update data
                    dp.user_data[uid]['courses'][course]['fileslist'] = new_files_list
                    pp.flush()
                    print(Fore.GREEN + "Ho trovato nuovi updates nel corso di %s (per uid: %d)" % (course, uid))

                    # If we have both additions and removes
                    new_upd_msg = "Ciao, ho trovato dei nuovi aggiornamenti nel corso di:\n*{}*".format(course)
                    if additions and removes:
                        custom_mex = new_upd_msg + "\n\n📎 *Files aggiunti:*\n\n"
                        mexs = uni.get_formatted_fileslist(additions, custom_mex)

                        for mex in mexs:
                            bot.sendMessage(uid, mex, parse_mode=ParseMode.MARKDOWN)

                        custom_mex = "💣 *Files rimossi:*\n\n"
                        mexs = uni.get_formatted_fileslist(removes, custom_mex)

                        for mex in mexs:
                            bot.sendMessage(uid, mex, parse_mode=ParseMode.MARKDOWN)
                    elif additions:
                        custom_mex = new_upd_msg + "\n\n📎 *Files aggiunti:*\n\n"
                        mexs = uni.get_formatted_fileslist(additions, custom_mex)

                        for mex in mexs:
                            bot.sendMessage(uid, mex, parse_mode=ParseMode.MARKDOWN)
                    elif removes:
                        custom_mex = new_upd_msg + "\n\n💣 *Files rimossi:*\n\n"
                        mexs = uni.get_formatted_fileslist(removes, custom_mex)

                        for mex in mexs:
                            bot.sendMessage(uid, mex, parse_mode=ParseMode.MARKDOWN)

        # Wait for a bit, then check for updates once more
        print(Fore.CYAN + "Aspetto per altri %d secondi" % UPD_TIME)
        time.sleep(upd_time)


def main():
    # Setting up
    colorama.init(autoreset=True)

    # Create the EventHandler and pass it your bot's token.
    updater = Updater(TOKEN, persistence=pp, use_context=True)
    dp = updater.dispatcher

    # Adding all the handler for the commands
    cmd_login = ConversationHandler(
        entry_points=[CommandHandler('login', login)],

        states={
            1: [MessageHandler(Filters.text, login_1)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    cmd_notifications = ConversationHandler(
        entry_points=[CommandHandler('notifications', notifications)],

        states={
            1: [MessageHandler(Filters.text, notifications_1)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    cmd_viewfiles = ConversationHandler(
        entry_points=[CommandHandler('viewfiles', viewfiles)],

        states={
            1: [MessageHandler(Filters.text | Filters.command, viewfiles_1)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    cmd_viewnews = ConversationHandler(
        entry_points=[CommandHandler('viewnews', viewnews)],

        states={
            1: [MessageHandler(Filters.text, viewnews_1)],
            2: [MessageHandler(Filters.text, viewnews_2)],
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help_list))
    dp.add_handler(CommandHandler('info', info))
    dp.add_handler(CommandHandler('logout', logout))
    dp.add_handler(cmd_login)
    dp.add_handler(cmd_notifications)
    dp.add_handler(cmd_viewfiles)
    dp.add_handler(cmd_viewnews)
    dp.add_handler(CommandHandler('cancel', cancel))

    # Adding callback_query handler
    dp.add_handler(CallbackQueryHandler(callback_query))
    # Log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()
    print("Ready to work.")

    # Start the listener for new files in courses' page
    listener = threading.Thread(target=listen, args=(updater.bot, dp, UPD_TIME))
    listener.start()
    
    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT.
    updater.idle()


if __name__ == '__main__':
    main()
