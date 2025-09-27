## eco2mix-retriever

Easy python tool to retrieve éCO2mix public available data.

### 1. Installation

With a recommended python version >=3.12, retrieve the virtual environment of the project with the package manager *uv* :

```bash
pip install uv
uv --version
```

### 2. Available data

Data can be retrieved by a general command by providing the following list of arguments : 
* **start**: start date of retrieval, inclusive (format *YYYY-MM-DD*)
* **end**: end date of retrieval, inclusive (format *YYYY-MM-DD*)
* **regions**: list of regions to retrieve (separated with a space)
* **outdir**: path to output directory to save the output files

List of available regions codes : 
* ARA -> Auvergne-Rhône-Alpes
* BFC -> Bourgogne-Franche-Comté
* BRE -> Bretagne
* CEN -> Centre-Val de Loire
* ACA -> Grand Est
* NPP -> Hauts-de-France
* IDF -> Île-de-France
* NOR -> Normandie
* ALP -> Nouvelle-Aquitaine
* LRM -> Occitanie
* PLO -> Pays de la Loire
* PAC -> Provence-Alpes-Côte d'Azur

#### 2.1. Real time production / consumption data

Example of output format : [here](./data/eco2mix_ARA_2025-09-01.csv)

Command : 
```bash
uv run main.py --start 2025-09-01 --end 2025-09-05 --regions ARA --outdir ./data
```

