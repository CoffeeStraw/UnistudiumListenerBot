"""
Functions to talk with Unistudium
"""
import requests
import re
from colorama import Fore, Style

from utility import cred_get, text_to_utf8
from settings import type_to_sym, LOGIN_URL, MAIN_URL


def reconnect(current_session):
    """
    Attempt to perform a login to the Unistudium website, saving the cookies in current_session.

    Returns:
        "OK" if the login was performed correctly, else a description with the error that can be used to inform the users.
    """
    # Check if credentials are set
    if (cred_get("username") == "YOUR_USERNAME" or cred_get("password") == "YOUR_PASSWORD"):
        print(Fore.RED + "[CONNECTION] Credenziali non settate")
        return "Non hai inserito il tuo username e/o la tua password nel file _cred.json_. Modificali e riprova."

    # Check if server is alive
    status_code = requests.head(LOGIN_URL).status_code
    if status_code != 200:
        print(
            Fore.RED + "[CONNECTION] Server irraggiungibile. Status code: " + str(status_code))
        return "Non riesco a contattare il server, riprova più tardi..."

    # If we're not already connected, we try to connect with credentials
    if current_session.head(MAIN_URL).status_code == 200:
        print(Fore.YELLOW + "[CONNECTION] Connessione già instaurata")
        return "OK"

    # Getting credentials
    payload = {
        "username": cred_get("username"),
        "password": cred_get("password")
    }

    # Trying login
    if current_session.post(LOGIN_URL, data=payload).url != MAIN_URL:
        print(Fore.RED + "[CONNECTION] Credenziali errate")
        return "Credenziali Errate"
    else:
        print(
            Fore.GREEN + "[CONNECTION] Connessione al portale UNISTUDIUM effettuata con successo")
        return "OK"


def get_course_ID(course_url):
    """
    Returns the ID of a given course's url.
    """
    pattern = r"id=(.+)"
    return re.search(pattern, course_url).group(1)


def get_courseslist(current_session):
    """
    Attempt to get a list of courses from Unistudium MAIN_URL (view settings.py) page, using the current_session with login performed.

    The courses are returned in a dictionary indicized by the course name containing another dictionary with the urls, like:
    {'COURSE NAME': {'url': Course url', 'forum_url': Course forum url'}}
    """
    # Get source code of the main_url page
    main_page = current_session.get(MAIN_URL)

    # Extract the content of some particular h3 tags containing the courses' name and link
    pattern = r"<h3 class=\"coursename\">(.+?)</h3>"
    courses_html = re.findall(pattern, str(main_page.content))

    # Compiling regex
    pattern_name = re.compile(r"<\w+.*?>(.+?)<\/a>")
    pattern_url = re.compile(r"href=\"(.+?)\"")

    # Extract and save informations in a dict object
    courses = {}
    for course_html in courses_html:
        name = pattern_name.search(course_html).group(1).strip()
        url = pattern_url.search(course_html).group(1).strip()
        forum_url = get_forum_url(current_session, url).strip()

        courses[name] = {'url': url, 'forum_url': forum_url}

    return courses


def get_course_fileslist(current_session, course_url):
    """
    Attempt to get a list with all the files in a course's page, grouped by sections.

    The returned list is constructed as follow:
    [ ['Section Name', ['Type of File', 'Name of the File', 'URL of the File']], [...] ]
    """
    # Get source code of the course_url page
    course_page = current_session.get(course_url)

    # Extract the content from some particular html tags in the course page, retrieving the sections
    pattern = r"<li id=\"section-[0-9]+\"(.+?)<\/ul><\/div><\/li>"
    sections = re.findall(pattern, str(course_page.content))

    # Compiling regex
    pattern_section = re.compile(r"<h3 class=\"sectionname\"><span>(.+?)</span></h3>")
    pattern_files = re.compile(r"<div class=\"activityinstance\">(.+?)<\/div>")
    pattern_file_link = re.compile(r"<a class=\"\" onclick=\".*\" href=\"(.+?)\"")
    pattern_file_name_type = re.compile(r"<span class=\"instancename\">(.+?)<span class=\"accesshide \" ?>(.+?)</span>")

    files_list = []
    for i, section in enumerate(sections):
        # Section name
        section_name = pattern_section.search(section)
        if section_name:
            section_name = section_name.group(1)
        else:
            section_name = "Introduzione"
        files_list.append([section_name, []])

        # Files in the section
        files_html = pattern_files.findall(section)

        for file_html in files_html:
            try:
                file_link = pattern_file_link.search(file_html).group(1).strip()
                file_name, file_type = pattern_file_name_type.search(file_html).group(1, 2)
                file_name = text_to_utf8(file_name.strip())
                file_type = file_type.strip()

                files_list[i][1].append([file_type, file_name, file_link])
            except AttributeError:
                pass

    return files_list


