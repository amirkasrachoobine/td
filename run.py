#!/usr/bin/env python3
"""Start Tower Defense or validate the bundled campaign."""

import argparse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true",
                        help="validate the campaign without opening pygame")
    args = parser.parse_args()
    try:
        from td import config
    except ValueError as error:
        parser.error(str(error))
    if args.validate:
        print(f"Valid campaign: {config.TOTAL_WAVES} waves across {len(config.MAPS)} maps")
        return

    from td.main import main as play
    play()


if __name__ == "__main__":
    main()
