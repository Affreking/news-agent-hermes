# scheduler.py — Ordonnanceur du brief quotidien (SPEC §4 / §14).
# Le pilot est conçu pour s'exécuter sur une machine disponible 24h/24.
# Deux modes :
#   1) crontab (Unix) : la ligne suivante lancera le brief tous les jours à 06:00 GMT.
#   2) daemon   : boucle inexhauste qui relance run() tous les jours à 06:00 GMT.

import os, sys, time, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from news_brief import run

MODE = "daemon"  # "daemon" | "cron-line" | "once"

def cron_line(hour="06", minute="00", tz="Africa/Abidjan"):
    # cron(5) ne gère pas le fuseau : utilise la variable TZ si votre cron le supporte.
    return (f"0 {minute} {hour} * * TZ={tz} cd {os.path.dirname(os.path.abspath(__file__))} && "
            f"python3 news_brief.py run >> logs/scheduler_cron.log 2>&1")

def daemon(mode_run="run", interval=900):
    """Boucle infinie. Être exécuté sous systemd/cron avec une limite de temps."""
    while True:
        try:
            run()
            # attend 24h + marge (900s = 15min de tolérance pour le retard le matin)
            for _ in range(int(24*3600)/interval):
                time.sleep(interval)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[FATAL] {e}", flush=True)

if __name__ == "__main__":
    if MODE == "cron-line":
        print(cron_line())
    elif MODE == "daemon":
        daemon()
    else:
        run()
