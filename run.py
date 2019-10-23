#!/usr/bin/env python3
import json
import os, os.path as op
from zipfile import ZipFile
import traceback
from utils import results, gear_preliminaries
from utils.args import GenericfMRIVolumeProcessingPipeline, \
                       GenericfMRISurfaceProcessingPipeline, \
                       hcpfunc_qc_mosaic

import flywheel

def main():
    # Preamble: take care of all gear-typical activities.
    context = flywheel.GearContext()

    # Initialize all hcp-gear variables.
    gear_preliminaries.initialize_gear(context)

    context.log_config()
    
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
        tb = traceback.format_tb(e.__traceback__)
        context.log.fatal(''.join(tb))
        os.sys.exit(1)

    # Get file list and configuration from hcp-struct zipfile
    try:
        gear_preliminaries.preprocess_hcp_struct_zip(context)
    except Exception as e:
        context.log.error(e,)
        context.log.error('Invalid hcp-struct zip file.')
        tb = traceback.format_tb(e.__traceback__)
        context.log.fatal(''.join(tb))
        os.sys.exit(1)
    
    # Ensure the subject_id is set in a valid manner 
    # (api, config, or hcp-struct config)
    try:
        gear_preliminaries.set_subject(context)
    except Exception as e:
        context.log.fatal(e,)
        context.log.fatal(
            'The Subject ID is not valid. Examine and try again.',
        )
        tb = traceback.format_tb(e.__traceback__)
        context.log.fatal(''.join(tb))
        os.sys.exit(1)

    ############################################################################
    ###################Build and Validate Parameters############################
    # Doing as much parameter checking before ANY computation.
    # Fail as fast as possible.

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
        tb = traceback.format_tb(e.__traceback__)
        context.log.fatal(''.join(tb))
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
        tb = traceback.format_tb(e.__traceback__)
        context.log.fatal(''.join(tb))
        os.sys.exit(1)

    ###########################################################################
    # Unzip hcp-struct results
    try: 
        gear_preliminaries.unzip_hcp_struct(context)
    except Exception as e:
        context.log.fatal(e)
        context.log.fatal(
            'Unzipping hcp-struct zipfile failed!'
        )
        tb = traceback.format_tb(e.__traceback__)
        context.log.fatal(''.join(tb))
        os.sys.exit(1)

    ############################################################################
    ####################Execute HCP Pipelines ##################################

    ###########################################################################
    # Pipelines common commands
    QUEUE = ""
    LogFileDirFull = op.join(context.work_dir,'logs')
    os.makedirs(LogFileDirFull, exist_ok=True)
    FSLSUBOPTIONS = "-l "+ LogFileDirFull

    command_common=[
        op.join(context.gear_dict['environ']['FSLDIR'],'bin','fsl_sub'),
        QUEUE,
        FSLSUBOPTIONS
    ]
    
    context.gear_dict['command_common'] = command_common

    # Execute fMRI Volume Pipeline
    try:
        GenericfMRIVolumeProcessingPipeline.execute(context)
    except Exception as e:
        context.log.fatal(e)
        context.log.fatal('The fMRI Volume Pipeline Failed!')
        tb = traceback.format_tb(e.__traceback__)
        context.log.fatal(''.join(tb))
        if context.config['save-on-error']:
            results.cleanup(context)
        os.sys.exit(1)

    # Execute fMRI Surface Pipeline 
    try:
        GenericfMRISurfaceProcessingPipeline.execute(context)
    except Exception as e:
        context.log.fatal(e)
        context.log.fatal('The fMRI Surface Pipeline Failed!')
        tb = traceback.format_tb(e.__traceback__)
        context.log.fatal(''.join(tb))
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
        tb = traceback.format_tb(e.__traceback__)
        context.log.fatal(''.join(tb))
        if context.config['save-on-error']:
            results.cleanup(context)
        exit(1)

    ###########################################################################
    # Clean-up and output prep
    results.cleanup(context)

    os.sys.exit(0)

if __name__ == '__main__':
    main()