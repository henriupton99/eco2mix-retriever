import time
import requests
import pandas as pd

from datetime import datetime, timedelta
from typing import Optional, List
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

    def _download_bytes(self, date_dt: datetime, region: str) -> bytes:
        params = {"date": date_dt.strftime("%d/%m/%Y"), "region": region}
        resp = self.session.get(self.base_url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.content

    def download_day_region(self, date_dt: datetime, region: str) -> pd.DataFrame:
        """
        Download region content from eco2mix platform for a given date_dt and region.
        Return a pandas dataframe with a single column "date" as merge of column "Date" and "Heures" + production/consumption columns
        """
        content = self._download_bytes(date_dt, region)
        df = parse_eco2mix_bytes(content)
        
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
            raise KeyError("Impossible to find 'Date' column in file (actual columns: {}).".format(available_cols))
        if heures_col is None:
            raise KeyError("Impossible to find 'Heures' column in file (actual columns: {}).".format(available_cols))
        
        df['date_concat'] = df[date_col].astype(str).str.strip() + ' ' + df[heures_col].astype(str).str.strip()
        
        df['date'] = pd.to_datetime(df['date_concat'], dayfirst=False, errors='coerce')
        
        if df['date'].isna().sum() > 0.5 * len(df):
            df['date'] = pd.to_datetime(df['date_concat'], dayfirst=True, errors='coerce')
          
        df['date'] = df['date'].dt.strftime("%Y-%m-%d %H:%M:%S")
        result_cols = ['date'] + matched_cols
        existing = [c for c in result_cols if c in df.columns]
        result = df.loc[:, existing].copy()
        
        return result

    def collect_range(self, start_date: str, end_date: str, regions: List[str], outdir: str):
        """
        Retrieve files from start_date to end_date included (format YYYY-MM-DD)
        for each provided region. Save data as single CSV file for each region and day.
        """
        s = datetime.strptime(start_date, "%Y-%m-%d")
        e = datetime.strptime(end_date, "%Y-%m-%d")
        current = s
        while current <= e:
            for region in regions:
                try:
                    df = self.download_day_region(current, region)
                    fname = f"{outdir.rstrip('/')}/eco2mix_{region}_{current.strftime('%Y-%m-%d')}.csv"
                    df.to_csv(fname, index=False, sep=';', encoding='utf-8')
                    print(f"Saved: {fname} ({len(df)} rows)")
                except Exception as ex:
                    print(f"[ERROR] region={region} date={current.date()} -> {ex}")
                time.sleep(self.sleep)
            current += timedelta(days=1)
