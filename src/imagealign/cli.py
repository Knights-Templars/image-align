import argparse
from pathlib import Path

from .config import load_config
from .dependencies import check_swarp, check_sex, check_scamp
from .alignment import run_swarp
from .logger import setup_logger
from .gaia_catalog import save_catalog
from .util import get_center
from .sextractor import run_sextractor
from .scamp import run_scamp

def clean_previous_outputs(output_dir: Path, remove_gaia: bool = False):

    output_dir = Path(output_dir)
    patterns = [
        "*_coadd.fits",
        "*_coadd_weight.fits",
        "*.list",
        "log.INFO",
        "*_resample.fits",
        "*_resample.weight.fits",
        "*.fits.ldac",
        "*.head"
    ]

    if remove_gaia:
        patterns.extend([
            "gaiacatalog.ldac",
            "gaiacatalog.txt"
        ])

    for pattern in patterns:
        for file in output_dir.glob(pattern):
            file.unlink()

    


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "config",
        help="YAML Configuration File"
    )

    parser.add_argument(
        "--gaia",
        "-g",
        action="store_true",
        help="Query gaia and generate catalog as ldac and ascii" 
    )

    parser.add_argument(
        "--sex",
        action="store_true",
        help="Run sextractor"
    )

    parser.add_argument(
        "--scamp",
        action="store_true",
        help="Run Scamp to fine tune astrometry"
    )

    args = parser.parse_args()
    config = load_config(args.config)

    wdir = config.working_dir
    clean_previous_outputs(wdir, remove_gaia=args.gaia)

    logger = setup_logger(wdir)
    logger.info("Starting image-align")

    if config.align.precise_align:

        images = list(sorted(wdir.glob("*.fits")))

        if args.gaia:
            (ra_cent, dec_cent) = get_center(images[0])

            save_catalog(ra_cent, dec_cent, 0.1, 10, 20, catname=wdir)

        if args.sex:
            check_sex()
            run_sextractor(images, config)

        if args.scamp:
            check_scamp()

            # these are coming from sextractor runs    
            image_ldacs = list(sorted(wdir.glob('*.fits.ldac')))
            logger.info(f"Collected {len(image_ldacs)} ldac files for scamp")

            run_scamp(image_ldacs, config)

        check_swarp()
        images = list(sorted(wdir.glob("*.fits")))
        logger.info("Running swarp")
        logger.info(f"Collected {len(images)} files for stacking")
        run_swarp(images, config)

        logger.info("Gaia catalogue made.")
        logger.info("Ran SExtractor.")
        logger.info("SCAMP successful.")
        logger.info("Swarp coadding done! :)")


    else:
        if any([
            args.gaia,
            args.sex,
            args.scamp
        ]):
            logger.error("Precise align is disabled."
                         "Skipping Gaia/Sextractor/SCAMP.")
            

        logger.info("Precise alignment in not turned on. Running SWarp only")
        check_swarp()
        images = list(sorted(wdir.glob("*.fits")))
        logger.info("Running swarp")
        logger.info(f"Collected {len(images)} files for stacking")
        run_swarp(images, config)



if __name__ == "__main__":
    main()