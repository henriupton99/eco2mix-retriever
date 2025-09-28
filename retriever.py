import re
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional

import requests
import pandas as pd

from utils import parse_eco2mix_bytes, match_desired_columns, simplify_col_name

BASE_URL = "https://eco2mix.rte-france.com/curves/eco2mixDl"

class Eco2mixRetriever:
    def __init__(self, base_url: str = BASE_URL, user_agent: Optional[str] = None, sleep_between_requests: float = 1.0):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent or "eco2mix-retriever (https://github.com/henriupton99/eco2mix-retriever)"
        })
        self.sleep = float(sleep_between_requests)
        
        self.dtypes = {
            "Données temps réel": "TR",
            "Données consolidées": "CONS",
            "Données définitives": "DEF"
        }
        
    def _expected_dtype_for_date(self, date_dt: datetime, run_dt: Optional[datetime] = None) -> str:
        """Infère le DTYPE attendu selon l'année du run et l'année de la date."""
        run_dt = run_dt or datetime.now()
        A = run_dt.year
        y = date_dt.year
        if y == A:
            return "TR"
        elif y == A - 1:
            return "CONS"
        else:
            return "DEF"

    def _cached_filepath(self, region: str, date_dt: datetime, outdir: str) -> Optional[Path]:
        """Retourne le chemin du fichier cache existant pour region/date, ou None."""
        p = Path(outdir)
        if not p.exists():
            return None
        pattern = f"eco2mix_{region}_*_{date_dt.strftime('%Y-%m-%d')}.csv"
        matches = list(p.glob(pattern))
        return matches[0] if matches else None

    def _extract_dtype_from_filename(self, filename: str) -> Optional[str]:
        m = re.search(r"_(TR|CONS|DEF)_\d{4}-\d{2}-\d{2}\.csv$", filename)
        return m.group(1) if m else None

    def _download_bytes(self, date_dt: datetime, region: str) -> bytes:
        params = {"date": date_dt.strftime("%d/%m/%Y")}
        if region != "FR":
            params["region"] = region
        resp = self.session.get(self.base_url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.content

    def _download_and_parse(self, date_dt: datetime, region: str) -> pd.DataFrame:
        """
        Télécharge et parse un jour/region.
        Retourne un DataFrame contenant au moins la colonne 'date' et éventuellement 'Nature'
        (avec 'Nature' mappée vers TR/CONS/DEF si possible).
        """
        content = self._download_bytes(date_dt, region)
        df = parse_eco2mix_bytes(content)
        df = df.iloc[:-1, :] 
        if region == "FR":
            columns = df.columns[1:]
            df = df.iloc[:, :-1]
            df.columns = columns

        available_cols = df.columns.tolist()
        matched_cols = match_desired_columns(available_cols)

        col_map = { simplify_col_name(c): c for c in available_cols }
        date_col = col_map.get('date') or col_map.get('date_jour') or col_map.get('date_heure') or None
        heures_col = col_map.get('heures') or col_map.get('heure') or col_map.get('heures_utc') or None

        if date_col is None or heures_col is None:
            for s, orig in col_map.items():
                if 'date' in s and date_col is None:
                    date_col = orig
                if 'heure' in s and heures_col is None:
                    heures_col = orig

        if date_col is None:
            raise KeyError(f"Impossible to trouver 'Date' (colonnes: {available_cols})")
        if heures_col is None:
            raise KeyError(f"Impossible to trouver 'Heures' (colonnes: {available_cols})")

        df['date_concat'] = df[date_col].astype(str).str.strip() + ' ' + df[heures_col].astype(str).str.strip()
        df['date'] = pd.to_datetime(df['date_concat'], dayfirst=False, errors='coerce')
        if df['date'].isna().sum() > 0.5 * len(df):
            df['date'] = pd.to_datetime(df['date_concat'], dayfirst=True, errors='coerce')
        df['date'] = df['date'].dt.strftime("%Y-%m-%d %H:%M:%S")

        result_cols = ['date'] + matched_cols
        existing = [c for c in result_cols if c in df.columns]
        result = df.loc[:, existing].copy()
        
        if 'Nature' in result.columns:
            result['Nature'] = result['Nature'].map(self.dtypes)
        else:
            for s, orig in col_map.items():
                if 'nature' in s:
                    result['Nature'] = df[orig].map(self.dtypes)
                    break

        return result
    
    def ensure_cached_for_date_region(self, date_dt: datetime, region: str, outdir: str,
                                      run_dt: Optional[datetime] = None, force: bool = False) -> Optional[Path]:
        """
        Assure qu'un fichier journalier existe dans outdir pour la pair region/date.
        - Si un fichier cache est trouvé, il est retourné (sauf si force=True).
        - Sinon, on télécharge, on parse et on sauve sous le nom eco2mix_{REGION}_{DTYPE}_{YYYY-MM-DD}.csv
        Retourne le Path du fichier sauvé ou None en cas d'erreur.
        """
        p_out = Path(outdir)
        p_out.mkdir(parents=True, exist_ok=True)

        existing = self._cached_filepath(region, date_dt, outdir)
        if existing and not force:
            print(f"[CACHE] found {existing.name} -> skip download")
            return existing

        try:
            df = self._download_and_parse(date_dt, region)
        except Exception as ex:
            print(f"[ERROR] download/parse failed for {region} {date_dt.date()}: {ex}")
            return None
        
        dtype = None
        if 'Nature' in df.columns:
            vals = df['Nature'].dropna().unique().tolist()
            if vals:
                dtype = vals[0]

        if not dtype:
            dtype = self._expected_dtype_for_date(date_dt, run_dt)
            
        if 'Nature' in df.columns:
            df_to_save = df.drop(columns=['Nature'])
        else:
            df_to_save = df

        fname = p_out / f"eco2mix_{region}_{dtype}_{date_dt.strftime('%Y-%m-%d')}.csv"
        try:
            df_to_save.to_csv(fname, index=False, sep=';', encoding='utf-8')
            print(f"[SAVED] {fname} ({len(df_to_save)} rows)")
            return fname
        except Exception as ex:
            print(f"[ERROR] saving file {fname}: {ex}")
            return None
        
    def collect_range(self, start_date: str, end_date: str, regions: List[str], outdir: str,
                    run_dt: Optional[datetime] = None, force: bool = False, aggregate: bool = True):
        """
        Complète le cache puis construit un fichier agrégé pour chaque région selon priorité DEF > CONS > TR.
        """
        run_dt = run_dt or datetime.now()
        s = datetime.strptime(start_date, "%Y-%m-%d")
        e = datetime.strptime(end_date, "%Y-%m-%d")
        current = s
        
        while current <= e:
            for region in regions:
                try:
                    self.ensure_cached_for_date_region(current, region, outdir, run_dt=run_dt, force=force)
                except Exception as ex:
                    print(f"[ERROR] region={region} date={current.date()} -> {ex}")
                time.sleep(self.sleep)
            current += timedelta(days=1)
        
        if not aggregate:
            return

        priority = {"DEF": 3, "CONS": 2, "TR": 1}

        for region in regions:
            frames = []
            missing = []
            current = s
            while current <= e:
                pattern = f"eco2mix_{region}_*_{current.strftime('%Y-%m-%d')}.csv"
                files = list(Path(outdir).glob(pattern))

                if not files:
                    missing.append(current.strftime("%Y-%m-%d"))
                else:
                    best_file = None
                    best_rank = -1
                    for f in files:
                        dtype = self._extract_dtype_from_filename(f.name)
                        if dtype and priority[dtype] > best_rank:
                            best_rank = priority[dtype]
                            best_file = f
                    if best_file:
                        try:
                            df = pd.read_csv(best_file, sep=';', dtype=str)
                            dtype = self._extract_dtype_from_filename(best_file.name)
                            df['DTYPE'] = dtype
                            frames.append(df)
                        except Exception as ex:
                            print(f"[ERROR] reading {best_file}: {ex}")

                current += timedelta(days=1)
                
            if frames:
                agg = pd.concat(frames, ignore_index=True, sort=False)
                cols = list(agg.columns)
                if 'date' in cols:
                    cols.remove('date')
                    newcols = ['date']
                    if 'DTYPE' in cols:
                        cols.remove('DTYPE')
                        newcols += ['DTYPE']
                    newcols += cols
                    agg = agg.loc[:, newcols]
                outpath = Path(outdir) / f"eco2mix_{region}_{s.strftime('%Y-%m-%d')}_{e.strftime('%Y-%m-%d')}.csv"
                agg.to_csv(outpath, index=False, sep=';', encoding='utf-8')
                print(f"[AGGREGATED] {outpath} ({len(agg)} rows). Missing days: {len(missing)}")
                if missing:
                    print(f"  -> missing days for region {region}: {missing}")
            else:
                print(f"[WARNING] nothing to aggregate for region {region} in {start_date}..{end_date}. Missing days: {missing}")

