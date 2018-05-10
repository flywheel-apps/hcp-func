# flywheel/hcp-func
[Flywheel Gear](https://github.com/flywheel-io/gears/tree/master/spec) that runs the functional preprocessing steps of the [Human Connectome Project](http://www.humanconnectome.org) Minimal Preprocessing Pipeline (MPP) described in [Glasser et al. 2013](http://www.ncbi.nlm.nih.gov/pubmed/23668970).  Currently, this includes v4.0-alpha release of fMRIVolume and fMRISurface, as well as generating some helpful QC images. For more info on the pipelines, see [HCP Pipelines](https://github.com/Washington-University/Pipelines).

## Important notes
* All MRI inputs (fMRI time series, FieldMaps) must include BIDS-conformed DICOM metadata!
* Gradient nonlinearity correction (using coefficient file) is currently only available for data from Siemens scanners.
* Readout distortion correction using B0 field maps (Field map "Option 1", below) is currently only available for data from Siemens scanners.  "TOPUP"-style correction (Field map "Option 2", below) should work for all data (but has not yet been tested).

## Required inputs
1. fMRI time series NiFTI
2. StructZip output from the HCP-Struct gear (containing <code>T1w/</code>, <code>T2w/</code>, and <code>MNINonLinear/</code> folders)
3. FreeSurfer license.txt file  (found in <code>$FREESURFER_HOME/license.txt</code>)

## Optional inputs
1. fMRIScout: high-quality exemplar volume from fMRI time-series. If using Multi-Band for fMRI, and Single-Band reference volume is available, use SBRef. Otherwise, leave empty to first time series volume for registration.
2. Field map for correcting readout distortion
    * Option 1: "typical" GRE B0 field map including magnitude and phase volumes
    * Option 2: a pair of spin echo with opposite phase-encode directions ("Positive" = R>>L or P>>A, and "Negative" = L>>R or A>>P) for "TOPUP"-style distortion estimation
3. Gradient nonlinearity coefficients copied from scanner. See [FAQ 8. What is gradient nonlinearity correction?](https://github.com/Washington-University/Pipelines/wiki/FAQ#8-what-is-gradient-nonlinearity-correction)
    * If needed, this file can be obtained from the console at <code>C:\MedCom\MriSiteData\GradientCoil\coeff.grad</code> for Siemens scanners
    * Note: This effect is significant for HCP data collected on custom Siemens "ConnectomS" scanner, and for 7T scanners.  It is relatively minor for production 3T scanners (Siemens Trio, Prisma, etc.)
    
## Outputs
* <code>\<subject\>\_\<fMRIName\>\_hcpfunc.zip</code>: Zipped output directory containing <code>\<fMRIName\>/</code> and <code>MNINonLinear/Results/\<fMRIName\>/</code> folders
* <code>\<subject\>\_\<fMRIName\>\_hcpfunc\_QC.*.png</code>: QC images for visual inspection of output quality (Distortion correction and registration to anatomy, details to come...)
* Logs (details to come...)

## Important HCP Pipeline links
* [HCP Pipelines](https://github.com/Washington-University/Pipelines)
* [HCP Pipelines FAQ](https://github.com/Washington-University/Pipelines/wiki/FAQ)
* [HCP Pipelines v3.4.0 release notes](https://github.com/Washington-University/Pipelines/wiki/v3.4.0-Release-Notes,-Installation,-and-Usage)
