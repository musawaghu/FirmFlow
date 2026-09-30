"""Command line entry point. Phase 1 only validates configuration."""

from __future__ import annotations

import argparse
import sys

from collector.config import ConfigError, load_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="firmflow-collector")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check-config", help="validate a config file and print what would be read")
    check.add_argument("config")
    args = parser.parse_args(argv)

    if args.command == "check-config":
        try:
            cfg = load_config(args.config)
        except ConfigError as exc:
            print(f"Config error: {exc}", file=sys.stderr)
            return 1
        print("Config OK. Channels the collector may read:")
        for s in cfg.sources:
            print(f"  {s.id} ({s.type.value}): {', '.join(s.channels)}")
        print(f"Smallest group shown to admins: {cfg.privacy.min_group_size} people")
        print(f"Raw text kept for: {cfg.privacy.raw_retention_days} days")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
