## eco2mix-retriever

Outil Python simple pour récupérer les données publiques de puissances disponibles d’éCO2mix.

### 1. Installation

Avec une version de Python recommandée >= 3.12, récupérez l’environnement virtuel du projet avec le gestionnaire de paquets *uv* :

```bash
pip install uv
uv --version
```

### 2. Récupération des données

Les données peuvent être récupérées via une commande générale en fournissant la liste d’arguments suivante :

* **start** : date de début de la récupération, incluse (format *AAAA-MM-JJ*)
* **end** : date de fin de la récupération, incluse (format *AAAA-MM-JJ*)
* **regions** : liste des régions à récupérer (séparées par un espace)
* **outdir** : chemin du répertoire de sortie pour enregistrer les fichiers produits

La commande générique d'execution est la suivante : 

```bash
uv run main.py --start 2025-09-01 --end 2025-09-05 --regions ARA FR --outdir ./data
```

Liste des codes de régions disponibles (**\<REGION>**):

* FR → France
* ARA → Auvergne-Rhône-Alpes
* BFC → Bourgogne-Franche-Comté
* BRE → Bretagne
* CEN → Centre-Val de Loire
* ACA → Grand Est
* NPP → Hauts-de-France
* IDF → Île-de-France
* NOR → Normandie
* ALP → Nouvelle-Aquitaine
* LRM → Occitanie
* PLO → Pays de la Loire
* PAC → Provence-Alpes-Côte d’Azur

Il existe trois types de données (**\<DTYPE>**), selon la proximité entre la date de récupération et les dates demandées. Par exemple pour une récupération en date du 28/09/2025:

* **temps-réel (TR)** : Dates de l'année en cours A (exemple [01/01/2025](./data/eco2mix_ARA_TR_2025-01-01.csv))
* **consolidé (CONS)** : Dates de l'année A-1 (exemple [01/01/2024](./data/eco2mix_ARA_CONS_2024-01-01.csv))
* **définitif (DEF)** : Dates de l'année A-2 et plus anciennes (exemple [01/01/2023](./data/eco2mix_ARA_DEF_2023-01-01.csv))

Le dossier de sortie indiqué fonctionne ainsi comme un système de cache : selon la date de récupation et les dates demandées, une analyse des fichiers déjà récupérés est effectuée en amont de sorte à ne pas effectuer des requetes déjà effectuées dans le passé. 

Le nom générique d'un fichier de sortie est le suivant : **"eco2mix_\<REGION>_\<DTYPE>_\<DATE>.csv"**


