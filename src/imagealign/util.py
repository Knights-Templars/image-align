import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy.table import Table
from pathlib import Path
import logging

logger = logging.getLogger("imagealign")

def read_data(fitsimage):

    image = fits.open(fitsimage)
    data = image[0].data
    header = image[0].header

    return data, header


def get_center(fitsimage):

    data, header = read_data(fitsimage)

    w = WCS(header)

    ny, nx = data.shape

    x_cent = nx / 2
    y_cent = ny / 2

    ra_cent, dec_cent = w.all_pix2world(x_cent, y_cent, 0)


    return (ra_cent, dec_cent)



def convert_hdu_to_ldac(hdu):
    
    """
    Convert an hdu table to a fits_ldac table
   
    """

    tblhdr = np.array([hdu.header.tostring(',')])
    col1 = fits.Column(name='Field Header Card', array=tblhdr, format='13200A')
    cols = fits.ColDefs([col1])
    tbl1 = fits.BinTableHDU.from_columns(cols)
    tbl1.header['TDIM1'] = '(80, {0})'.format(len(hdu.header))
    tbl1.header['EXTNAME'] = 'LDAC_IMHEAD'
    tbl2 = fits.BinTableHDU(hdu.data)
    tbl2.header['EXTNAME'] = 'LDAC_OBJECTS'
    return (tbl1, tbl2)

def convert_table_to_ldac(tbl):
    
    """
    Convert an astropy table to a fits_ldac
    
    """
    import tempfile
    f = tempfile.NamedTemporaryFile(suffix='.fits', mode='rb+')
    tbl.write(f, format='fits')
    f.seek(0)
    hdulist = fits.open(f, mode='update')
    tbl1, tbl2 = convert_hdu_to_ldac(hdulist[1])
    new_hdulist = [hdulist[0], tbl1, tbl2]
    new_hdulist = fits.HDUList(new_hdulist)
    return new_hdulist

def save_table_as_ldac(tbl, filename, **kwargs):
    
    """
    Save a table as a fits LDAC file
    
    """
    hdulist = convert_table_to_ldac(tbl)
    hdulist.writeto(filename, **kwargs)



def get_table_from_ldac(filename, frame=1):
    
    """
    Load an astropy table from a fits_ldac by frame 
    
    """
    if frame>0:
        frame = frame*2
    tbl = Table.read(filename, hdu=frame)
    return tbl


def copy_header_keywords(
    input_image: str | Path,
    coadd_image: str | Path,
    config,
    filter_name: str | None = None,
):
    """
    Copy selected FITS header keywords from an input image to the
    final coadded image.

    Parameters
    ----------
    input_image : str or Path
        Reference input FITS image.
    coadd_image : str or Path
        Coadded FITS image produced by SWarp.
    keywords : list of str
        Header keywords to copy.
    """


    keywords = [
    "DATE-OBS",
    "OBJECT",
    "FILTER",
    "RA",
    "DEC",
    "RA_DEG",
    "DEC_DEG",
    "UT",
    "GRISM",
    "AIRMASS",
    "TM_START",
    "DATE-AVG",
    "TIME-OBS",
    "EXPOSURE",
    "OBJCTRA",
    "OBJCTDEC",
    "JD",
    "TELESCOP",
    "INSTRUME",
    "DETECTOR",
    "CAMERA",
    "JD-OBS",
    "HJD-OBS",
    "BJD-OBS",
    "AZIMUTH",
    "ALTITUDE",
    "HA",
    "DATE",
    "UT",
    "FWHM",
    "ZMAG",
    "PA"
    ]

    with fits.open(input_image) as hdul_in, fits.open(
        coadd_image, mode="update"
    ) as hdul_out:

        in_hdr = hdul_in[0].header
        out_hdr = hdul_out[0].header

        for key in keywords:
            if key in in_hdr:
                out_hdr[key] = (in_hdr[key], in_hdr.comments[key])
                logger.info("Copied keyword %s = %s", key, in_hdr[key])
            else:
                logger.warning("Keyword %s not found in %s", key, input_image)

        out_hdr["GAIN"] = config.ccd.gain
        out_hdr["RMSNOISE"] = config.ccd.rmnoise
        if filter_name is not None:
            out_hdr["FILTER"] = (filter_name, "Filter of combined images")

        hdul_out.flush()

    logger.info("Finished copying FITS keywords.")




def update_coadd_exptime(images, coadd_file):

    total_exptime = 0.0
    jd_values = []
    observation_metadata = []

    for index, image in enumerate(images, start=1):
        with fits.open(image) as hdul:
            header = hdul[0].header
            exptime = header.get("EXPTIME")
            jd = header.get("JD")
            date_obs = header.get("DATE-OBS")

            observation_metadata.append((index, image, jd, date_obs))

            if exptime is None:
                logger.warning(
                    "EXPTIME missing in %s, skipping",
                    image
                )
            else:
                total_exptime += exptime

            if jd is None:
                logger.warning("JD missing in %s, excluding from MEANJD", image)
            else:
                try:
                    jd_values.append(float(jd))
                except (TypeError, ValueError):
                    logger.warning(
                        "Invalid JD value %r in %s, excluding from MEANJD",
                        jd,
                        image,
                    )

    mean_jd = float(np.mean(jd_values)) if jd_values else None

    with fits.open(coadd_file, mode="update") as hdul:
        hdr = hdul[0].header

        hdr["EXPTIME"] = (
            total_exptime,
            "Total exposure time of combined images"
        )

        hdr["NCOMBINE"] = (
            len(images),
            "Number of images combined"
        )

        if mean_jd is not None:
            hdr["MEANJD"] = (
                mean_jd,
                "Mean JD of the combined images"
            )
        else:
            logger.warning("No valid JD values; MEANJD not written to %s", coadd_file)

        for index, image, jd, date_obs in observation_metadata:
            hdr[f"IMAGE_{index}"] = (
                Path(image).name,
                f"Input image {index} used in coadd",
            )

            if jd is not None:
                hdr[f"JD_{index}"] = (jd, f"JD of input image {index}")
            else:
                logger.warning("JD missing in %s; JD_%d not written", image, index)

            if date_obs is not None:
                hdr[f"DATE_OBS_{index}"] = (
                    date_obs,
                    f"DATE-OBS of input image {index}",
                )
            else:
                logger.warning(
                    "DATE-OBS missing in %s; DATE_OBS_%d not written",
                    image,
                    index,
                )

        hdul.flush()

    logger.info(
        "Updated %s: EXPTIME=%s s, NCOMBINE=%d, MEANJD=%s",
        coadd_file,
        total_exptime,
        len(images),
        mean_jd,
    )
