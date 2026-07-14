from astroquery.gaia import Gaia
import logging
from astropy.table import Table
from astropy.io import ascii
from .util import save_table_as_ldac

logger = logging.getLogger("imagealign")

def query_gaia_catalog(ra: float,
                       dec: float,
                       radius_deg: float,
                       min_mag: float,
                       max_mag: float) -> Table:
    

    logger.info(f"Querying Gaia DR3 at RA=%.6f DEC=%.6f Radius=%.3f deg", ra, dec, radius_deg)


    query = f"""

    SELECT 
        g.source_id,
        g.ra,
        g.dec,
        g.ra_error,
        g.dec_error,
        g.pmra,
        g.pmdec,
        ps1.r_mean_psf_mag,
        ps1.r_mean_psf_mag_error
    
    FROM gaiadr3.gaia_source AS g
    JOIN gaiadr3.panstarrs1_best_neighbour AS pbest
      ON g.source_id = pbest.source_id
    JOIN gaiadr2.panstarrs1_original_valid AS ps1
      ON pbest.original_ext_source_id = ps1.obj_id

    WHERE
        CONTAINS(
        POINT('ICRS', g.ra, g.dec),
        CIRCLE('ICRS', {ra}, {dec}, {radius_deg})
        ) = 1

        AND ps1.r_mean_psf_mag BETWEEN {min_mag} AND {max_mag}
        AND ABS(g.pmra) < 40
        AND ABS(g.pmdec) < 40
        AND g.pmra IS NOT NULL
        AND g.pmdec IS NOT NULL

        AND ps1.n_detections > 6
        AND pbest.number_of_mates = 0
        AND pbest.number_of_neighbours = 1

    """

    job = Gaia.launch_job_async(query)
    catalog = job.get_results()

    # convert RA and DEC errors from mas to degrees

    catalog['ra_errdeg'] = catalog['ra_error'] / 3.6e6
    catalog['dec_errdeg'] = catalog['dec_error'] / 3.6e6
    catalog["FLAGS"] = 0

    logger.info("Retrieved %d Gaia sources", len(catalog))

    return catalog


def save_catalog(ra, dec, radius_deg, min_mag, max_mag, catname):

    catalog = query_gaia_catalog(
        ra, 
        dec,
        radius_deg,
        min_mag,
        max_mag,
    )

    ascii.write(catalog,
                catname / 'gaiacatalog.txt',
                overwrite=True)
    
    save_table_as_ldac(
        catalog,
        catname / 'gaiacatalog.ldac'
    )
