#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UnistudiumListener - Telegram Bot
Author: CoffeeStraw
"""
import re
import os
import requests
import threading
import time

import logging
import colorama
from colorama import Fore, Style

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove,
                      InlineKeyboardButton, InlineKeyboardMarkup, ChatAction)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler, CallbackQueryHandler)

import unistudium_framework as uni
from utility import cred_get
from settings import TOKEN, UPD_TIME, MAIN_URL

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Starting session for persisten cookies
current_session = requests.Session()


def start(update, context):
    start_msg = "*Benvenuto a* @UnistudiumListenerBot.\n"\
        "Questo bot ti terrà aggiornato in tempo reale sui nuovi caricamenti effettuati dai docenti "\
        "nei rispettivi corsi presenti sulla piattaforma Unistudium.\n\n"\
        "_Il bot è da considerarsi non ufficiale, né KITLab né Unipg sono responsabili in alcun modo._"

    update.message.reply_markdown(start_msg)

    return ConversationHandler.END


def help(update, context):
    help_msg = "Questa è una lista degli attuali *comandi* presenti nel bot:\n\n"\
        "- /info: Informazioni utili sul bot e sul suo creatore\n\n"\
        "- /trylogin: Effettua un tentativo di connessione al portale di Unistudium con le credenziali "\
        "fornite all'interno del file _cred.json_\n\n"\
        "- /listen: Permette di aggiungere alla propria lista personale i corsi che si desiderano far "\
        "ascoltare al bot\n\n"\
        "- /stoplisten: Permette di rimuovere dalla propria lista personale i corsi di cui non si "\
        "vuole più ricevere aggiornamenti\n\n"\
        "- /viewfiles: Permette di visualizzare una lista di tutti i files presenti in un determinato "\
        "corso\n\n"\
        "- /viewnews: Permette di visualizzare una lista di tutte le news presenti nella sezione forum "\
        "di un determinato corso e leggerne il contenuto\n\n"\
        "- /settings: Accedi alla sezione dedicata alle impostazioni per modificare alcuni parametri "\
        "relativi all'esperienza utente"
    update.message.reply_markdown(help_msg)

    return ConversationHandler.END


def info(update, context):
    info_msg = "*UnistudiumListener* è il miglior metodo per tenerti sempre aggiornato sugli ultimi argomenti "\
               "caricati dai docenti su *Unistudium.*\nL'intero codice sorgente è totalmente open ed è "\
               "consultabile sulla pagina GitHub del creatore di questo bot.\n\n"
    keyboard = [[InlineKeyboardButton("GitHub", url='https://github.com/CoffeeStraw/UnistudiumListenerBot')]]
    update.message.reply_markdown(info_msg, reply_markup=InlineKeyboardMarkup(keyboard))

    return ConversationHandler.END


def trylogin(update, context):
    """
    Simple debug command that can be used to check if we can actually connect to the Unistudium portal
    """
    print(Fore.CYAN + "[CONNECTION] Tentativo di connessione con |{} - {}|".format(cred_get("username"), "*"*len(cred_get("password"))))
    context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)

    response = uni.reconnect(current_session)
    if response != "OK":
        update.message.reply_markdown(
            response, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    main_page = current_session.get(MAIN_URL)

    pattern = "<span class=\"usertext\">(.+?)</span>"
    name = re.findall(pattern, str(main_page.content))[0]

    update.message.reply_markdown("Sono riuscito a collegarmi, benvenuto *%s*!" % name)
    return ConversationHandler.END


def stoplisten(update, context):
    # TO DO
    return ConversationHandler.END


def stoplisten_1(update, context):
    # TO DO
    return ConversationHandler.END


def viewfiles(update, context):
    """
    Request a list of files of a specific course in Unistudium
    """
    # If the user hasn't requested the list of the courses already, we get it using the unistudium framework
    if 'courses' not in context.user_data:
        response = uni.reconnect(current_session)
        if response != "OK":
            # Error
            update.message.reply_markdown(response, reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

        context.user_data['courses'] = uni.get_courseslist(current_session)

    choose_course_view_files = 'Seleziona il corso di cui vuoi vedere i files caricati'
    reply_keyboard = [[course_name] for course_name in context.user_data['courses'].keys()]
    update.message.reply_text(choose_course_view_files, reply_markup=ReplyKeyboardMarkup(reply_keyboard))
    return 1


def viewfiles_1(update, context):
    course_name = update.message.text

    # Check for course name validity
    try:
        course_urls = context.user_data['courses'][course_name]
    except KeyError:
        no_course = 'Non è presente un corso con quel nome, riprova.'
        update.message.reply_text(no_course)
        return 1

    # Get list of files from Unistudium website
    files_list = uni.get_course_fileslist(current_session, course_urls['url'])
    custom_mex = 'Ecco tutti i file che ho trovato nel corso di *%s*:\n\n' % course_name
    mexs = uni.get_formatted_fileslist(files_list, custom_mex)

    for mex in mexs:
        update.message.reply_markdown(mex, reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def viewnews(update, context):
    """
    view news from unistudium
    """
    # If the user hasn't requested the list of the courses already, we get it using the unistudium framework
    if 'courses' not in context.user_data:
        response = uni.reconnect(current_session)
        if response != "OK":
            # Error
            update.message.reply_markdown(response, reply_markup=ReplyKeyboardRemove())
            return ConversationHandler.END

        context.user_data['courses'] = uni.get_courseslist(current_session)

    choose_course_view_files = 'Seleziona il corso di cui vuoi vedere le news caricate'
    reply_keyboard = [[course_name] for course_name in context.user_data['courses'].keys()]
    update.message.reply_text(choose_course_view_files, reply_markup=ReplyKeyboardMarkup(reply_keyboard))
    return 1


def viewnews_1(update, context):
    course_name = update.message.text

    # Check for course name validity
    try:
        course_urls = context.user_data['courses'][course_name]
    except KeyError:
        no_course = 'Non è presente un corso con quel nome, riprova.'
        update.message.reply_text(no_course)
        return 1

    context.user_data['course_news'] = uni.get_forum_news(current_session, course_urls['forum_url'])
    if not context.user_data['course_news']:
        no_news = 'Non è presente alcuna notizia nella pagina della materia scelta.'
        update.message.reply_text(no_news)
        return ConversationHandler.END
    
    choose_news = 'Seleziona la news di cui vuoi vedere il contenuto'
    reply_keyboard = [[news_name] for news_name in context.user_data['course_news'].keys()]
    update.message.reply_text(choose_news, reply_markup=ReplyKeyboardMarkup(reply_keyboard))
    return 2


def viewnews_2(update, context):
    news_name = update.message.text
    
    try:
        news = context.user_data['course_news'][news_name]
    except KeyError:
        no_news = 'La notizia indicata non esiste, riprova.'
        update.message.reply_text(no_news)
        return 2
    
    news_msg = uni.get_news_msg(current_session, news)
    update.message.reply_text(news_msg, reply_markup=ReplyKeyboardRemove())
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


def update(upd_time):
    while True:
        time.sleep(1)


def main():
    # Setting up
    colorama.init(autoreset=True)

    # Create the EventHandler and pass it your bot's token.
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Adding all the handler for the commands
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('info', info))
    dp.add_handler(CommandHandler('trylogin', trylogin))

    cmd_stoplisten = ConversationHandler(
        entry_points=[CommandHandler('stoplisten', stoplisten)],

        states={
            1: [MessageHandler(Filters.text, stoplisten_1)]
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

    dp.add_handler(cmd_stoplisten)
    dp.add_handler(cmd_viewfiles)
    dp.add_handler(cmd_viewnews)
    dp.add_handler(CommandHandler('cancel', cancel))

    # Adding callback_query handler
    dp.add_handler(CallbackQueryHandler(callback_query))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    upd = threading.Thread(target=update, args=(UPD_TIME,))
    upd.start()
    
    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT.
    print("Ready to work.")
    updater.idle()


if __name__ == '__main__':
    main()
