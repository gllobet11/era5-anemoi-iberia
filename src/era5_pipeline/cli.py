import argparse
import logging

from era5_pipeline.config import load_config


def main(argv=None):
    p = argparse.ArgumentParser(prog="era5_pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)
    for cmd in ("ingest", "transform"):
        sub.add_parser(cmd).add_argument("--config", required=True)
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = load_config(args.config)
    if args.cmd == "ingest":
        from era5_pipeline.ingest import ingest

        print(ingest(cfg))
    elif args.cmd == "transform":
        from era5_pipeline.transform import transform

        print(transform(cfg))


if __name__ == "__main__":
    main()
