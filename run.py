#!/usr/bin/env python3
import json
import os, os.path as op
from zipfile import ZipFile
from utils import results
from utils import results, gear_preliminaries
from utils.args import GenericfMRIVolumeProcessingPipeline, \
                       GenericfMRISurfaceProcessingPipeline, \
                       hcpfunc_qc_mosaic

import flywheel
from utils.custom_logger import get_custom_logger

if __name__ == '__main__':
    # Preamble: take care of all gear-typical activities.
    context = flywheel.GearContext()
    #get_Custom_Logger is defined in utils.py
    # TODO: Get this consistent with how Andy has been doing logs...
    # TODO: furthermore, update hcp-func to be consistent.
    context.log = get_custom_logger('[flywheel:hcp-func]')

    context.log_config()

    # This gear will use a "gear_dict" dictionary as a custom-user field 
    # on the gear context.
    # TODO: change all of these to "gear_dict"
    context.gear_dict ={}
    context.gear_dict['SCRIPT_DIR']    = '/tmp/scripts'

    # Set dry-run parameter
    # TODO: Integrate "dry-run" into manifest.
    context.gear_dict['dry-run'] = True

    # grab environment for gear
    with open('/tmp/gear_environ.json', 'r') as f:
        environ = json.load(f)

    context.gear_dict['environ'] = environ
    context.gear_dict['whitelist'] = []
    context.gear_dict['metadata'] = {}
    # Before continuing from here, we need to validate the config.json
    # Validate gear configuration against gear manifest
    try:
        gear_preliminaries.validate_config_against_manifest(context)
    except Exception as e:
        context.log.error('Invalid Configuration:')
        context.log.fatal(e,)
        context.log.fatal(
            'Please make the prescribed corrections and try again.'
        )
        os.sys.exit(1)

    # Get file list and configuration from hcp-struct zipfile
    try:
        gear_preliminaries.preprocess_hcp_struct_zip(context)
    except Exception as e:
        context.log.error(e,)
        context.log.error('Invalid hcp-struct zip file.')
    
    # Ensure the subject_id is set in a valid manner 
    # (api, config, or hcp-struct config)
    try:
        gear_preliminaries.set_subject(context)
    except Exception as e:
        context.log.fatal(e,)
        context.log.fatal(
            'The Subject ID is not valid. Examine and try again.',
        )
        os.sys.exit(1)

    try:
        # Build and validate from Volume Processing Pipeline
        GenericfMRIVolumeProcessingPipeline.build(context)
        GenericfMRIVolumeProcessingPipeline.validate(context)
    except Exception as e:
        context.log.fatal(e)
        context.log.fatal(
            'Validating Parameters for the ' + \
            'fMRI Volume Pipeline Failed!'
        )
        os.sys.exit(1)

    try:
        # Build and validate from Surface Processign Pipeline
        GenericfMRISurfaceProcessingPipeline.build(context)
        GenericfMRISurfaceProcessingPipeline.validate(context)
    except Exception as e:
        context.log.fatal(e)
        context.log.fatal(
            'Validating Parameters for the ' + \
            'fMRI Surface Pipeline Failed!'
        )
        os.sys.exit(1)

    ###########################################################################
    # Unzip hcp-struct results
    gear_preliminaries.unzip_hcp_struct(context)

    ###########################################################################
    # Pipelines common commands
    QUEUE = ""
    LogFileDirFull = op.join(context.work_dir,'logs')
    os.makedirs(LogFileDirFull, exist_ok=True)
    FSLSUBOPTIONS = "-l "+ LogFileDirFull

    command_common=[op.join(environ['FSLDIR'],'bin','fsl_sub'),
                   QUEUE, FSLSUBOPTIONS]
    
    context.gear_dict['command_common'] = command_common

    # Execute fMRI Volume Pipeline
    try:
        GenericfMRIVolumeProcessingPipeline.execute(context)
    except Exception as e:
        context.log.fatal(e)
        context.log.fatal('The fMRI Volume Pipeline Failed!')
        if context.config['save-on-error']:
            results.cleanup(context)
        os.sys.exit(1)

    # Execute fMRI Surface Pipeline Failed
    try:
        GenericfMRISurfaceProcessingPipeline.execute(context)
    except Exception as e:
        context.log.fatal(e)
        context.log.fatal('The fMRI Surface Pipeline Failed!')
        if context.config['save-on-error']:
            results.cleanup(context)
        os.sys.exit(1)

    # Generate HCP-Functional QC Images
    try:
        hcpfunc_qc_mosaic.build(context)
        hcpfunc_qc_mosaic.execute(context)
    except Exception as e:
        context.log.fatal(e,)
        context.log.fatal('HCP Functional QC Images has failed!')
        if context.config['save-on-error']:
            results.cleanup(context)
        exit(1)

    ###########################################################################
    # Clean-up and output prep
    results.cleanup(context)
    os.sys.exit(0)       