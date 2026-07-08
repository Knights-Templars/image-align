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