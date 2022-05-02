
WORKFLOW='inversion'    # inversion, migration
SOLVER='specfem2d'      # specfem2d, specfem3d
#SYSTEM='serial'         # serial, pbs, slurm,multicore
SYSTEM='multicore'         # serial, pbs, slurm,multicore
NPROCMAX=20
OPTIMIZE='LBFGS'        # NLCG, LBFGS
#PREPROCESS='base'       # base
PREPROCESS='dispersion'       # base
POSTPROCESS='base'      # base

#MISFIT='Waveform'
MISFIT='dispersion'
MATERIALS='Elastic'
DENSITY='Constant'


# WORKFLOW
BEGIN=1                 # first iteration
END=80                   # last iteration
NREC=100               # number of receivers
NSRC=20                 # number of sources
SAVEGRADIENT=1          # save gradient how often
SAVERESIDUALS=1
SAVETRACES= 1
# PREPROCESSING
FORMAT='su'             # data file format
CHANNELS='z'            # data channels
NORMALIZE=0             # normalize
BANDPASS=0              # bandpass
FREQLO=0.               # low frequency corner
FREQHI=0.               # high frequency corner
MUTECONST=0.            # mute constant
MUTESLOPE=0.            # mute slope
NORMALIZE='NormalizeTracesMAX'            #'NormalizeTracesMAX'

MUTE=''                  # mute direct arrival
#MUTE='MuteLongOffsets' #,'MuteShortOffsets'
MUTE_SHORT_OFFSETS_DIST = 50.
#MUTE_LONG_OFFSETS_DIST= 50.

# DISPERSION
FMIN = 20.00
FMAX = 80.00
DX = 2
MINREC = 12
DF = 1.5
DK = 0.0001


# POSTPROCESSING
HESSIAN1=''     # precondition
#SMOOTH=4.              # smoothing radius
SMOOTH=4.              # smoothing radius
SCALE=6.0e6             # scaling factor


# OPTIMIZATION
PRECOND=None            # preconditioner type
STEPMAX=10              # maximum trial steps
STEPTHRESH=0.1          # step length safeguard


# SOLVER
NT=3000                 # number of time steps
DT=0.0001                 # time step
F0=30                # dominant frequency


# SYSTEM
NTASK=1                # must satisfy 1 <= NTASK <= NSRC
NPROC=1                 # processors per task

