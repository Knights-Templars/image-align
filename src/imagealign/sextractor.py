import subprocess
from pathlib import Path
import logging

logger = logging.getLogger("imagealign")

def run_sextractor(images, config):

    files_list = config.working_dir / "imagelist.list"

    with open(files_list, "w") as f:
        for image in images:
            f.write(f"{image}\n")


    config_sex = config.configuration_setup.config_sex
    param_sex = config.configuration_setup.param_sex

    pxscale = str(config.ccd.pxscale)
    gain = str(config.ccd.gain)

    for image_name in images:

        catalog_name = config.working_dir / f"{image_name}"
        cmd = [
            "sex",
            image_name,
            "-c",
            config_sex,
            "-CATALOG_NAME",
            catalog_name,
            "-CATALOG_TYPE",
            "FITS_LDAC",
            "-PARAMETERS_NAME",
            param_sex,
            "-MAG_ZEROPOINT",
            "25.0",
            "-GAIN",
            gain,
            "-PIXEL_SCALE",
            pxscale
        ]

        subprocess.run(cmd, check=True)
        logger.info(f"Executing: %s", " ".join(map(str, cmd)))   

