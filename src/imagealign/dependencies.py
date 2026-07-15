import shutil


def check_swarp():
    swarp_path = shutil.which("swarp")

    if swarp_path is None:
        raise RuntimeError(
            "Swarp is not installed.\n"
            "Install it using:\n"
            "sudo port install swarp"
        )
    
    return swarp_path


def check_sex():
    sex_path = shutil.which("sex")

    if sex_path is None:
        raise RuntimeError(
            "Sextractor is not installed.\n"
            "Install it using:\n"
            "conda install astromatic-source-extractor"
        )

    return sex_path

def check_scamp():

    scamp_path = shutil.which("scamp")

    if scamp_path is None:
        raise RuntimeError(
            "Scamp is not installed.\n"
            "Install it using:\n"
            "sudo port install scamp"
        )

    return scamp_path