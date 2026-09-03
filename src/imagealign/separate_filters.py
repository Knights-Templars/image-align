"""Utilities for partitioning FITS images by filter."""

from collections import defaultdict
from pathlib import Path

from astropy.io import fits


def separate_by_filter(images):
    """Return input images grouped by their ``FILTER`` header value.

    The order of both the filters and the images within each filter is
    deterministic, which keeps the coaddition runs reproducible.
    """

    groups = defaultdict(list)

    for image in sorted(map(Path, images)):
        filter_name = fits.getheader(image, 0).get("FILTER")
        if filter_name is None or not str(filter_name).strip():
            raise ValueError(f"FILTER keyword missing or empty in {image}")

        # Match the filter naming convention used for SWarp outputs. Some
        # instruments append metadata after an underscore (for example,
        # ``R_BESSEL``); those images still belong to the same passband.
        filter_name = str(filter_name).strip().split("_", 1)[0]
        groups[filter_name].append(image)

    return dict(sorted(groups.items()))
