"""
Builds, validates, and excecutes parameters for the HCP script 
/opt/HCP-Pipelines/fMRISurface/GenericfMRISurfaceProcessingPipeline.sh
part of the hcp-func gear
"""
import logging
import os.path as op

# Note common is available from hcp-base, once the Docker image is pulled.
from .common import build_command_list, exec_command

log = logging.getLogger(__name__)


def build(context):
    """
    Collect the configurations from the manifest to be passed to HCPPipelines' fMRISurface
    Args:
        context: Gear information, chiefly containing selected configuration options.
    Returns:
        modified context with "Surf-params" property for the parameters to run the command.
    """
    config = context.config
    params = {}
    params["path"] = context.work_dir
    params["subject"] = config["Subject"]
    params["fmriname"] = config["fMRIName"]
    # LowResMesh usually 32k vertices ("59" = 1.60mm)
    params["lowresmesh"] = "32"
    # ****config option?****** #generally "2", "1.60" possible
    params["fmrires"] = "2"
    # Smoothing during CIFTI surface and subcortical resampling
    params["smoothingFWHM"] = params["fmrires"]
    # GrayordinatesResolution usually 2mm ("1.60" also available)
    params["grayordinatesres"] = "2"
    # The func gear configuration overides the struct configuration
    # else use the struct configuration.
    if config["RegName"] != "Empty":
        params["regname"] = config["RegName"]
    elif "RegName" in context.gear_dict["hcp_struct_config"]["config"].keys():
        params["regname"] = context.gear_dict["hcp_struct_config"]["config"]["RegName"]
        config["RegName"] = params["regname"]
    else:
        raise Exception('Could not set "RegName" with current configuration.')

    params["printcom"] = ""
    context.gear_dict["Surf-params"] = params


def execute(context):
    environ = context.gear_dict["environ"]
    # Start by building command to execute
    command = []
    command.extend(context.gear_dict["command_common"])
    command.append(
        op.join(
            environ["HCPPIPEDIR"],
            "fMRISurface",
            "GenericfMRISurfaceProcessingPipeline.sh",
        )
    )
    command = build_command_list(command, context.gear_dict["Surf-params"])

    stdout_msg = (
        "Pipeline logs (stdout, stderr) will be available "
        + 'in the file "pipeline_logs.zip" upon completion.'
    )

    log.info("fMRI Surface Processing command: \n")
    exec_command(context, command, stdout_msg=stdout_msg)
