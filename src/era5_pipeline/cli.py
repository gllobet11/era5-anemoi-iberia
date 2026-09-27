import argparse
import logging

from era5_pipeline.config import load_config


def main(argv=None):
    p = argparse.ArgumentParser(prog="era5_pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)
    ing = sub.add_parser("ingest")
    ing.add_argument("--config", required=True)
    ing.add_argument("--month", help="YYYY-MM: solo ese mes (tarea de job array)")
    for cmd in ("transform", "months"):
        sub.add_parser(cmd).add_argument("--config", required=True)
    qc_p = sub.add_parser("qc")
    qc_p.add_argument("--zarr", required=True)
    qc_p.add_argument("--config", default="configs/iberia.yaml")
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    cfg = load_config(args.config)
    if args.cmd == "ingest":
        from era5_pipeline.ingest import ingest

        print(ingest(cfg, month=args.month))
    elif args.cmd == "months":
        from era5_pipeline.ingest import months

        print("\n".join(f"{y}-{m:02d}" for y, m in months(cfg)))
    elif args.cmd == "transform":
        from era5_pipeline.transform import transform

        print(transform(cfg))
    elif args.cmd == "qc":
        from era5_pipeline.qc import qc

        report = qc(args.zarr, cfg)
        failed = [k for k, c in report["checks"].items() if not c["passed"]]
        print(f"QC {'OK' if report['passed'] else 'FALLA'}: {failed or 'todos los checks pasan'}")
        return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
