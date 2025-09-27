import argparse
from retriever import Eco2mixRetriever

def main():
    parser = argparse.ArgumentParser(description="eco2mix retriever - download regional data and export CSVs.")
    parser.add_argument("--start", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="End date YYYY-MM-DD (inclusive)")
    parser.add_argument("--regions", required=True, nargs="+", help="List of region codes (ex: ARA IDF PACA).")
    parser.add_argument("--outdir", default="./data", help="Output directory for CSV files.")
    parser.add_argument("--sleep", type=float, default=1.0, help="Seconds to sleep between requests (default 1s).")
    args = parser.parse_args()
    
    import os
    os.makedirs(args.outdir, exist_ok=True)

    dl = Eco2mixRetriever(sleep_between_requests=args.sleep)
    dl.collect_range(args.start, args.end, args.regions, args.outdir)

if __name__ == "__main__":
    main()
