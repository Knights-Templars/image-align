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
from .check_align import check_alignment
from .util import copy_header_keywords
from .util import update_coadd_exptime
from .separate_filters import separate_by_filter


def combine_by_filter(images, config, logger):
    """Run SWarp and update coadd metadata independently for each filter."""

    if not images:
        raise ValueError(f"No FITS images found in {config.working_dir}")

    filter_groups = separate_by_filter(images)
    logger.info("Separated %d images into %d filter group(s)",
                len(images), len(filter_groups))

    coadd_files = []
    for filter_name, filter_images in filter_groups.items():
        logger.info("Combining %d image(s) for filter %s",
                    len(filter_images), filter_name)
        coadd_file = run_swarp(
            filter_images,
            config,
            filter_name=filter_name,
        )
        update_coadd_exptime(filter_images, coadd_file)
        copy_header_keywords(
            filter_images[0],
            coadd_file,
            config,
            filter_name=filter_name,
        )
        coadd_files.append(coadd_file)

    return coadd_files

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
        "*.head",
        "*.png"
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

    parser.add_argument(
        "--check_align",
        action="store_true",
        help="Test Alignment"
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
        combine_by_filter(images, config, logger)

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
        combine_by_filter(images, config, logger)

        if args.check_align:
            resampled_images = list(sorted(wdir.glob("*_resample.fits")))
            logger.info("Testing image alignment")
            check_alignment(resampled_images, config)

if __name__ == "__main__":
    main()
