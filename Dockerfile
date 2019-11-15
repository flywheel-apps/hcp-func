# Creates docker container that runs HCP Pipeline algorithms
#
#

# Uses Ubuntu 16.04 LTS
FROM flywheel/hcp-base:0.1.0_4.0.1

LABEL maintainer="Flywheel <support@flywheel.io>"

#############################################
# FSL 6.0.1 is a part of the base image.  Update the environment variables

# Configure FSL environment
ENV FSLDIR=/usr/share/fsl/6.0
ENV FSL_DIR="${FSLDIR}"
ENV FSLOUTPUTTYPE=NIFTI_GZ
ENV PATH=/usr/share/fsl/6.0/bin:$PATH
ENV FSLMULTIFILEQUIT=TRUE
ENV POSSUMDIR=/usr/share/fsl/6.0
ENV LD_LIBRARY_PATH=/usr/share/fsl/6.0/lib:$LD_LIBRARY_PATH
ENV FSLTCLSH=/usr/bin/tclsh
ENV FSLWISH=/usr/bin/wish

#############################################
# Connectome Workbench 1.3.2 is installed in base image.  Ensure variables are set
# Compatible with HCP v4.0.1

ENV CARET7DIR=/opt/workbench/bin_linux64

#############################################
# HCP Pipelines v4.0.1 are installed in base image. Ensure variables are set

# Set up specific environment variables for the HCP Pipeline
ENV FSL_DIR="${FSLDIR}"
ENV HCPPIPEDIR=/opt/HCP-Pipelines
ENV MSMBINDIR=${HCPPIPEDIR}/MSMBinaries
ENV MSMCONFIGDIR=${HCPPIPEDIR}/MSMConfig
#ENV MATLAB_COMPILER_RUNTIME=/media/myelin/brainmappers/HardDrives/1TB/MATLAB_Runtime/v901
#ENV FSL_FIXDIR=/media/myelin/aahana/fix1.06

#For HCP Pipeline v3.x
ENV MSMBin=${HCPPIPEDIR}/MSMBinaries

ENV HCPPIPEDIR_Templates=${HCPPIPEDIR}/global/templates
ENV HCPPIPEDIR_Bin=${HCPPIPEDIR}/global/binaries
ENV HCPPIPEDIR_Config=${HCPPIPEDIR}/global/config

ENV HCPPIPEDIR_PreFS=${HCPPIPEDIR}/PreFreeSurfer/scripts
ENV HCPPIPEDIR_FS=${HCPPIPEDIR}/FreeSurfer/scripts
ENV HCPPIPEDIR_PostFS=${HCPPIPEDIR}/PostFreeSurfer/scripts
ENV HCPPIPEDIR_fMRISurf=${HCPPIPEDIR}/fMRISurface/scripts
ENV HCPPIPEDIR_fMRIVol=${HCPPIPEDIR}/fMRIVolume/scripts
ENV HCPPIPEDIR_tfMRI=${HCPPIPEDIR}/tfMRI/scripts
ENV HCPPIPEDIR_dMRI=${HCPPIPEDIR}/DiffusionPreprocessing/scripts
ENV HCPPIPEDIR_dMRITract=${HCPPIPEDIR}/DiffusionTractography/scripts
ENV HCPPIPEDIR_Global=${HCPPIPEDIR}/global/scripts
ENV HCPPIPEDIR_tfMRIAnalysis=${HCPPIPEDIR}/TaskfMRIAnalysis/scripts

#try to reduce strangeness from locale and other environment settings
ENV LC_ALL=C
ENV LANGUAGE=C
#POSIXLY_CORRECT currently gets set by many versions of fsl_sub, unfortunately, but at least don't pass it in if the user has it set in their usual environment
RUN unset POSIXLY_CORRECT

#############################################
# FreeSurfer is installed in base image. Ensure environment is set
# 6.0.1 ftp://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/6.0.1/freesurfer-Linux-centos6_x86_64-stable-pub-v6.0.1.tar.gz
# 5.3.0 ftp://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/5.3.0-HCP/freesurfer-Linux-centos4_x86_64-stable-pub-v5.3.0-HCP.tar.gz

# Set up the FreeSurfer environment
ENV OS Linux
ENV FS_OVERRIDE 0
ENV FIX_VERTEX_AREA=
ENV SUBJECTS_DIR /opt/freesurfer/subjects
ENV FSF_OUTPUT_FORMAT nii.gz
ENV MNI_DIR /opt/freesurfer/mni
ENV LOCAL_DIR /opt/freesurfer/local
ENV FREESURFER_HOME /opt/freesurfer
ENV FSFAST_HOME /opt/freesurfer/fsfast
ENV MINC_BIN_DIR /opt/freesurfer/mni/bin
ENV MINC_LIB_DIR /opt/freesurfer/mni/lib
ENV MNI_DATAPATH /opt/freesurfer/mni/data
ENV FMRI_ANALYSIS_DIR /opt/freesurfer/fsfast
ENV PERL5LIB /opt/freesurfer/mni/lib/perl5/5.8.5
ENV MNI_PERL5LIB /opt/freesurfer/mni/lib/perl5/5.8.5
ENV PATH /opt/freesurfer/bin:/opt/freesurfer/fsfast/bin:/opt/freesurfer/tktools:/opt/freesurfer/mni/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH

#############################################
# Gradient unwarp script is installed in base image. 

#############################################
# MSM_HOCR v3 binary is installed in base image.
ENV MSMBINDIR=${HCPPIPEDIR}/MSMBinaries

#############################################

# Copy executable/manifest to Gear
COPY run.py ${FLYWHEEL}/run.py
COPY manifest.json ${FLYWHEEL}/manifest.json

# ENV preservation for Flywheel Engine
RUN python3 -c 'import os, json; f = open("/tmp/gear_environ.json", "w"); json.dump(dict(os.environ), f)'

# Configure entrypoint
ENTRYPOINT ["/flywheel/v0/run.py"]
