import subprocess
from pathlib import Path
from astropy.io import fits
from .util import get_center
import logging


logger = logging.getLogger("imagealign")


def get_name(image, filter_name=None):

    header = fits.getheader(image, 0)
    date = header['DATE-OBS']
    if filter_name is None:
        filter_name = str(header['FILTER']).strip().split("_", 1)[0]

    date = date.split('T')[0]

    name = date + "_" + filter_name

    return name


def run_swarp(images, config, use_image_center=True, filter_name=None):

    files_list = config.working_dir / f"coaddition_{filter_name}.list"
    name = get_name(images[0], filter_name=filter_name)

    with open(files_list, "w") as f:
        for image in images:
            f.write(f"{image}\n")

    (ra_cent, dec_cent) = get_center(images[0])

    logger.info(f"The central sky coordinates are RA: {ra_cent} and DEC: {dec_cent}")

    # Make it explicit for understanding
    config_swarp = config.configuration_setup.config_swarp
    output_name = name + config.combine.coadded_suffix
    output_file = config.working_dir / output_name
    weight_out_name = name + "_coadd_weight.fits"
    weight_out_file = config.working_dir / weight_out_name

    #object
    if use_image_center:
        ra = ra_cent
        dec = dec_cent
    else:
        ra = str(config.object.ra)
        dec = str(config.object.dec)

    # ccd
    pxscale = str(config.ccd.pxscale)
    gain = str(config.ccd.gain)
    rmnoise = str(config.ccd.rmnoise)
    naxis1 = str(config.ccd.naxis1)
    naxis2 = str(config.ccd.naxis2)
    datamax = str(config.ccd.datamax)
    # align
    resample = config.align.resample
    resample_type = config.align.resampling_type
    resample_suffix = config.align.resample_suffix
    pixel_scale_type = config.align.pixel_scale_type
    subtract_bkg = config.align.subtract_background
    # combine
    coadd = config.combine.coadd
    combine_type = config.combine.combine_type

    # This hack is for making sure we can test both automatic and fixed image size
    if config.align.image_size == "0":
        image_size = str(0)
    elif config.align.image_size == "1":
        image_size = f"{naxis1},{naxis2}"

    cmd = [
        "swarp",
        f"@{files_list}",
        "-c",
        f"{config_swarp}",
        "-IMAGEOUT_NAME",
        output_file,
        "-WEIGHTOUT_NAME",
        weight_out_file,
        "-COMBINE",
        coadd,
        "-COMBINE_TYPE",
        combine_type,
        "-CENTER",
        f"{ra},{dec}",
        "-PIXELSCALE_TYPE",
        pixel_scale_type,
        "-PIXEL_SCALE",
        pxscale,
        "-IMAGE_SIZE",
        image_size,
        "-RESAMPLE",
        resample,
        "-RESAMPLE_SUFFIX",
        resample_suffix,
        "-RESAMPLING_TYPE",
        resample_type,
        "-GAIN_DEFAULT",
        gain,
        "-SATLEV_DEFAULT",
        datamax,
        "-SUBTRACT_BACK",
        subtract_bkg,
        "-RESAMPLE_DIR",
        config.working_dir,
        ]

    logger.info(f"Executing: %s", " ".join(map(str, cmd)))

    subprocess.run(cmd, check=True)

    return output_file
