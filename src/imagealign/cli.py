import argparse
from pathlib import Path

from .config import load_config
from .dependencies import check_swarp
from .alignment import run_swarp

def clean_previous_outputs(output_dir):

    output_dir = Path(output_dir)
    patterns = [
        "*_coadd.fits",
        "*_coadd_weight.fits",
        "*.list"
    ]

    for pattern in patterns:
        for file in output_dir.glob(pattern):
            file.unlink()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "config",
        help="YAML Configuration File"
    )

    args = parser.parse_args()

    check_swarp()

    config = load_config(args.config)
    wdir = config.working_dir
    clean_previous_outputs(wdir)
    images = list(sorted(wdir.glob("*.fits")))
    run_swarp(images, config)


if __name__ == "__main__":
    main()