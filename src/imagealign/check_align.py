import numpy as np
from pathlib import Path
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.stats import sigma_clipped_stats
import matplotlib.pyplot as plt
import logging
from .sextractor import run_sextractor
from .util import get_table_from_ldac
from .util import read_data

logger = logging.getLogger("imagealign")


def check_alignment(images, config):

    logger.info("Running Sextractor on resampled images")
    logger.info(f"Collected {len(images)} files.")
    run_sextractor(images, config)

    resampled_ldacs =  list(sorted(config.working_dir.glob("*_resample.fits.ldac")))
    logger.info(f"Collected {len(resampled_ldacs)} ldac files after resampling.")

    files_list = config.working_dir / "resampled.list"

    with open(files_list, "w") as f:
        for ldac in resampled_ldacs:
            f.write(f"{ldac}\n")

    # Read the gaia catalog
    gaia_catalog = get_table_from_ldac(config.working_dir / 'gaiacatalog.ldac')

    
    for ldac_file, image in zip(resampled_ldacs, images):


        sourcetable = get_table_from_ldac(ldac_file)

        data, header = read_data(image)

        w= WCS(header)

        gaia_x, gaia_y = w.all_world2pix(
            gaia_catalog['ra'],
            gaia_catalog['dec'],
            1
        )

        clean_gaia_sources = gaia_catalog[(
            (gaia_x > 200) &
            (gaia_x < data.shape[1] - 200) &
            (gaia_y > 200) &
            (gaia_y < data.shape[0] - 200)
        )]


        cleansourcetable = sourcetable[
            (sourcetable['FLAGS']==0) &
            (sourcetable['FWHM_WORLD'] < 3) &
            (sourcetable['ELLIPTICITY'] < 0.5)
        ]


        imagecoords = SkyCoord(
            ra=cleansourcetable['X_WORLD'],
            dec=cleansourcetable['Y_WORLD'],
            unit="degree"
        )

        gaiacoords = SkyCoord(
            ra=clean_gaia_sources['ra'],
            dec=clean_gaia_sources['dec'],
            unit='degree'
        )

        idx_image, idx_gaia, _, _ = gaiacoords.search_around_sky(imagecoords,
                                                                 1.0*u.arcsec)
        
        logger.info(f"Found {len(idx_image)} within {1/config.ccd.pxscale} pixels")

        delta_ra = np.array(clean_gaia_sources['ra'][idx_gaia] - cleansourcetable['X_WORLD'][idx_image])
        delta_dec = np.array(clean_gaia_sources['dec'][idx_gaia] - cleansourcetable['Y_WORLD'][idx_image])


        delta_ra_mean, delta_ra_med, delta_ra_std = sigma_clipped_stats(delta_ra)
        delta_dec_mean, delta_dec_med, delta_dec_std = sigma_clipped_stats(delta_dec)

        logger.info(
            f"Std. dev in RA for {image} is: {delta_ra_std * 3600} arcsec"
            f"Std. dev in DEC for {image} is: {delta_dec_std * 3600} arcsec"
        )

        fig, ax = plt.subplots(1, 2, figsize=(12, 5))

        ax[0].hist(delta_ra, bins=50)
        ax[0].axvline(0, linestyle="--")
        ax[0].set_xlabel(r"$\Delta$RA (arcsec)")
        ax[0].set_ylabel("Number of stars")

        ax[1].hist(delta_dec, bins=50)
        ax[1].axvline(0, linestyle="--")
        ax[1].set_xlabel(r"$\Delta$DEC (arcsec)")
        ax[1].set_ylabel("Number of stars")

        plot_name = config.working_dir / image
        plt.tight_layout()
        plt.savefig(f"{plot_name}.png")

        # Quiver Plot


        plt.figure(figsize=(6, 6))
        plt.quiver(
            cleansourcetable['X_WORLD'][idx_image],
            cleansourcetable['Y_WORLD'][idx_image],
            delta_ra,
            delta_dec,
            angles='xy',
            scale_units='xy',
            scale=1
        )

        plt.xlabel("RA (deg)")
        plt.ylabel("DEC (deg)")
        plt.title("Astrometric residual vectors")
        plt.tight_layout()
        plt.savefig(f"{plot_name}_quiver.png")


