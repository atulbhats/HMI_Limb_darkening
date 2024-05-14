#!/usr/bin/env python
"""
Program to correct limb darkening in python based on ILD/swwidl
Based on:
    https://hesperia.gsfc.nasa.gov/ssw/gen/idl/solar/darklimb_correct.pro

Coefficients taken from
    Cox, A. N.: Allen's Astrophysical Quantities, Springer, 2000 taken from IDL

Author:  AngelMartinezC
Modified: AtulBhatS
"""


import numpy as np
import matplotlib.pyplot as plt
# from astropy.io import fits
from sunpy.map import Map
import os
# import sys

# Make fonts bigger
plt.rcParams.update({'font.size': 13})

replace = '.fits'

def writefits(image, name='limbcorrect.fits'):
    """
    Function to write data into a fits file. It overrides any former file
    with the same name.
    Parameters:
    ----------
        image `astropy.fits.getdata`: Sunpy/astropy map
    """
    #os.system(f'rm -r {name}')
    name = name.replace(replace,"_noLimbDark.fits")
    image.save(name,overwrite=1)
    return name


def figure(image):
    """
    Función para graficar el mapa
    """
    plt.figure(figsize=(8, 8))
    plt.subplot(projection=image)
    image.plot()
    image.draw_grid()
    plt.title('Image')
    # plt.show()


def darklimb(name):
    """
    Darklimb function:

    It is requiered the files to be in a .FITS file in order to take
    advantage of the Header structure.

    Output:
      Dos arrays: The first image is the corrected array, the second
      one is the original.
    """

    # -------------------------------------------------------------

    def darklimb_u(ll):
        pll = np.array([1.0, ll, ll**2, ll**3, ll**4, ll**5])
        au = -8.9829751
        bu = 0.0069093916
        cu = -1.8144591e-6
        du = 2.2540875e-10
        eu = -1.3389747e-14
        fu = 3.0453572e-19
        a = np.array([au, bu, cu, du, eu, fu])
        ul = sum(a*pll)
        return ul

    def darklimb_v(ll):
        pll = np.array([1.0, ll, ll**2, ll**3, ll**4, ll**5])
        av = 9.2891180
        bv = -0.0062212632
        cv = 1.5788029e-6
        dv = -1.9359644e-10
        ev = 1.1444469e-14
        fv = -2.599494e-19
        a = np.array([av, bv, cv, dv, ev, fv])
        vl = sum(a*pll)
        return vl

    # -------------------------------------------------------------

    # Read data files
    mapa = Map(name)
    data = mapa.data
    head = mapa.meta

    # Parameters needed for the function
    wavelength = head['WAVELNTH']  # Wavelenght
    xcen = head['CRPIX1']  # X center
    ycen = head['CRPIX2']  # Y center
    radius = head['RSUN_OBS']/head['CDELT1']  # Sun radius in pixels
    size = head['NAXIS1']  # X array size
    bzero = head['BZERO']  # For scaling the data
    blank = head['BLANK']  # For scaling the data
    bscale = head['BSCALE']  # For scaling the data

    ll = 1.0*wavelength

    array = 1e4*data/np.max(data)  # Convert data into numpy arrays
    NaNs = np.where(data < -10)
    array[NaNs] = 0  # np.nan  # Make zero all NANs

    # Apply correction
    ul = darklimb_u(ll)
    vl = darklimb_v(ll)

    xarr = np.arange(0, size, 1)  # Make X array
    yarr = np.arange(0, size, 1)  # Make Y array
    xx, yy = np.meshgrid(xarr, yarr)  # Make XY array

    # z: Make array so that the zero center is the center XY
    # Performed in order to make a circle
    z = np.sqrt((xx-xcen)**2 + (yy-ycen)**2)
    # grid: Normalize the circle so that inside radius is the unity
    grid = z/radius
    out = np.where(grid > 1.0)  # Look for the values greater than unity
    grid[out] = 0  # Make zero all those values (Domain of arcsin)

    limbfilt = (1.0 - ul - vl + ul*np.cos(np.arcsin(grid))
                + vl*np.cos(np.arcsin(grid))**2)

    # Final image
    imgout = np.array(array/limbfilt, dtype='uint32')
    mapa.meta["BZERO"] = bzero
    mapa.meta["BLANK"] = blank
    mapa.meta["BSCALE"] = bscale
    imgout *= (int(1e-4*np.nanmax(data)))

    return Map(imgout, mapa.meta), mapa


# name = sys.argv[1]
# corrected, original = darklimb(name)
#
# writefits(corrected)
# print(f'Limb corrected for {name}')


if __name__ == '__main__':

    # Input the string of the original name
    name = './hmi.ic_45s.2014.02.04_03_44_15_TAI.continuum.fits'
    corrected, original = darklimb(name)
    figure(original)
    figure(corrected)
    fname = writefits(corrected,name)
    print(f"Your File has been processed and saved as [{fname}] in the same directory.")
