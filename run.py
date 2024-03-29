#!/usr/bin/env python3
import os
import os.path as op

import flywheel

# Note utils are from hcp-base Docker image.
from utils import func_utils, gear_preliminaries, results
from utils.args import (
    GenericfMRISurfaceProcessingPipeline,
    GenericfMRIVolumeProcessingPipeline,
    hcpfunc_qc_mosaic,
)


def main():
    """
    Handles all the aspects of setting up the HCPPipeline functional run.
    1) Check/get the FS license
    2) Unzip the analyzed structural files (hcp-struct must be run first)
    3) Build and validate the command for the fMRIVolume
    4) Build the command for fMRISurface.
    5) Unzip the structural analysis output.
    6) Run fMRIVolume
    7) Run fMRISurface.
    8) Produce QC on fMRI analyses.

    Returns:
        Zipped analysis folder
        Exit status of the gear
    """

    # Preamble: take care of all gear-typical activities.
    context = flywheel.GearContext()
    context.gear_dict = {}
    # Initialize all hcp-gear variables.
    gear_preliminaries.initialize_gear(context)
    context.log_config()

    # Utilize FreeSurfer license from config or project metadata
    try:
        gear_preliminaries.set_freesurfer_license(context)
    except Exception as e:
        context.log.exception(e)
        context.log.fatal(
            "A valid FreeSurfer license must be present to run."
            + "Please check your configuration and try again."
        )
        os.sys.exit(1)

    # Before continuing from here, we need to validate the config.json
    # Validate gear configuration against gear manifest
    try:
        gear_preliminaries.validate_config_against_manifest(context)
    except Exception as e:
        context.log.error("Invalid Configuration:")
        context.log.exception(e)
        context.log.fatal("Please make the prescribed corrections and try again.")
        os.sys.exit(1)

    # Get file list and configuration from hcp-struct zipfile
    try:
        hcp_struct_zip_filename = context.get_input_path("StructZip")
        hcp_struct_list, hcp_struct_config = gear_preliminaries.preprocess_hcp_zip(
            hcp_struct_zip_filename
        )
        context.gear_dict["exclude_from_output"] = hcp_struct_list
        context.gear_dict["hcp_struct_config"] = hcp_struct_config
    except Exception as e:
        context.log.exception(e)
        context.log.fatal("Invalid hcp-struct zip file.")
        os.sys.exit(1)

    # Ensure the subject_id is set in a valid manner
    # (api, config, or hcp-struct config)
    try:
        gear_preliminaries.set_subject(context)
    except Exception as e:
        context.log.exception(e)
        context.log.fatal("The Subject ID is not valid. Examine and try again.",)
        os.sys.exit(1)

    # ##########################################################################
    # #################Build and Validate Parameters############################
    # Doing as much parameter checking before ANY computation.
    # Fail as fast as possible.

    try:
        # Build and validate from Volume Processing Pipeline
        GenericfMRIVolumeProcessingPipeline.build(context)
        GenericfMRIVolumeProcessingPipeline.validate(context)
    except Exception as e:
        context.log.exception(e)
        context.log.fatal("Validating Parameters for the fMRI Volume Pipeline Failed!")
        os.sys.exit(1)

    try:
        # Build and validate from Surface Processing Pipeline
        GenericfMRISurfaceProcessingPipeline.build(context)
    except Exception as e:
        context.log.exception(e)
        context.log.fatal("Validating Parameters for the fMRI Surface Pipeline Failed!")
        os.sys.exit(1)

    ###########################################################################
    # Unzip hcp-struct results
    try:
        gear_preliminaries.unzip_hcp(context, hcp_struct_zip_filename)
    except Exception as e:
        context.log.exception(e)
        context.log.fatal("Unzipping hcp-struct zipfile failed!")
        os.sys.exit(1)

    # ##########################################################################
    # ##################Execute HCP Pipelines ##################################
    # Some hcp-func specific output parameters:
    (
        context.gear_dict["output_config"],
        context.gear_dict["output_config_filename"],
    ) = func_utils.configs_to_export(context)

    context.gear_dict["output_zip_name"] = op.join(
        context.output_dir,
        "{}_{}_hcpfunc.zip".format(
            context.config["Subject"], context.config["fMRIName"]
        ),
    )

    context.gear_dict["remove_files"] = func_utils.remove_intermediate_files
    ###########################################################################
    # Pipelines common commands
    QUEUE = ""
    LogFileDirFull = op.join(context.work_dir, "logs")
    os.makedirs(LogFileDirFull, exist_ok=True)
    FSLSUBOPTIONS = "-l " + LogFileDirFull

    command_common = [
        op.join(context.gear_dict["environ"]["FSLDIR"], "bin", "fsl_sub"),
        FSLSUBOPTIONS,
    ]

    context.gear_dict["command_common"] = command_common

    # Execute fMRI Volume Pipeline
    try:
        GenericfMRIVolumeProcessingPipeline.execute(context)
    except Exception as e:
        context.log.exception(e)
        context.log.fatal("The fMRI Volume Pipeline Failed!")
        if context.config["save-on-error"]:
            results.cleanup(context)
        os.sys.exit(1)

    # Execute fMRI Surface Pipeline
    try:
        GenericfMRISurfaceProcessingPipeline.execute(context)
    except Exception as e:
        context.log.exception(e)
        context.log.fatal("The fMRI Surface Pipeline Failed!")
        if context.config["save-on-error"]:
            results.cleanup(context)
        os.sys.exit(1)

    # Generate HCP-Functional QC Images
    try:
        hcpfunc_qc_mosaic.build(context)
        hcpfunc_qc_mosaic.execute(context)
    except Exception as e:
        context.log.exception(e)
        context.log.fatal("HCP Functional QC Images has failed!")
        if context.config["save-on-error"]:
            results.cleanup(context)
        exit(1)

    ###########################################################################
    # Clean-up and output prep
    results.cleanup(context)

    os.sys.exit(0)


if __name__ == "__main__":
    main()
