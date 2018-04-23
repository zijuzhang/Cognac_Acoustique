# encoding: utf-8
'''
Useful functions to analyze roms simulations
'''


import sys
from glob import glob

from netCDF4 import Dataset

import numpy as np
import xarray as xr
import warnings




def minmax(x,xname):
    print(xname+' min= %.3f, max=%.3f'%(x.min(),x.max()))
    
    

#--------------------------------------------------------------------------------------------

class grid(object):
    
    
    def __init__(self, datadir='/home/datawork-lops-osi/jgula/NESED/', hgrid_file=None, verbose=1):
        
        self._verbose = verbose
        
        self._datadir = datadir
        
        self._load_hgrid(hgrid_file=hgrid_file)
        self._load_vgrid()
        
        self.__str__()

    def __str__(self):
        #
        print('-- Grid object')
        #
        print('dim lon_rho: %i  %i' %self['lon_rho'].shape)
        minmax(self['lon_rho'],'lon_rho')
        minmax(self['lat_rho'],'lat_rho')
        minmax(self['h'],'h')
        #
        if self._verbose > 1:
            print('Lxi = %f km, Leta = %f km' %(self.Lxi/1e3, self.Leta/1e3) )
        
    def __getitem__(self,item):
        """Returns a grid object restricted to a subdomain.

        Use slicing with caution, this functionnality depends on the order of
        the dimensions in the netcdf files.

        Parameters
        ----------
        item : slice, str
            item can be a slice for restricting the grid to a subdomain
            or a string in which case, a xarray grid variable is returned

        Returns
        -------
        out :  new grid object

        Example
        -------
        for restricting the grid to a subdomain :
        >>> new_grd = grd[100:200,300:500]

        """

        if isinstance(item,slice) \
            or isinstance(item, tuple) and all([isinstance(i, slice) for i in item]):
            
            ij = item
            
            import copy
            print('-- Generate a subset of the original grid')
            returned = copy.copy(self)
            returned.ij = ij
            print(ij)
            # update
            returned._ds = returned._ds.isel(eta_rho=ij[0], xi_rho=ij[1])
            #returned.lon_rho = returned.lon_rho[ij]
            #returned.lat_rho = returned.lat_rho[ij]
            #returned.h = returned.h[ij]
            #
            returned.Lp = returned['lon_rho'].shape[1]
            returned.Mp = returned['lon_rho'].shape[0]        
            #
            returned._update_hextent()
            #
            returned.__str__()

            return returned
        
        elif isinstance(item,str):
            return self._ds[item]
            
        else:
            return None
        

    def _load_hgrid(self,hgrid_file=None):
        ''' load horizontal grid variables
        '''
        if hgrid_file is None:
            # search for files
            hgrid_file = glob(self._datadir+'*grd.nc')
            if len(hgrid_file)==0:
                print('No grid file found in'+self._datadir)
                sys.exit()
            else:
                if self._verbose > 0 : 
                    print('%i grid file found, uses: %s'%(len(hgrid_file),hgrid_file[0]))
                hgrid_file = hgrid_file[0]
        # open and load variables
        ds = xr.open_dataset(hgrid_file)
        self._ds = ds
        #self.lon_rho = ds['lon_rho']
        #self.lat_rho = ds['lat_rho']
        #self.h = ds['h']
        #
        self.Lp = self['lon_rho'].shape[1]
        self.Mp = self['lon_rho'].shape[0]
        #
        self._update_hextent()
        
    def _update_hextent(self):
        ''' Compute the lengths of southern and western boundaries
        '''
        self.hextent = [self['lon_rho'].min(), self['lon_rho'].max(), \
                        self['lat_rho'].min(), self['lat_rho'].max()]
        self.Lxi = (1./self._ds['pm'][0,:]).sum()
        self.Leta = (1./self._ds['pn'][:,0]).sum()


    def _load_vgrid(self):
        ''' load vertical grid variables
        '''
        # search for files with 
        files = glob(self._datadir+'*.nc')
        if len(files)==0:
            print('No nc file found in'+self._datadir)
            sys.exit()
        for lfile in files:
            ds = xr.open_dataset(lfile)
            ds.coords['s_rho'] = ds.attrs['sc_r']
            ds.coords['s_w'] = ds.attrs['sc_w']
            ds['Cs_w'] = xr.DataArray(ds.attrs['Cs_w'], coords=[ds['s_w']])
            ds['Cs_r'] = xr.DataArray(ds.attrs['Cs_r'], coords=[ds['s_rho']])
            #print(ds)
            if 'sc_w' in ds.attrs:
                if self._verbose > 1:
                    print('vertical grid parameters found in %s'%(lfile))
                break
            else:
                ds.close()
        self.hc = ds.attrs['hc']
        #self.sc_w = ds.attrs['sc_w']
        #self.Cs_w = ds.attrs['Cs_w']
        #self.sc_r = ds.attrs['sc_r']
        #self.Cs_r = ds.attrs['Cs_r']
        self.sc_w = ds['s_w']
        self.Cs_w = ds['Cs_w']
        self.sc_r = ds['s_rho']
        self.Cs_r = ds['Cs_r']
        #self.z_r = z_r()
        self._ds = xr.merge([self._ds, ds['Cs_w'], ds['Cs_r']])

    def get_z(self, zeta, h, sc=None, cs=None):
        ''' compute vertical coordinates
            zeta should have the size of the final output
            vertical coordinate should be first
        '''
        if sc is None:
            sc=self['s_rho']
        if cs is None:
            cs=self['Cs_r']
        z0 = (self.hc * sc + h * cs) / (self.hc + h)
        z = zeta + (zeta + h) * z0
        # manually swap dims, could also perform align with T,S
        if z.ndim == 3:
            z = z.transpose(sc.name, zeta.dims[0], zeta.dims[1])
        elif z.ndim == 2:
            z = z.transpose(sc.name, zeta.dims[0])            
        return z

    def plot_domain(self,ax,**kwargs):
        ''' plot the domain bounding box
        '''
        #dlon = self.lon_rho[[0,0,-1,-1,0],[0,-1,-1,0,0]]
        #dlat = self.lat_rho[[0,0,-1,-1,0],[0,-1,-1,0,0]]
        dlon = np.hstack((self['lon_rho'][0:-1,0],self['lon_rho'][-1,0:-1], \
                        self['lon_rho'][-1:0:-1,-1],self['lon_rho'][0,-1:0:-1]))
        dlon[np.where(dlon>180)]=dlon[np.where(dlon>180)]-360
        dlat = np.hstack((self['lat_rho'][0:-1,0],self['lat_rho'][-1,0:-1], \
                        self['lat_rho'][-1:0:-1,-1],self['lat_rho'][0,-1:0:-1]))
        ax.plot(dlon,dlat,**kwargs)

    def plot_xz(self,ax,x,z,toplt,**kwargs):
        x = (x[:,1:]-x[:,:-1])*.5
        toplt = np.hstack((toplt,toplt[-1,:]))
        toplt = np.vstack((toplt,toplt[-1,:]))
        im = ax.pcolormesh(x,z,toplt,**kwargs)
        return im
        
