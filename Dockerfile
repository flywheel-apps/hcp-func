# Creates docker container that runs HCP Pipeline algorithms
#
#

# Use Ubuntu 14.04 LTS
FROM flywheel/fsl-base:5.0.9_trusty

LABEL maintainer="Flywheel <support@flywheel.io>"

#############################################
# FSL 5.0.9 is a part of the base image.  Update the environment variables

# Configure FSL environment
ENV FSLDIR=/usr/share/fsl/5.0
ENV FSL_DIR="${FSLDIR}"
ENV FSLOUTPUTTYPE=NIFTI_GZ
ENV PATH=/usr/lib/fsl/5.0:$PATH
ENV FSLMULTIFILEQUIT=TRUE
ENV POSSUMDIR=/usr/share/fsl/5.0
ENV LD_LIBRARY_PATH=/usr/lib/fsl/5.0:$LD_LIBRARY_PATH
ENV FSLTCLSH=/usr/bin/tclsh
ENV FSLWISH=/usr/bin/wish

#############################################
# Download and install Connectome Workbench 1.3.2 
# Compatible with HCP v4.0.0
RUN cd /opt/ && \
    wget https://www.humanconnectome.org/storage/app/media/workbench/workbench-linux64-v1.3.2.zip -O workbench.zip && \
    unzip workbench.zip && \
    rm workbench.zip && \
    cd /

ENV CARET7DIR=/opt/workbench/bin_linux64

#############################################
# Download and install HCP Pipelines

# Using v4.0.0
RUN wget -nv https://github.com/Washington-University/HCPpipelines/archive/v4.0.0.tar.gz -O pipelines.tar.gz && \
    cd /opt/ && \
    tar zxvf /pipelines.tar.gz && \
    mv /opt/*ipelines* /opt/HCP-Pipelines && \
    rm /pipelines.tar.gz && \
    cd / 

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
# Download and install FreeSurfer
RUN apt-get -y update \
    && apt-get install -y wget && \
    wget -nv -O- ftp://surfer.nmr.mgh.harvard.edu/pub/dist/freesurfer/5.3.0-HCP/freesurfer-Linux-centos4_x86_64-stable-pub-v5.3.0-HCP.tar.gz | tar zxv -C /opt \
    --exclude='freesurfer/trctrain' \
    --exclude='freesurfer/subjects/fsaverage_sym' \
    --exclude='freesurfer/subjects/fsaverage3' \
    --exclude='freesurfer/subjects/fsaverage4' \
    --exclude='freesurfer/subjects/fsaverage5' \
    --exclude='freesurfer/subjects/fsaverage6' \
    --exclude='freesurfer/subjects/cvs_avg35' \
    --exclude='freesurfer/subjects/cvs_avg35_inMNI152' \
    --exclude='freesurfer/subjects/bert' \
    --exclude='freesurfer/subjects/V1_average' \
    --exclude='freesurfer/average/mult-comp-cor' \
    --exclude='freesurfer/lib/cuda' \
    --exclude='freesurfer/lib/qt' && \
    apt-get install -y tcsh bc tar libgomp1 perl-modules curl 

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
# Download and install gradient unwarp script
# note: python-dev needed for Ubuntu 14.04 (but not for 16.04)
# latest = v1.0.3
RUN apt-get -y update \
    && apt-get install -y --no-install-recommends \ 
    python-dev \
    python-numpy \
    python-scipy \
    python-nibabel && \
    wget -nv https://github.com/Washington-University/gradunwarp/archive/v1.0.3.tar.gz -O gradunwarp.tar.gz && \
    cd /opt/ && \
    tar zxvf /gradunwarp.tar.gz && \
    mv /opt/gradunwarp-* /opt/gradunwarp && \
    cd /opt/gradunwarp/ && \
    python setup.py install && \
    rm /gradunwarp.tar.gz && \
    cd / 


#############################################
# Download amnd install MSM_HOCR v3 binary
ENV MSMBINDIR=${HCPPIPEDIR}/MSMBinaries

RUN mkdir -p ${MSMBINDIR} && \
    wget -nv https://github.com/ecr05/MSM_HOCR/releases/download/1.0/msm_ubuntu14.04 -O ${MSMBINDIR}/msm && \
    chmod +x ${MSMBINDIR}/msm
#############################################

# Make directory for flywheel spec (v0)
ENV FLYWHEEL /flywheel/v0
WORKDIR ${FLYWHEEL}

# Install gear dependencies
COPY requirements.txt ${FLYWHEEL}/requirements.txt
RUN apt-get install -y --no-install-recommends \
    gawk \
    python3-pip \
    zip \
    unzip \
    gzip && \
    pip3 install --upgrade pip && \
    apt-get remove -y python3-urllib3 && \
    pip3.4 install -r requirements.txt && \
    rm -rf /root/.cache/pip && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Copy executable/manifest to Gear
COPY run.py ${FLYWHEEL}/run.py
COPY utils ${FLYWHEEL}/utils
COPY manifest.json ${FLYWHEEL}/manifest.json

# Copy additional scripts and scenes
COPY scripts /tmp/scripts


# ENV preservation for Flywheel Engine
RUN python -c 'import os, json; f = open("/tmp/gear_environ.json", "w"); json.dump(dict(os.environ), f)'

# Configure entrypoint
ENTRYPOINT ["/flywheel/v0/run.py"]
