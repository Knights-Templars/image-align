from astropy.io import fits
from astropy.wcs import WCS


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
