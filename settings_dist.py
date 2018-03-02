import os

TOKEN     = 'YOUR_TOKEN'
bot_name  = "@UnistudiumListenerBot"

update_time = 3600 # seconds

userDir             = os.path.dirname(os.path.abspath(__file__)) + "/UserPref/"
configDir           = userDir + "ChatConfig/"
coursesFollowedDir  = userDir + "CoursesFollowed/"
coursesFullDir      = userDir + "CoursesFull/"

dlDir               = os.path.dirname(os.path.abspath(__file__)) + "/Download/"
fileslistDir        = dlDir + "FilesList/"
filesDir            = dlDir + "Files/"
newslistDir         = dlDir + "NewsList/"

pidfile   = "/tmp/unistudiumlistener.pid"

LOGIN_URL = "https://www.unistudium.unipg.it/unistudium/login/index.php"
MAIN_URL  = "https://www.unistudium.unipg.it/unistudium/"

def_config = [
    1,    # English language
    1,    # Notification ON
    0     # Don't download any file
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
