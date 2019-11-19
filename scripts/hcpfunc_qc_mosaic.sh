#!/bin/bash

set -e

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

qcmosaic1() { 
  bash ${SCRIPT_DIR}/volmosaic.sh $1 x 10 ${2}.png 
}
qcmosaic2() { 
  bash ${SCRIPT_DIR}/volmosaic.sh $2 $1 x 10 ${3}.png 
}

#2mm version of mosaics, skip fewer slices and do upscale at end
qcmosaic1_2mm() { 
  bash ${SCRIPT_DIR}/volmosaic.sh $1 x 5 ${2}.png -n -s 2
}
qcmosaic2_2mm() { 
  bash ${SCRIPT_DIR}/volmosaic.sh $2 $1 x 5 ${3}.png -n -s 2
}


SubjectDIR=$1
fMRIName=$2
imgroot=$3

#set -x

# anat-res, EPI-to-T1acpc volume with high-res T1 edges
qcmosaic2 ${SubjectDIR}/T1w/T1w_acpc_dc_restore ${SubjectDIR}/${fMRIName}/Scout2T1w ${imgroot}acpc_T1

#qcmosaic2 ${SubjectDIR}/T1w/ribbon ${SubjectDIR}/${fMRIName}/Scout2T1w ${imgroot}acpc_T1ribbon

# EPI-res, final MNI registration with low-res T1 edges (match either 2mm or 1.6mm)
qcmosaic2_2mm ${SubjectDIR}/${fMRIName}/T1w_restore.*.nii.gz ${SubjectDIR}/${fMRIName}/${fMRIName}_SBRef_nonlin ${imgroot}mni2mm_T1

# EPI-res, final MNI space, temporal mean
qctmp="qctmp"
${FSLDIR}/bin/fslmaths ${SubjectDIR}/MNINonLinear/Results/${fMRIName}/${fMRIName} -Tmean ${qctmp} \
  && qcmosaic1_2mm ${qctmp} ${imgroot}mni2mm_mean \
  && ${FSLDIR}/bin/imrm $qctmp

# EPI-res, final MNI space, temporal std dev
${FSLDIR}/bin/fslmaths ${SubjectDIR}/MNINonLinear/Results/${fMRIName}/${fMRIName} -Tstd ${qctmp} \
  && qcmosaic1_2mm ${qctmp} ${imgroot}mni2mm_stdev \
  && ${FSLDIR}/bin/imrm $qctmp

# Show EPI before and after distortion correction (to confirm correction was applied properly)
dcdirname=${SubjectDIR}/${fMRIName}/DistortionCorrectionAndEPIToT1wReg_FLIRTBBRAndFreeSurferBBRbased
qcfile_epiToT1_linear=${dcdirname}/epiToT1_linear.nii.gz
qcfile_epiToT1_corrected=${dcdirname}/epiToT1_corrected.nii.gz

${FSLDIR}/bin/applywarp --interp=spline \
  -i ${dcdirname}/FieldMap/SBRef.nii.gz \
  --premat=${dcdirname}/fMRI2str.mat \
  -r ${SubjectDIR}/T1w/T1w_acpc_dc_restore_brain.nii.gz \
  -o ${qcfile_epiToT1_linear} \
 && qcmosaic2 ${SubjectDIR}/T1w/T1w_acpc_dc_restore ${qcfile_epiToT1_linear} ${imgroot}epi2T1_uncorrected \
 && rm -f ${qcfile_epiToT1_linear}

${FSLDIR}/bin/applywarp --interp=spline \
  -i ${dcdirname}/FieldMap/SBRef_dc.nii.gz \
  --premat=${dcdirname}/fMRI2str.mat \
  -r ${SubjectDIR}/T1w/T1w_acpc_dc_restore_brain.nii.gz \
  -o ${qcfile_epiToT1_corrected} \
 && qcmosaic2 ${SubjectDIR}/T1w/T1w_acpc_dc_restore ${qcfile_epiToT1_corrected} ${imgroot}epi2T1_corrected \
 && rm -f ${qcfile_epiToT1_corrected}
