import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy.table import Table

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