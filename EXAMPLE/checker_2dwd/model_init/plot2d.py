#!/usr/bin/env python

import sys
from os.path import exists

import numpy as np
import pylab
import scipy.interpolate


def read_fortran(filename):
    """ Reads Fortran style binary data and returns a numpy array.
    """
    with open(filename, 'rb') as f:
        # read size of record
        f.seek(0)
        n = np.fromfile(f, dtype='int32', count=1)[0]

        # read contents of record
        f.seek(4)
        v = np.fromfile(f, dtype='float32')

    return v[:-1]


def mesh2grid(v, x, z):
    """ Interpolates from an unstructured coordinates (mesh) to a structured 
        coordinates (grid)
    """
    lx = x.max() - x.min()
    lz = z.max() - z.min()
    nn = v.size
    mesh = _stack(x, z)

    nx = np.around(np.sqrt(nn*lx/lz))
    nz = np.around(np.sqrt(nn*lz/lx))
    dx = lx/nx
    dz = lz/nz

    # construct structured grid
    x = np.linspace(x.min(), x.max(), nx)
    z = np.linspace(z.min(), z.max(), nz)
    X, Z = np.meshgrid(x, z)
    grid = _stack(X.flatten(), Z.flatten())

    # interpolate to structured grid
    V = scipy.interpolate.griddata(mesh, v, grid, 'linear')

    # workaround edge issues
    if np.any(np.isnan(V)):
        W = scipy.interpolate.griddata(mesh, v, grid, 'nearest')
        for i in np.where(np.isnan(V)):
            V[i] = W[i]

    return np.reshape(V, (nz, nx))
    


def _stack(*args):
    return np.column_stack(args)



if __name__ == '__main__':
    """ Plots data on 2-D unstructured mesh

      Can be used to plot models or kernels created by SPECFEM2D

      SYNTAX
          plot2d  x_coords_file  z_coords_file  database_file
    """

    # parse command line arguments
    x_coords_file = sys.argv[1]
    z_coords_file = sys.argv[2]
    database_file = sys.argv[3]

    # check filenames conform to SPECFEM2D naming convention
    assert 'proc000000_x.bin' in x_coords_file
    assert 'proc000000_z.bin' in z_coords_file
    assert 'proc000000_' in database_file

    # check that files actually exist
    assert exists(x_coords_file)
    assert exists(z_coords_file)
    assert exists(database_file)

    # read mesh coordinates
    #try:
    if True:
        x = read_fortran(x_coords_file)
        z = read_fortran(z_coords_file)
    #except:
    #    raise Exception('Error reading mesh coordinates.')

    # read database file
    try:
        v = read_fortran(database_file)
    except:
        raise Exception('Error reading database file: %s' % database_file)

    # check mesh dimensions
    assert x.shape == z.shape == v.shape, 'Inconsistent mesh dimensions.'


    # interpolate to uniform rectangular grid
    V = mesh2grid(v, x, z)

    # display figure
    pylab.pcolor(V)
    pylab.show()

