#!/usr/bin/env python3
import json
import os, os.path as op
from zipfile import ZipFile
from utils import results
from utils import results, validate_config
from utils.args import GenericfMRIVolumeProcessingPipeline, \
                       GenericfMRISurfaceProcessingPipeline, \
                       hcpfunc_qc_mosaic

import flywheel
from utils.args.Common import set_subject
from utils.custom_logger import get_custom_logger

if __name__ == '__main__':
    # Preamble: take care of all gear-typical activities.
    context = flywheel.GearContext()
    #get_Custom_Logger is defined in utils.py
    # TODO: Get this consistent with how Andy has been doing logs...
    # TODO: furthermore, update hcp-func to be consistent.
    context.log = get_custom_logger('[flywheel:hcp-func]')

    context.log_config()

    # This gear will use a "custom_dict" dictionary as a custom-user field 
    # on the gear context.
    # TODO: change all of these to "gear_dict"
    context.custom_dict ={}
    context.custom_dict['SCRIPT_DIR']    = '/tmp/scripts'

    # grab environment for gear
    with open('/tmp/gear_environ.json', 'r') as f:
        environ = json.load(f)

    context.custom_dict['environ'] = environ

    # Before continuing from here, we need to validate the config.json
    # Validate gear configuration against gear manifest
    try:
        validate_config.validate_config_against_manifest(context)
    except Exception as e:
        context.log.error('Invalid Configuration:')
        context.log.fatal(e,)
        context.log.fatal(
            'Please make the prescribed corrections and try again.'
        )
        os.sys.exit(1)

    # Get file list and configuration from hcp-struct zipfile
    try:
        validate_config.preprocess_hcp_struct_zip(context)
    except Exception as e:
        context.log.error(e,)
        context.log.error('Invalid hcp-struct zip file.')
    
    # Ensure the subject_id is set in a valid manner 
    # (api, config, or hcp-struct config)
    try:
        validate_config.set_subject(context)
    except Exception as e:
        context.log.fatal(e,)
        context.log.fatal(
            'The Subject ID is not valid. Examine and try again.',
        )
        os.sys.exit(1)
    # build and validate parameters from the two pipelines
    # Ensure the subject_id is set in a valid manner (api or config)
    try:
        set_subject(context)
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
    # Pipelines common commands
    QUEUE = ""
    LogFileDirFull = op.join(context.work_dir,'logs')
    os.makedirs(LogFileDirFull, exist_ok=True)
    FSLSUBOPTIONS = "-l "+ LogFileDirFull

    command_common=[op.join(environ['FSLDIR'],'bin','fsl_sub'),
                   QUEUE, FSLSUBOPTIONS]
    
    context.custom_dict['command_common'] = command_common
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