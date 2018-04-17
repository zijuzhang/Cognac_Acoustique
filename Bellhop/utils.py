from pathlib import Path
import numpy as np 
import matplotlib.pyplot as plt
import scipy.io as sio


class bellhop(object):
    ''' bellhop class, contains simulations parameters, generates input files,
    read output files and plot results
    '''
    
    
    def __init__(self, SSP, **kwargs):
        '''
        Parameters
        ----------
        SSP : dic
            Sound speed profile key and file 
            (example : {'p1': './SSP_4profils.mat'})
        '''
    
        zmax = 2550.
        rmax = 35.
        simu = 'simulation'
        self.params = {'name': simu, 'freq': 8000., \
                       'zs': 50., 'zmax': zmax, \
                       'rmax': rmax, 'NDepth': zmax + 1., \
                       'NRange': rmax * 100. + 1., \
                       'ALimites': [-20., 20.], 'file_type': 'R'}
        self.params.update(kwargs)
        self.params['file_bathy'] = self.params['name']+'.bty'
        self.params['file_env'] = self.params['name']+'.env'
        self.params['file_ssp'] = self.params['name']+'.ssp'   # range dependent SSP
        #
        self.SSP = {}
        self.load_SSP(SSP)
        

        
        
    def load_SSP(self, SSP_dict):
        '''
        Parameters
        ----------
        SSP_dict : dic
            Sound speed profile key and file
        '''
        
        for ssp_key, file in SSP_dict.items():
            if '.mat' in file:
                D = sio.loadmat(file)
                self.SSP[ssp_key] = {'c': D['SSP_Dr1m'], 'depth': D['Depthr'][0,:]}
                
        
        
        
    def generate_envfile(self, ssp_key, Issp=0, file_env=None):
        ''' 
        Parameters
        ----------
        ssp_key: str
            Key referencing which sound speed profile should be used
        Issp : int
            Sound speed profile index in SSP file
        file_env : str
            Name of the env file to generate (.env)
        '''
        
       
        # name of the environnement file
        if file_env is None:
            file_env = self.params['file_env']
        print('Output file is : '+file_env)
            
        # load sound speed profile
        c = self.SSP[ssp_key]['c'][Issp,:]
        depth = self.SSP[ssp_key]['depth'][:]

        # Create environment file
        with open(file_env, 'w') as f:
            f.write('\'Range dep, Gaussian beams\'\n')
            f.write('%.1f\n' % self.params['freq'])
            f.write('%.d\n' %1)
            f.write('\'SVWT\'\n')
            #
            depth_max = depth.max() # ! Bathymetrie maximale
            f.write('%d %.1f %.1f\n'%(0, 0.0, depth_max))
            for i in range(0,len(depth),5):
                f.write('%.1f %.1f /\n' %(depth[i], c[i]))
            #
            f.write('\'A*\' %.1f\n' %0.0)
            f.write('%.1f %.1f %.1f %.1f %.1f %.1f\n'%(depth_max,1800,10,2,0.1,0)) #gravier
            #
            f.write('%d \t  !NSD\n' %1)
            f.write('%d / \t  !Source depth\n' % self.params['zs'])
            f.write('%d \t  !Number receiver depth\n' % self.params['NDepth'])
            f.write('%.1f %.1f / \t  !Receiver depths\n' %(0.0, self.params['zmax']))

            f.write('%d \t  !Number of ranges\n' % self.params['NRange'])
            f.write('%.1f  %.1f / \t  !Range limites\n'%(0., self.params['rmax']))
            f.write('\'%s\'\n' %self.params['file_type'])  # R : .ray ; IB : .shd
            #f.write('\'IB\'\n')            #! On choisit de travailler en champ incoherent
            f.write('%d  \t  !NBeams\n'%0)      #! Bellhop calcule le nombre optimal de rayons
            f.write('%.1f  %.1f  / \t  !Angles limites\n' %( 
                self.params['ALimites'][0],self.params['ALimites'][1]))
            f.write('%.1f  %.1f  %.1f \t  !Steps zbox(m) rbox(km)\n' %(
                0.0,self.params['zmax']+450,self.params['rmax']+1.))


            
            
    def plotray (self, filename = None):
        ''' 
        Parameters
        ----------
        filename : str
            Output file from bellhop simulation (.ray) 
        '''
        
        if filename is None :
            filename = self.params['name']+'.ray'
            
        file = Path("./%s" %filename)
        if not file.is_file():
            print("Le fichier %s n'exite pas dans ce répertoire." %filename)
            return

        Nsxyz       = np.zeros(3) 
        NBeamAngles = np.zeros(2)

        fid = open(filename,'r')
        title = fid.readline()
        freq  = float( fid.readline() )
        theline = str( fid.readline() )
        datai = theline.split()
        Nsxyz[0] = int( datai[0] )
        Nsxyz[1] = int( datai[1] )
        Nsxyz[2] = int( datai[2] )
        theline = str( fid.readline() )
        datai = theline.split()
        NBeamAngles[0] = int( datai[0] )
        NBeamAngles[1] = int( datai[1] )
        DEPTHT = float( fid.readline() )
        DEPTHB = float( fid.readline() )
        Type   = fid.readline()
        Nsx = int( Nsxyz[0] )
        Nsy = int( Nsxyz[1] )
        Nsz = int( Nsxyz[2] )
        Nalpha = int( NBeamAngles[0] )
        Nbeta  = int( NBeamAngles[1] )
        # axis limits
        rmin =  1.0e9
        rmax = -1.0e9
        zmin =  1.0e9
        zmax = -1.0e9

        #plt.figure(figsize=(9,6))

        for isz in range(Nsz):
            for ibeam in range(Nalpha):
                theline = str( fid.readline() )
                l = len( theline )
                if l > 0:
                   alpha0 = float( theline )
                   theline = str( fid.readline() )
                   datai = theline.split()
                   nsteps    = int( datai[0] )
                   NumTopBnc = int( datai[1] )
                   NumBotBnc = int( datai[2] )
                   r = np.zeros(nsteps)
                   z = np.zeros(nsteps)
                   for j in range(nsteps):
                       theline = str(fid.readline())
                       rz = theline.split()
                       r[j] = float( rz[0] )
                       z[j] = float( rz[1] )        
                   rmin = min( [ min(r), rmin ] )
                   rmax = max( [ max(r), rmax ] )
                   zmin = min( [ min(z), zmin ] )
                   zmax = max( [ max(z), zmax ] )

                   ## Color of the ray
                   #RED : no reflexion on top and bottom
                   if np.logical_and (NumTopBnc==0, NumBotBnc==0):
                        color = 'r'
                   #BLUE : no reflexion on bottom
                   elif NumBotBnc==0 :
                        color = 'b'
                   #BLACK : reflexion on top and bottom
                   else : 
                        color = 'k'

                   ## plot  
                   plt.plot( r, -z,  color = color )
                   plt.axis([rmin,rmax,-zmax,-zmin])


        plt.title(filename[:-4])
        plt.xlabel('range (m)')
        plt.ylabel('profondeur (m)')
        #plt.savefig('plotray_'+filename[:-4], dpi=100)

        fid.close()

        
        
       
    def plotshd(self, filename=None):
        ''' 
        Parameters
        ----------
        filename : str
            Output file from bellhop simulation (.shd)
        '''
        
        if filename is None :            
            filename = self.params['name']+'.shd'
            
        file = Path("./%s" %filename)
        if not file.is_file():
            print("Le fichier %s n'exite pas." %filename)
            return
              
           
        ###### READ file #######  
        
        fid = open(filename,'rb')
        recl  = int( np.fromfile( fid, np.int32, 1 ) )
        title = fid.read(80)
        fid.seek( 4*recl )
        PlotType = fid.read(10)
        fid.seek( 2*4*recl ); # reposition to end of second record
        Nfreq  = int(   np.fromfile( fid, np.int32  , 1 ) )
        Ntheta = int(   np.fromfile( fid, np.int32  , 1 ) )
        Nsx    = int(   np.fromfile( fid, np.int32  , 1 ) )
        Nsy    = int(   np.fromfile( fid, np.int32  , 1 ) )
        Nsd    = int(   np.fromfile( fid, np.int32  , 1 ) )
        Nrd    = int(   np.fromfile( fid, np.int32  , 1 ) )
        Nrr    = int(   np.fromfile( fid, np.int32  , 1 ) ) 
        atten  = float( np.fromfile( fid, np.float32, 1 ) )
        fid.seek( 3 * 4 * recl ); # reposition to end of record 3
        freqVec = np.fromfile( fid, np.float32, Nfreq  )
        fid.seek( 4 * 4 * recl ); # reposition to end of record 4
        thetas  = np.fromfile( fid, np.float32, Ntheta )
        if  ( PlotType[ 0 : 1 ] != 'TL' ):
            fid.seek( 5 * 4 * recl ); # reposition to end of record 4
            Xs     = np.fromfile( fid, np.float32, Nsx )
            fid.seek( 6 * 4 * recl );  # reposition to end of record 5
            Ys     = np.fromfile( fid, np.float32, Nsy )
        else:   # compressed format for TL from FIELD3D
            fid.seek( 5 * 4 * recl ); # reposition to end of record 4
            Pos_S_x     = np.fromfile( fid, np.float32, 2 )
            Xs          = np.linspace( Pos_S_x[0], Pos_S_x[1], Nsx )
            fid.seek( 6 * 4 * recl ); # reposition to end of record 5
            Pos_S_y     = np.fromfile( fid, np.float32, 2 )
            Ys          = np.linspace( Pos_S_y[0], Pos_S_y[1], Nsy )
        fid.seek( 7 * 4 * recl ) # reposition to end of record 6
        zs = np.fromfile( fid, np.float32, Nsd )
        fid.seek( 8 * 4 * recl ) # reposition to end of record 7
        zarray =  np.fromfile( fid, np.float32, Nrd )
        fid.seek( 9 * 4 * recl ) # reposition to end of record 8
        rarray =  np.fromfile( fid, np.float32, Nrr )
        if PlotType == 'rectilin  ':
            pressure = np.zeros( (Ntheta, Nsd, Nrd, Nrr) ) + 1j*np.zeros( (Ntheta, Nsd, Nrd, Nrr) )
            Nrcvrs_per_range = Nrd
        elif PlotType == 'irregular ':
            pressure = np.zeros( (Ntheta, Nsd,   1, Nrr) ) + 1j*np.zeros( (Ntheta, Nsd, Nrd, Nrr) )
            Nrcvrs_per_range = 1
        else:
            pressure = np.zeros( (Ntheta, Nsd, Nrd, Nrr) )
            Nrcvrs_per_range = Nrd
        pressure = np.zeros( (Ntheta,Nsd,Nrcvrs_per_range,Nrr) ) + 1j*np.zeros(    (Ntheta,Nsd,Nrcvrs_per_range,Nrr) )
    
        for itheta in range(Ntheta):
            for isd in range( Nsd ):
                for ird in range( Nrcvrs_per_range ):
                    recnum = 10 + itheta * Nsd * Nrcvrs_per_range + isd * Nrcvrs_per_range + ird
                    status = fid.seek( recnum * 4 * recl ) # Move to end of previous record    
                    if ( status == -1 ):
                        print ('Seek to specified record failed in readshd...')
                    temp = np.fromfile( fid, np.float32, 2 * Nrr ) # Read complex data
                    for k in range(Nrr):
                        pressure[ itheta, isd, ird, k ] = temp[ 2 * k ] + 1j * temp[ 2*k + 1 ]

            fid.close()
            
        geometry = {"zs":zs, "f":freqVec,"thetas":thetas,"rarray":rarray,"zarray":zarray}
          
            
        ###### PLOT transmission loss #######    
            
        # range and depth
        rt = geometry.get ("rarray")
        zt = geometry.get ("zarray")

        # pressure
        P = np.squeeze(pressure).real
        Pabs = abs(P)
        Pabs[np.where(np.isnan(Pabs))] = 1e-6  #remove NaNs
        Pabs[np.where(np.isinf(Pabs))] = 1e-6  #remove infinities
        Pabs[np.where(Pabs<1e-37)] = 1e-37     #remove zeros

        # transmission loss
        TL = -20.0 * np.log10 (Pabs) 

        #statistics to define limits of colorbar
        icount = TL[np.where(Pabs > 1e-37)]       # statistics only on pressure P > 1e-37
        tlmed = np.median (icount)                # median value
        tlstd = np.std(icount)                    # standard deviation
        tlmax = tlmed + 0.75 * tlstd              # max for colorbar
        tlmax = 10 * np.round (tlmax/10)          # make sure the limits are round numbers
        tlmin = tlmax - 50                        # min for colorbar

        # plot TL 
        plt.figure(figsize=(14,4))
        plt.subplot(1,2,1)
        plt.pcolormesh (rt, zt, TL, cmap='jet')
        plt.title (filename[:-4])
        plt.xlabel("range (m)")
        plt.ylabel("depth (m)")
        cbar = plt.colorbar()
        cbar.set_label("TL(dB)")
        plt.clim ([tlmin,tlmax])
        plt.gca().invert_yaxis()
        #plt.savefig('plotshd_'+filename[:-4], dpi=100)    


        # plot TL from 0 to 500m (ZOOM) 
        plt.subplot(1,2,2)
        plt.pcolormesh (rt, zt, TL, cmap='jet')
        plt.title (filename[:-4]+' ZOOM de 0 à 500m')
        plt.xlabel("range (m)")
        plt.ylabel("depth (m)")
        cbar = plt.colorbar()
        cbar.set_label("TL(dB)")
        plt.clim ([tlmin,tlmax])
        plt.axis([0,35000,0,500])
        plt.gca().invert_yaxis()
        #plt.savefig('plotshd_'+filename[:-4]+'_ZOOM', dpi=100)
        
        
  
    
    def plotssp2D (self, filename=None):
        '''
        Parameters
        ----------
        filename: str
            File containing range dependent sound speed profiles (.ssp)    
        '''
        
        if filename is None :           
            filename = self.params['file_ssp']
            
        file = Path("./%s" %filename)
        if not file.is_file():
            print("Le fichier %s n'exite pas dans ce répertoire." %filename)
            return
          

        ### read file ssp
        fid = open(file_SSP,'r')
        
        NProf = int( np.fromfile( fid, float, 1, sep = " " ) )  # number of profiles 
        rProf = np.fromfile( fid, float, NProf, sep = " " )     # range of each profile
        values = np.fromfile (fid, float, -1, sep=" ")          # all the values in .ssp
        n_line = int(len(values)/NProf)                         # number of lines per profile
        cmat = np.zeros((n_line,NProf))                         # sound speed matrix

        for i in range (n_line) :
            cmat[i,:] = values[i*NProf:(i+1)*NProf]

        fid.close()


        ### read file env (to have depths)
        file_env = file_SSP[:-4]+'.env'
        fid = open (file_env,'r')
        f = fid.readlines()

        depth = np.zeros(n_line)     # depths corresponding to profile values
        for i in range(n_line):
            data =f[i+5].split()
            depth[i] =data[0]

        fid.close()


        ### plot ssp2D 
        plt.figure(figsize=(17,8))
        for i in range(NProf):
            plt.subplot (1,NProf,i+1)
            plt.plot(cmat[:,i],depth)
            plt.gca().invert_yaxis()
            plt.title('%d km' %rProf[i])

        #plt.savefig('profiles_'+file_SSP[:-4], dpi=100)

        plt.figure(figsize=(12,8))
        plt.pcolormesh(rProf, depth, cmat, shading='gouraud', cmap ='jet')
        plt.gca().invert_yaxis()
        cbar = plt.colorbar()
        cbar.set_label("sound speed (m/s)")
        plt.title ("Range-dependent SSP - "+file_SSP[:-4])
        plt.xlabel("range (km)")
        plt.ylabel("depth (m)")
        plt.contour(rProf, depth,cmat,10,colors='w',linestyles='dotted')

        #plt.savefig('range-dependent SSP_'+file_SSP[:-4], dpi=100)




