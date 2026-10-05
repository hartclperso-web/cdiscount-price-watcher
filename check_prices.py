#!/usr/bin/env python3
"""
Surveillance de prix Cdiscount.
Pour chaque produit de products.json : ouvre la page avec un vrai navigateur
(Playwright/Chromium), lit le prix et la disponibilite dans les donnees
structurees JSON-LD, et envoie un email si le prix est sous le seuil.

Un fichier state.json memorise la derniere alerte par produit pour eviter
de renvoyer un email a chaque passage tant que le prix reste bas.
"""

import json
import os
import smtplib
import sys
from email.mime.text import MIMEText
from email.utils import formataddr
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
PRODUCTS_FILE = ROOT / "products.json"
STATE_FILE = ROOT / "state.json"

# Ne pas renvoyer d'email pour le meme produit avant ce delai (heures),
# meme si le prix reste sous le seuil.
COOLDOWN_HEURES = 12


def charger_json(path, defaut):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return defaut


def extraire_prix(page):
    """Retourne (prix: float|None, disponible: bool) depuis le JSON-LD de la page."""
    scripts = page.eval_on_selector_all(
        'script[type="application/ld+json"]',
        "els => els.map(e => e.textContent)",
    )
    for brut in scripts:
        try:
            data = json.loads(brut)
        except Exception:
            continue
        for obj in (data if isinstance(data, list) else [data]):
            if not isinstance(obj, dict):
                continue
            offers = obj.get("offers")
            if not offers:
                continue
            offers = offers[0] if isinstance(offers, list) else offers
            prix = offers.get("price") or offers.get("lowPrice")
            dispo = str(offers.get("availability", "")).lower()
            disponible = "instock" in dispo or "limited" in dispo
            if prix is not None:
                try:
                    return float(str(prix).replace(",", ".")), disponible
                except ValueError:
                    pass
    return None, False


def envoyer_email(sujet, corps):
    user = os.environ["GMAIL_USER"]
    mdp = os.environ["GMAIL_APP_PASSWORD"]
    destinataire = os.environ.get("ALERT_TO", user)

    msg = MIMEText(corps, "plain", "utf-8")
    msg["Subject"] = sujet
    msg["From"] = formataddr(("Alerte prix Cdiscount", user))
    msg["To"] = destinataire

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, mdp)
        s.sendmail(user, [destinataire], msg.as_string())
    print(f"  -> Email envoye a {destinataire}")


def main():
    import time

    produits = charger_json(PRODUCTS_FILE, [])
    state = charger_json(STATE_FILE, {})
    maintenant = time.time()
    state_modifie = False

    with sync_playwright() as p:
        navigateur = p.chromium.launch()
        page = navigateur.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="fr-FR",
        )

        for prod in produits:
            nom, url, seuil = prod["nom"], prod["url"], float(prod["seuil"])
            print(f"\n{nom} (seuil {seuil} EUR)")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_selector(
                    'script[type="application/ld+json"]', timeout=20000
                )
                prix, disponible = extraire_prix(page)
            except Exception as e:
                print(f"  ! Erreur de lecture : {e}")
                continue

            if prix is None or not disponible:
                print(f"  Indisponible ou prix absent (prix={prix}, dispo={disponible})")
                continue

            print(f"  Prix actuel : {prix} EUR")

            if prix < seuil:
                derniere = state.get(url, {}).get("derniere_alerte", 0)
                if maintenant - derniere < COOLDOWN_HEURES * 3600:
                    print("  Deja alerte recemment, on n'envoie pas (cooldown).")
                    continue
                sujet = f"\U0001F525 Alerte prix Cdiscount : {nom} a {prix:.2f} EUR"
                corps = (
                    f"Le prix de \"{nom}\" est passe sous ton seuil de {seuil:.0f} EUR.\n\n"
                    f"Prix actuel : {prix:.2f} EUR\n\n"
                    f"Lien : {url}\n"
                )
                try:
                    envoyer_email(sujet, corps)
                    state[url] = {"derniere_alerte": maintenant, "prix": prix}
                    state_modifie = True
                except Exception as e:
                    print(f"  ! Echec envoi email : {e}")
                    sys.exit(1)
            else:
                # Prix repasse au-dessus : on oublie l'alerte precedente
                if url in state:
                    del state[url]
                    state_modifie = True
                print("  Au-dessus du seuil, rien a faire.")

        navigateur.close()

    if state_modifie:
        STATE_FILE.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print("\nstate.json mis a jour.")


if __name__ == "__main__":
    main()