def interp2z_1d(z0, z, v):
    ''' Interpolate on a horizontally uniform grid
    '''
    from scipy.interpolate import interp1d
    return interp1d(z,v, kind='cubic')(z0)

def interp2z(z0, z, v):
    ''' Interpolate on a horizontally uniform grid
    '''
    import clib.fast_interp3D as fi  # OpenMP accelerated C based interpolator
    if v.ndim == 1 or z.ndim == 1 :
        v = v.squeeze()
        z = z.squeeze()
        return fi.interp(z0.astype('float64'),z[:,None,None].astype('float64'),
                         v[:,None,None])
    elif v.ndim == 2 :
        return fi.interp(z0.astype('float64'),z[...,None].astype('float64'),
                         v[...,None])
    else:
        # assumes input files are indeed 3D
        return fi.interp(z0.astype('float64'), z.astype('float64'), v)


#--------------------------------------------------------------------------------------------
def get_soundc(t, s, z, lon, lat):
    ''' compute sound velocity
    '''
    import gsw
    latm = np.mean(lat)
    lonm = np.mean(lon)
    #
    p = gsw.p_from_z(z,latm)
    SA = gsw.SA_from_SP(s, p, lonm, latm)
    CT = gsw.CT_from_pt(SA,t)
    c = gsw.sound_speed(s,t,p)
    # inputs are: SA (absolute salinity) and CT (conservative temperature)
    return c
    
    
def earth_dist(lon, lat):
    deg2m=111.e3
    dlon = np.diff(lon)*np.cos(np.pi/180.*np.mean(lat))
    dlat = np.diff(lat)
    return deg2m * np.sqrt( dlon**2 + dlat**2 )


    
    