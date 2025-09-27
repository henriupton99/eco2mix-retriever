import re
import io
import zipfile
import unicodedata
import pandas as pd

from typing import List

DESIRED_COLS = [
    "Consommation", "Thermique", "Nucléaire", "Eolien", "Solaire", "Hydraulique",
    "Pompage", "Bioénergies", "Stockage batterie", "Déstockage batterie",
    "Eolien terrestre", "Eolien offshore"
]

def simplify_col_name(s: str) -> str:
    """Simplify column name by removing accents and other symbols"""
    s = str(s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '_', s)
    s = s.strip('_')
    return s

def match_desired_columns(df_columns: List[str]) -> List[str]:
    """
    Return columns that match the desired columns to retrieve, based on df_columns input
    """
    simplified_map = { simplify_col_name(c): c for c in df_columns }
    matched = []
    for col in DESIRED_COLS:
        key = simplify_col_name(col)
        if key in simplified_map:
            matched.append(simplified_map[key])
        else:
            candidates = [orig for s, orig in simplified_map.items() if key in s or s in key]
            if candidates:
                matched.append(candidates[0])
    return matched

def parse_eco2mix_bytes(content: bytes) -> pd.DataFrame:
    """
    Parse content bytes returned by the RTE endpoint and returns a pandas.DataFrame.
    Handles:
      - ZIP archives (faux .xls) that contain a text file (.xls/.csv/.txt)
      - raw CSV/TXT in bytes (tab-separated or semicolon)
      - fallback read_excel for real excel if needed
    """
    if content[:2] == b'PK':
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            names = z.namelist()
            candidates = [n for n in names if n.lower().endswith(('.csv', '.txt', '.xls')) or 'eco2mix' in n.lower()]
            candidate = candidates[0] if candidates else names[0]
            data = z.read(candidate)
            for sep in ['\t', ';', ',']:
                try:
                    return pd.read_csv(io.BytesIO(data), sep=sep, encoding='latin-1', engine='python', on_bad_lines='skip')
                except Exception:
                    continue
            text = data.decode('latin-1', errors='replace')
            return pd.read_csv(io.StringIO(text), sep='\t', engine='python', on_bad_lines='skip')
    
    for sep in ['\t', ';', ',']:
        try:
            return pd.read_csv(io.BytesIO(content), sep=sep, encoding='latin-1', engine='python', on_bad_lines='skip')
        except Exception:
            continue
    try:
        return pd.read_excel(io.BytesIO(content), engine='xlrd')
    except Exception as e:
        raise ValueError("Impossible to parse the imput content (no zip text, no csv).") from e
