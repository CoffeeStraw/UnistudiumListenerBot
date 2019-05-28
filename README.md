<p align="center">
<img src="https://i.imgur.com/wgnHNbJ.jpg" alt="Unistudium Listener" />
</p>

[![forthebadge](http://forthebadge.com/images/badges/made-with-python.svg)](https://www.python.org/)
[![forthebadge](http://forthebadge.com/images/badges/cc-by-nd.svg)](https://opensource.org/licenses/MIT)

**Unistudium Listener** è un bot Telegram creato per aiutare gli studenti dell'università di Perugia a ricevere aggiornamenti sui corsi seguiti all'interno del portale [Unistudium](https://www.unistudium.unipg.it/unistudiumpage/aboutUnistudium.htm).

***

## Caratteristiche

Attualmente il bot dispone delle seguenti caratteristiche:
* Aggiunta e rimozione di un corso ad una lista che si desidera far seguire dal bot
* Visualizzazione dei files/links presenti in un determinato corso
* Aggiornamento ad intervallo regolabile riguardante nuovi files aggiunti di recente dai docenti
* Gestione di singoli utenti o di gruppi
* Download automatico di tutti i files trovati all'interno di un corso o anche solo degli ultimi files caricati da quando si è impostato il bot per seguire quel determinato corso (WIP)

*Lista in costante aggiornamento...*

---

## Installazione

Il bot viene rilasciato con licenza MIT. Ciò significa che chiunque voglia modificare o proporre suggerimenti per implementare nuove funzionalità o risolvere eventuali problemi, può farlo liberamente utilizzando GitHub.

Una volta effettuato il clone della repository attraverso il comando git clone, per poter cominciare ad usare il bot sulla propria macchina bisognerà prima installare le dipendenze del software attraverso questo comando:
```bash
$ sudo pip install -r requirements.txt
```

Oppure nel caso non funzioni (se non si è su Windows ad esempio):
```bash
$ sudo pip3 install -r requirements.txt
```

Dopodiché sarà necessario rinominare il seguente file:
* ``settings_dist.py`` in ``settings.py``,

Il file ``settings.py`` contiene vari parametri che si potranno modificare secondo le proprie esigenze (per un uso facile e veloce, basterà modificare il TOKEN del bot con uno vostro generato tramite [BotFather](http://www.insidevcode.eu/2015/06/27/telegram-3-0-bot/)).

---

## Avvio
L'avvio del bot è molto semplice, basterà eseguire il seguente comando da bash:
```bash
$ python main.py
```

Oppure nel caso non funzioni (se non si è su Windows ad esempio):
```bash
$ python3 main.py
```

---
Il presente bot è stato realizzato tramite l'utilizzo di [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot).

È inoltre da considerarsi totalmente **non ufficiale**, né *KITLab* né *Unipg* sono responsabili in alcun modo.

*This program comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it.*
