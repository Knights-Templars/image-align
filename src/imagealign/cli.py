import argparse
from pathlib import Path

from .config import load_config
from .dependencies import check_swarp
from .alignment import run_swarp
from .logger import setup_logger

def clean_previous_outputs(output_dir):

    output_dir = Path(output_dir)
    patterns = [
        "*_coadd.fits",
        "*_coadd_weight.fits",
        "*.list",
        "log.INFO",
        "*_resample.fits",
        "*_resample.weight.fits",
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
    config = load_config(args.config)

    wdir = config.working_dir
    clean_previous_outputs(wdir)

    logger = setup_logger(wdir)
    logger.info("Starting image-align")

    logger.info("Checking swarp installation")
    check_swarp()

    images = list(sorted(wdir.glob("*.fits")))

    logger.info(f"Collected {len(images)} files for stacking")

    logger.info("Running swarp")
    run_swarp(images, config)


if __name__ == "__main__":
    main()