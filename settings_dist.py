import os

TOKEN     = 'YOUR_TOKEN'
bot_name  = "@UnistudiumListenerBot"

start_msg = "*Benvenuto a @UnistudiumListenerBot*.\n"\
            "Questo bot ti terrà aggiornato in tempo reale sui nuovi caricamenti"\
            " effettuati dai docenti nei rispettivi corsi presenti sulla piattaforma Unistudium.\n\n"\
            "_Il bot è stato creato in modo non ufficiale, né KITLab né Unipg sono responsabili in alcun modo._"

cmd_list  = "Questa è una lista degli attuali comandi presenti nel bot:\n\n"\
            "/help: Lista dei comandi attualmente disponibili\n"\
            "/info: Informazioni utili sul bot e sul suo creatore\n\n"\
            "..."\

info_msg  = "*UnistudiumListener* è il miglior metodo per tenerti sempre aggiornato"\
            " sugli ultimi argomenti caricati dai docenti su *Unistudium*.\n\n"\
            "Se questo bot ti piace, offrimi una birra!"

userDir             = os.path.dirname(os.path.abspath(__file__)) + "/UserPref/"
configDir           = userDir + "ChatConfig/"
coursesFollowedDir  = userDir + "CoursesFollowed/"
coursesFullDir      = userDir + "CoursesFull/"

dlDir               = os.path.dirname(os.path.abspath(__file__)) + "/Download/"
fileslistDir        = dlDir + "FilesList/"
filesDir            = dlDir + "Files/"

pidfile   = "/tmp/unistudiumlistener.pid"

LOGIN_URL = "https://www.unistudium.unipg.it/unistudium/login/index.php"
MAIN_URL  = "https://www.unistudium.unipg.it/unistudium/"

settings_options = [
    "Lingua",
    "Notifiche",
    "Download automatico"
]

lang_options = [
    "Italiano",
    "English"
]

notification_options = [
    "Disabilita",
    "Abilita"
]

dl_options = [
    "Disabilita",
    "Abilita per tutti i files",
    "Abilita solo per gli ultimi files caricati"
]

type_to_sym = {
    "Pagina"       : "📄",
    "File"         : "💾",
    "Prenotazione" : "📅",
    "URL"          : "🌐",
    "Cartella"     : "📂"
}

class color:
   PURPLE    = '\033[95m'
   CYAN      = '\033[96m'
   DARKCYAN  = '\033[36m'
   BLUE      = '\033[94m'
   GREEN     = '\033[92m'
   YELLOW    = '\033[93m'
   RED       = '\033[91m'
   BOLD      = '\033[1m'
   ITALIC    = '\033[3m'
   UNDERLINE = '\033[4m'
   END       = '\033[0m'
