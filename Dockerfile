# Creates docker container that runs HCP Pipeline algorithms
#
#

# Uses Ubuntu 16.04 LTS
FROM flywheel/hcp-base:1.0.2_4.3.0rc0

LABEL maintainer="Flywheel <support@flywheel.io>"

#############################################
# FSL 6.0.1 is a part of the base image.  Update the environment variables

#Build-time key retrieval is sometimes unable to connect to keyserver.  Instead, download the public key manually and store it in plaintext
#within repo.  You should run these commands occassionally to make sure the saved public key is up to date:
#gpg --keyserver hkp://pgp.mit.edu:80  --recv 0xA5D32F012649A5A9 && \
#gpg --export --armor 0xA5D32F012649A5A9 > neurodebian_pgpkey.txt && \
#gpg --batch --yes --delete-keys 0xA5D32F012649A5A9

COPY neurodebian_pgpkey.txt /tmp/

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    curl -sSL http://neurodebian.ovgu.de/lists/trusty.us-ca.full >> /etc/apt/sources.list.d/neurodebian.sources.list && \
    apt-key add /tmp/neurodebian_pgpkey.txt && \
    apt-get update && \
    apt-get install -y fsl-core=5.0.9-5~nd14.04+1 \
    python3-pip && \
    pip3 install pip==20.0.2 && \
    pip3 install flywheel-sdk~=14.6.3 && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Configure FSL environment
ENV FSLDIR=/usr/share/fsl/6.0 \ 
    FSL_DIR="${FSLDIR}" \ 
    FSLOUTPUTTYPE=NIFTI_GZ \ 
    PATH=/usr/share/fsl/6.0/bin:$PATH \ 
    FSLMULTIFILEQUIT=TRUE \ 
    POSSUMDIR=/usr/share/fsl/6.0 \ 
    LD_LIBRARY_PATH=/usr/share/fsl/6.0/lib:$LD_LIBRARY_PATH \ 
    FSLTCLSH=/usr/bin/tclsh \ 
    FSLWISH=/usr/bin/wish

#############################################
# Connectome Workbench 1.3.2 is a part of the base image. Compatible with HCP v4.0.1
# Setting related ENV variable here.

ENV CARET7DIR=/opt/workbench/bin_linux64

#############################################
# HCP Pipelines v4.0.1 installed in base image
# Set up specific environment variables for the HCP Pipeline
ENV FSL_DIR="${FSLDIR}" \ 
    HCPPIPEDIR=/opt/HCP-Pipelines \ 
    MSMBINDIR=${HCPPIPEDIR}/MSMBinaries \ 
    MSMCONFIGDIR=${HCPPIPEDIR}/MSMConfig

#For HCP Pipeline v4.0.1
ENV MSMBin=${HCPPIPEDIR}/MSMBinaries \
    HCPPIPEDIR_Templates=${HCPPIPEDIR}/global/templates \ 
    HCPPIPEDIR_Bin=${HCPPIPEDIR}/global/binaries \ 
    HCPPIPEDIR_Config=${HCPPIPEDIR}/global/config \ 
    HCPPIPEDIR_PreFS=${HCPPIPEDIR}/PreFreeSurfer/scripts \ 
    HCPPIPEDIR_FS=${HCPPIPEDIR}/FreeSurfer/scripts \ 
    HCPPIPEDIR_PostFS=${HCPPIPEDIR}/PostFreeSurfer/scripts \ 
    HCPPIPEDIR_fMRISurf=${HCPPIPEDIR}/fMRISurface/scripts \ 
    HCPPIPEDIR_fMRIVol=${HCPPIPEDIR}/fMRIVolume/scripts \ 
    HCPPIPEDIR_tfMRI=${HCPPIPEDIR}/tfMRI/scripts \ 
    HCPPIPEDIR_dMRI=${HCPPIPEDIR}/DiffusionPreprocessing/scripts \ 
    HCPPIPEDIR_dMRITract=${HCPPIPEDIR}/DiffusionTractography/scripts \ 
    HCPPIPEDIR_Global=${HCPPIPEDIR}/global/scripts \ 
    HCPPIPEDIR_tfMRIAnalysis=${HCPPIPEDIR}/TaskfMRIAnalysis/scripts

#try to reduce strangeness from locale and other environment settings
ENV LC_ALL=C \ 
    LANGUAGE=C
#POSIXLY_CORRECT currently gets set by many versions of fsl_sub, unfortunately, but at least don't pass it in if the user has it set in their usual environment
RUN unset POSIXLY_CORRECT

#############################################
# FreeSurfer is installed in base image. Ensure environment is set
# 6.0.1 ftp://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/6.0.1/freesurfer-Linux-centos6_x86_64-stable-pub-v6.0.1.tar.gz
# 5.3.0 ftp://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/5.3.0-HCP/freesurfer-Linux-centos4_x86_64-stable-pub-v5.3.0-HCP.tar.gz

# Set up the FreeSurfer environment
ENV OS=Linux \ 
    FS_OVERRIDE=0 \ 
    FIX_VERTEX_AREA= \ 
    SUBJECTS_DIR=/opt/freesurfer/subjects \ 
    FSF_OUTPUT_FORMAT=nii.gz \ 
    MNI_DIR=/opt/freesurfer/mni \ 
    LOCAL_DIR=/opt/freesurfer/local \ 
    FREESURFER_HOME=/opt/freesurfer \ 
    FSFAST_HOME=/opt/freesurfer/fsfast \ 
    MINC_BIN_DIR=/opt/freesurfer/mni/bin \ 
    MINC_LIB_DIR=/opt/freesurfer/mni/lib \ 
    MNI_DATAPATH=/opt/freesurfer/mni/data \ 
    FMRI_ANALYSIS_DIR=/opt/freesurfer/fsfast \ 
    PERL5LIB=/opt/freesurfer/mni/lib/perl5/5.8.5 \ 
    MNI_PERL5LIB=/opt/freesurfer/mni/lib/perl5/5.8.5 \ 
    PATH=/opt/freesurfer/bin:/opt/freesurfer/fsfast/bin:/opt/freesurfer/tktools:/opt/freesurfer/mni/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH

#############################################
# Gradient unwarp script is installed in base image. 

#############################################
# MSM_HOCR v3 binary is installed in base image.
ENV MSMBINDIR=${HCPPIPEDIR}/MSMBinaries

#############################################
# Copy gear-specific utils and dependencies
COPY utils ${FLYWHEEL}/utils
COPY scripts /tmp/scripts

# Copy executable/manifest to Gear
COPY run.py ${FLYWHEEL}/run.py
COPY manifest.json ${FLYWHEEL}/manifest.json

# ENV preservation for Flywheel Engine
RUN python3 -c 'import os, json; f = open("/tmp/gear_environ.json", "w"); json.dump(dict(os.environ), f)'

# Configure entrypoint
ENTRYPOINT ["/flywheel/v0/run.py"]
