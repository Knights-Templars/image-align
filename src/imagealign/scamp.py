import subprocess
from pathlib import Path
import logging

logger = logging.getLogger("imagealign")


def run_scamp(image_ldacs, config):


    files_list = config.working_dir / "image_ldacs.list"

    with open(files_list, "w") as f:
        for ldacs in image_ldacs:
            f.write(f"{ldacs}\n")

    # gaia catalog name is hardcoded. 
    catalog_name = config.working_dir / 'gaiacatalog.ldac'
    config_scamp = config.configuration_setup.config_scamp

    cmd = [
        "scamp",
        "-c",
        config_scamp,
        f"@{files_list}",
        "-ASTREFCAT_NAME",
        catalog_name,
        "-REFOUT_CATPATH",
        config.working_dir,
        "-CHECKPLOT_DEV",
        "PDF",
    ]

    logger.info(f"Executing Scamp: %s", " ".join(map(str, cmd)))

    subprocess.run(cmd, check=True)