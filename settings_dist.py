TOKEN = 'YOUR_TOKEN'

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

dlDir    = "YOUR_PATH"
filesDir = dlDir + "Files/"

coursesFile = dlDir + "courses_list.txt"
coursesFollowedFile = dlDir + "courses_followed.txt"

pidfile = "/tmp/unistudiumlistener.pid"

LOGIN_URL = "https://www.unistudium.unipg.it/unistudium/login/index.php"
MAIN_URL  = "https://www.unistudium.unipg.it/unistudium/"

type_to_sym = {
    "Pagina"       : "📄",
    "File"         : "💾",
    "Prenotazione" : "📅",
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