def get_formatted_fileslist(files_list, custom_mex=""):
    """
    Returns a list of formatted message generated by the list of sections of files given.
    It is returned a list, since messages could exceed the maximum length allowed by Telegram (4096 chars atm of writing).

    Parameters:
        files_list (list): List of sections of files returned by get_course_fileslist()        
        custom_mex (str): A message to put at the beginning of the first message of the list
    """
    i = 0
    mexs = [custom_mex]

    for sec in files_list:
        sec_string = "Nella sezione *%s*" % sec[0] + "\n"
        if len(mexs[i] + sec_string) > 4096:  # Max length of text allowed by Telegram
            i += 1
            mexs.append("")
        mexs[i] += sec_string

        for file_downloaded in sec[1]:
            if file_downloaded[0] not in type_to_sym:
                print(Fore.RED + "[ERROR] Risolvere eccezione simbolo: " + file_downloaded[0])
                type_to_sym[file_downloaded[0]] = "⁉️"

            file_string = type_to_sym[file_downloaded[0]] + " [" + file_downloaded[1] + "](" + file_downloaded[2] + ")\n"
            if len(mexs[i] + file_string) > 4096:
                i += 1
                mexs.append("")
            mexs[i] += file_string

        mexs[i] += "\n"

    return mexs


def get_forum_url(current_session, course_url_link):
    """
    Get the forum news url, given the course link. It uses current_session with the cookies obtained by performing the login.
    """
    # Get source code of the course_url page
    course_page = current_session.get(course_url_link)
    
    # Extracting url of the forum from the course page
    pattern = r"<a class=\"\" onclick=\"\" href=\"(.+?)\"><img src"
    try:
        return re.search(pattern, str(course_page.content)).group(1)
    except AttributeError:
        return "https://www.unistudium.unipg.it/unistudium/error/"


def get_forum_news(current_session, forum_link_url):
    """
    Attempt to get a list of all the forum news from a course forum url

    Returned list will contain the news as follow:
    [ ["News name", "URL"], [...] ]
    """
    # Get source code of the forum_url page
    course_page_content = current_session.get(forum_link_url).content
    
    # Extract the content from some particular html tags in the course page, retrieving the sections
    pattern = r"<tr class=(.+?)<\/tr>"
    news_msg = re.findall(pattern, str(course_page_content))

    # Compiling regex
    pattern_news = re.compile(r"<td class=\"topic starter\"><a href=\"(.*?)\">(.*?)</a>.*</td>")

    # Extract news name and url
    news = {}
    for new_news in news_msg:
        try:
            url, name = pattern_news.search(new_news).group(1,2)
        except AttributeError:
            return []

        name = text_to_utf8(name)
        news[name] = url

    return news


def get_news_msg(current_session, link_news):
    """
    Access to a news from url given and returns the content of the news
    """
    # Get source code of the forum_url page
    news_content = current_session.get(link_news).content

    pattern = r"<div class=\"author\".+?</div>"
    head = re.search(pattern, str(news_content)).group(1)

    pattern = r">(.+?)<"
    head = re.findall(pattern, head)

    author = head[1].title()
    date = text_to_utf8(head[2].replace(" - ", "")).title()

    pattern = r"<div class=\"posting fullpost\".+?<p>(.+?)</p><div class=\"attachedimages\""
    news_msg = text_to_utf8(re.search(pattern, str(news_content)).group(1))

    news_msg = re.sub(r"<br */? *>", "\n", news_msg).replace("</p>", "\n")
    news_msg = re.sub(r"<.*?>", "", news_msg)

    final_mex = ""\
                "👤 *AUTORE:* _{}_\n"\
                "📆 *DATA:* _{}_\n"\
                "\n"\
                "📃 *MESSAGGIO:*\n"\
                "{}".format(author, date, news_msg)

    return final_mex
