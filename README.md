## eco2mix-retriever

Outil Python simple pour récupérer les [données publiques de puissances disponibles d’éCO2mix](https://www.rte-france.com/eco2mix/telecharger-les-indicateurs).

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
* **sleep** (optionnel) : délai d'attente ("cooldown") entre chaque requete (en secondes). Par défaut : 1s

La commande générique d'execution est la suivante : 

```bash
uv run main.py --start 2024-12-25 --end 2025-01-15 --regions ARA --outdir ./output
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

* **temps-réel (TR)** : Dates de l'année en cours A (exemple [01/01/2025](./data/eco2mix_ARA_TR_2025-01-01.csv)). *données de puissance instantanée basées sur des télé-informations et
des estimations pour les sites non télémesurés*
* **consolidé (CONS)** : Dates de l'année A-1 (exemple [01/01/2024](./data/eco2mix_ARA_CONS_2024-01-01.csv)) *données de puissance moyenne basées sur les comptages de Rte et
d’Enedis*
* **définitif (DEF)** : Dates de l'année A-2 et plus anciennes (exemple [01/01/2023](./data/eco2mix_ARA_DEF_2023-01-01.csv)) *données de puissance moyenne basées sur l’ensemble des comptages
de Rte et des ELD*

Plus d'informations sur les différents types de données ici : [lien](https://assets.rte-france.com/prod/public/2025-06/Eco2mix%20-%20Sp%C3%A9cifications%20des%20fichiers%20en%20puissance.pdf)

Le récupération fonctionne avec un système de cache. Selon la date de récupation et les dates demandées, une analyse des fichiers déjà récupérés est effectuée en amont de sorte à ne pas effectuer des requetes déjà effectuées dans le passé : 

```bash
[SAVED] output/eco2mix_ARA_CONS_2024-12-25.csv (96 rows)
[SAVED] output/eco2mix_ARA_CONS_2024-12-26.csv (96 rows)
[SAVED] output/eco2mix_ARA_CONS_2024-12-27.csv (96 rows)
[SAVED] output/eco2mix_ARA_CONS_2024-12-28.csv (96 rows)
[SAVED] output/eco2mix_ARA_CONS_2024-12-29.csv (96 rows)
[SAVED] output/eco2mix_ARA_CONS_2024-12-30.csv (96 rows)
[SAVED] output/eco2mix_ARA_CONS_2024-12-31.csv (96 rows)
[CACHE] found eco2mix_ARA_2025-01-01_2025-01-01.csv -> skip download
[CACHE] found eco2mix_ARA_TR_2025-01-02.csv -> skip download
[CACHE] found eco2mix_ARA_TR_2025-01-03.csv -> skip download
[CACHE] found eco2mix_ARA_TR_2025-01-04.csv -> skip download
[CACHE] found eco2mix_ARA_TR_2025-01-05.csv -> skip download
[AGGREGATED] output/eco2mix_ARA_2024-12-25_2025-01-05.csv (1152 rows). Missing days: 0
```

Une agrégation des fichiers journaliers est finalement réalisée pour chaque région de sorte à obtenir un historique complet en un seul fichier CSV. Le nom générique d'un fichier de sortie est le suivant (exemple de sortie récupérée le 28/09/2025 pour le range [25/12/2024->05/01/2025](./data/eco2mix_ARA_2024-12-25_2025-01-05.csv)): **"eco2mix_\<REGION>_\<DTYPE>_\<DATE_START>_\<DATE_END>.csv"**

*NB : Un ordre de priorité selon le type de données est appliqué pour chaque jour : DEF si disponible, sinon CONS si disponible, sinon TR. Le type de données est indiqué dans le fichier de sortie (colonne DTYPE). Pour l'exemple ci dessus, on a donc du CONS du pour les dates de 2024 puis du TR pour les dates de 2025 car la récupération a été effectuée en 2025.*


