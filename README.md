# Surveillance de prix Cdiscount (cloud, gratuit)

Ce dossier contient tout ce qu'il faut pour surveiller des prix Cdiscount **24h/24**
depuis le cloud GitHub, **même ordinateur éteint**. À chaque passage, un vrai
navigateur ouvre chaque page, lit le prix, et t'envoie un **email** si le prix
passe sous ton seuil.

- Vérification : **toutes les 5 minutes** (minimum fiable sur GitHub Actions)
- Coût : **gratuit** (voir la note sur les minutes plus bas)
- Anti-spam : un seul email par produit, puis silence pendant 12 h tant que le prix reste bas

---

## Ce dont tu as besoin
1. Un compte **GitHub** (gratuit) — https://github.com
2. Une adresse **Gmail** pour envoyer les emails + un **mot de passe d'application** (étape 3)

---

## Étape 1 — Créer le dépôt (repo)
1. Sur GitHub, clique sur **New repository**.
2. Nom au choix (ex. `cdiscount-price-watcher`).
3. Choisis **Public** (recommandé : minutes d'Actions illimitées et gratuites.
   Tes identifiants email ne sont PAS dans le code, ils vont dans des "secrets" chiffrés — voir étape 3).
4. Clique **Create repository**.
5. Clique **uploading an existing file** et glisse-dépose **tout le contenu de ce dossier**
   (le fichier `check_prices.py`, `products.json`, `requirements.txt`, `state.json`,
   et le dossier `.github`). Puis **Commit changes**.

> Important : garde la structure des dossiers. Le fichier du planificateur doit se trouver
> dans `.github/workflows/price-check.yml`.

---

## Étape 2 — Créer un mot de passe d'application Gmail
Gmail n'accepte pas ton mot de passe habituel pour les scripts : il faut un "mot de passe d'application".
1. Active la **validation en deux étapes** sur ton compte Google si ce n'est pas déjà fait :
   https://myaccount.google.com/security
2. Va sur **https://myaccount.google.com/apppasswords**
3. Donne un nom (ex. "Cdiscount watcher") et génère. Google affiche un code de **16 lettres** — copie-le.

---

## Étape 3 — Ajouter les secrets dans GitHub
Dans ton repo : **Settings → Secrets and variables → Actions → New repository secret**.
Crée ces trois secrets :

| Nom du secret         | Valeur                                             |
|-----------------------|----------------------------------------------------|
| `GMAIL_USER`          | ton adresse Gmail (ex. `moi@gmail.com`)            |
| `GMAIL_APP_PASSWORD`  | le code de 16 lettres de l'étape 2 (sans espaces)  |
| `ALERT_TO`            | l'adresse qui reçoit l'alerte (`charinquet@rodeofx.com`) |

---

## Étape 4 — Activer et tester
1. Onglet **Actions** du repo → si demandé, clique **I understand my workflows, enable them**.
2. Clique le workflow **« Surveillance prix Cdiscount »** → **Run workflow** (bouton à droite)
   pour un test immédiat.
3. Ouvre l'exécution pour voir les logs : tu dois voir le prix de chaque produit s'afficher.
   Ensuite, ça tournera tout seul toutes les 5 minutes.

Pour vérifier que l'email marche, tu peux temporairement mettre un seuil très haut
dans `products.json` (ex. `99999`) : tu recevras un email au prochain run, puis remets le bon seuil.

---

## Modifier les produits ou les seuils
Édite **`products.json`** directement sur GitHub (crayon ✏️ puis Commit).
Format :
```json
{
  "nom": "Nom affiché dans l'email",
  "url": "https://www.cdiscount.com/...",
  "seuil": 50
}
```
Ajoute autant de produits que tu veux. Alerte envoyée quand le prix est **strictement
inférieur** au seuil **et** que le produit est **en stock**.

---

## Bon à savoir
- **Fréquence** : GitHub Actions ne descend pas sous 5 min, et peut parfois retarder un run
  en cas de forte charge. Pour du vrai temps réel à la seconde, il faudrait un serveur dédié payant.
- **Minutes gratuites** : repo **public** = illimité. Repo **privé** = 2000 min/mois offertes ;
  à 5 min d'intervalle tu dépasserais ce quota — dans ce cas passe en public, ou espace à 15/30 min
  (change le `cron` dans `.github/workflows/price-check.yml`).
- **Anti-spam** : le fichier `state.json` se met à jour tout seul. Tu verras des petits commits
  automatiques "maj etat alertes" : c'est normal.
- **Blocages Cdiscount** : si le site se met à bloquer, les logs Actions le montreront ;
  on pourra alors ajouter des pauses ou réduire la fréquence.
