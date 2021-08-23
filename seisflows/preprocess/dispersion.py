import sys
import numpy as np

from os.path import exists
from obspy.core import Stream, Trace

from seisflows.plugins import adjoint, misfit
from seisflows.tools import unix
from seisflows.config import ParameterError, custom_import

PAR = sys.modules['seisflows_parameters']
PATH = sys.modules['seisflows_paths']

system = sys.modules['seisflows_system']


class dispersion(custom_import('preprocess', 'base')):
    """ WD dispersion misfit function's data processing class

      Adds dispersion misfit functions to base class
    """

    def check(self):
        """ Checks parameters, paths, and dependencies
        """
        super(dispersion, self).check()

        assert PAR.MISFIT in [
            'dispersion']
        if 'FMIN' not in PAR:
            raise ParameterError(PAR, 'FMIN')
        if 'FMAX' not in PAR:
            raise ParameterError(PAR, 'FMAN')
        if 'DX' not in PAR:
            raise ParameterError(PAR, 'DX')
        if 'DF' not in PAR:
            raise ParameterError(PAR, 'DF')
        if 'DK' not in PAR:
            raise ParameterError(PAR, 'DK')
        if 'MINREC' not in PAR:
            raise ParameterError(PAR, 'MINREC')
    def write_residuals(self,path,syn,obs):
        """ Computes residuals from observations and synthetics

          INPUT
            PATH - location residuals will be written
            disp_syn - synthetic dispersion data
            disp_obs - observed Dispersion data
        """
        fmin,fmax,dx,minrec,dfpara,dkpara = self.get_dispersion_para()
        self.dispersion_diff=self.calculate_misfit(path,syn,obs,fmin,fmax,dx,minrec,dfpara,dkpara)
        dispersion_diff_1d=self.dispersion_diff.flatten()
        np.savetxt(path+'/'+'dispersion_diff',dispersion_diff_1d)
        residuals = []
        for ii in range(2*self.nfcount):
            residuals.append(np.abs(dispersion_diff_1d[ii]))

        filename = path+'/'+'residuals'
        if exists(filename):
            residuals.extend(list(np.loadtxt(filename)))

        np.savetxt(filename, residuals)

    def write_adjoint_traces(self, path, syn, obs, channel):
        fmin,fmax,dx,minrec,dfpara,_ = self.get_dispersion_para()
        adj = self.calculate_adjoint(path,syn,obs,fmin,fmax,dx,minrec,dfpara)
        self.writer(adj, path, channel)

    def sum_residuals(self,paths):
        """ Sums squares of residuals
        """
        total_misfit = 0.
        for path in paths:
            total_misfit += np.sum(np.loadtxt(path))
        return total_misfit

    def get_receiver_coords_new(self,path,nx):
        #Read STATIONS file from path+'DATA/STATIONS'
        stations = np.genfromtxt(path+'/DATA/STATIONS',dtype=None)
        ntemp = stations.shape
        assert ntemp[0]==nx
        rx=np.zeros(nx)
        rz=np.zeros(nx)
        for ix in range(nx):
            rx[ix] = stations[ix][2]
            rz[ix] = stations[ix][3]
        return rx,rz

    def get_source_coords_new(self, path):
        with open(path+'/DATA/SOURCE','r') as f:
            for line in f.readlines():
                tmp0=line.strip().split('\n')
                tmp1=tmp0[0].split('=')
                tmp2=tmp1[0].split()
                if tmp2[0]=='xs':
                    sx=(float(tmp1[1].split()[0]))
                if tmp2[0]=='zs':
                    sz=(float(tmp1[1].split()[0]))
            return sx,sz

    def get_dist(self,rx,rz,rx1,rz1):
        return(np.sqrt((rx-rx1)**2+(rz-rz1)**2))

    def get_source_ID_and_SR_distance(self,path,nx):
        sx,sz=self.get_source_coords_new(path)
        rx,rz=self.get_receiver_coords_new(path,nx)
        dist = np.zeros(nx)
        angl = np.zeros(nx)
        for ix in range(0,nx):
            dist[ix]=np.sqrt((rx[ix]-sx)**2+(rz[ix]-sz)**2)
            angl[ix]=np.arctan2(rz[ix]-sz,rx[ix]-sx)
        return np.argmin(abs(dist)), dist, angl

    def get_dispersion_para(self):
        fmin = PAR.FMIN
        fmax = PAR.FMAX
        dx = PAR.DX
        df = PAR.DF
        dk = PAR.DK
        minrec = PAR.MINREC
        return fmin, fmax, dx, minrec,df,dk

    def calculate_adjoint(self,path,syn,obs,fmin,fmax,dx,minrec,dfpara):
        nt, dt, _ = self.get_time_scheme(syn)
        nx, _ = self.get_network_size(syn)
        df = 1./(nt*dt)
        ntextend = nt
        if dfpara<df:
            df=dfpara
            ntextend = int(round(1/df/dt))
        nfmin=int(round(fmin/df))
        nfmax=int(round(fmax/df))
        nfcount=nfmax-nfmin+1
        dispersion_diff=self.dispersion_diff
        syn_ft=np.fft.rfft(syn,ntextend)
        syn_ft_adj = np.zeros(syn_ft.shape,np.complex128)
        #syn_ft_adj = syn_ft
        sourceid=self.sourceid 
        dist=self.dist 
        num_rec_left = sourceid 
        num_rec_right = nx-sourceid
        #print ('sourceid=')
        #print (sourceid)
        #print ('left A')
        scal = 0.1
        Areal=np.zeros(nfcount)
        if num_rec_left >= minrec:
            for iff in range(0,nfcount):
                A = 0.
                for ix in range(0,sourceid):
                    A = A - 2*np.pi*dist[ix]**2*syn_ft[ix][iff+nfmin]*np.conjugate(syn_ft[ix][iff+nfmin])
                Areal[iff] = np.real(A)
            factor=scal*max(abs(Areal))
            for iff in range(0,nfcount):
                #print(A)
                #A = -1
                if abs(Areal[iff])>= 0:
                    for ix in range(0,sourceid):
                        syn_ft_adj[ix][iff+nfmin] = (1j*dispersion_diff[1][iff]*dist[ix])*syn_ft[ix][iff+nfmin]/(Areal[iff]-factor)
                        #syn_ft_adj[ix][iff+nfmin] = (1j*dispersion_diff[1][iff]*dist[ix])*syn_ft[ix][iff+nfmin]*(-1)
                
        #print ('right A')
        if num_rec_right >= minrec:
            for iff in range(0,nfcount):
                A = 0.
                for ix in range(sourceid,nx):
                    A = A - 2*np.pi*dist[ix]**2*syn_ft[ix][iff+nfmin]*np.conjugate(syn_ft[ix][iff+nfmin])
                Areal[iff] = np.real(A)
                #print(A)
                #A = -1
            factor=scal*max(abs(Areal))
            for iff in range(0,nfcount):
                if abs(Areal[iff])>= 0:
                    for ix in range(sourceid,nx):
                        syn_ft_adj[ix][iff+nfmin] = (1j*dispersion_diff[0][iff]*dist[ix])*syn_ft[ix][iff+nfmin]/(Areal[iff]-factor)
                        #syn_ft_adj[ix][iff+nfmin] = (1j*dispersion_diff[0][iff]*dist[ix])*syn_ft[ix][iff+nfmin]*(-1)
        adj_temp = np.fft.irfft(syn_ft_adj)
        adj = obs
        for ii in range(nx):
            adj[ii].data = adj_temp[ii][0:nt]
        return adj
        

    def calculate_misfit(self,path,syn,obs,fmin,fmax,dx,minrec,dfpara,dkpara):
        nt, dt, _ = self.get_time_scheme(syn)
        nx, _ = self.get_network_size(syn)
        df = 1./(nt*dt)
        ntextend = nt
        if dfpara<df:
            df=dfpara
            ntextend = int(round(1/df/dt))
        nfmin=int(round(fmin/df))
        nfmax=int(round(fmax/df))
        nfcount=nfmax-nfmin+1
        self.nfcount=nfcount
        dispersion_diff=np.zeros((2,nfcount))

        syn_ft=np.fft.rfft(syn,ntextend)
        obs_ft=np.fft.rfft(obs,ntextend)
        sourceid,dist,angl = self.get_source_ID_and_SR_distance(path,nx)
        self.sourceid = sourceid
        self.dist = dist
        num_rec_left = sourceid 
        num_rec_right = nx-sourceid
        if num_rec_left >= minrec:
            dk = 1./(num_rec_left*dx)
            nxextend = num_rec_left
            if dkpara<dk:
                dk=dkpara
                nxextend = int(round(1/dk/dx))
            for iff in range(0,nfcount):
                syn_ft_fx = np.fft.fft(syn_ft[sourceid-1::-1,iff+nfmin],nxextend)
                obs_ft_fx = np.fft.fft(obs_ft[sourceid-1::-1,iff+nfmin],nxextend)
                phicon=np.real(np.correlate(obs_ft_fx,syn_ft_fx,"full"))
                #phicon = (np.correlate(abs(obs_ft_fx),abs(syn_ft_fx),"full"))
                #phicon=np.imag(np.correlate(obs_ft_fx,syn_ft_fx,"full"))
                dispersion_diff[1][iff] = (np.argmax(phicon)-nxextend+1)*dk
        if num_rec_right >= minrec:
            dk = 1./(num_rec_right*dx)
            nxextend = num_rec_right
            if dkpara<dk:
                dk=dkpara
                nxextend = int(round(1/dk/dx))
            for iff in range(0,nfcount):
                syn_ft_fx = np.fft.fft(syn_ft[sourceid:nx,iff+nfmin],nxextend)
                obs_ft_fx = np.fft.fft(obs_ft[sourceid:nx,iff+nfmin],nxextend)
                phicon=np.real(np.correlate(obs_ft_fx,syn_ft_fx,"full"))
                #phicon = (np.correlate(abs(obs_ft_fx),abs(syn_ft_fx),"full"))
                #phicon=np.imag(np.correlate(obs_ft_fx,syn_ft_fx,"full"))
                dispersion_diff[0][iff] = (np.argmax(phicon)-nxextend+1)*dk
        return dispersion_diff
