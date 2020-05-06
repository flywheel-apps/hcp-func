"""
Builds, validates, and excecutes parameters for the HCP helper script 
/tmp/scripts/hcpfunc_qc_mosaic.sh
part of the hcp-func gear
"""
import logging
import os
import os.path as op
from collections import OrderedDict

from .common import build_command_list, exec_command

log = logging.getLogger(__name__)


def build(context):
    config = context.config
    params = OrderedDict()
    params['qc_scene_root'] = op.join(context.work_dir, config['Subject'])
    params['fMRIName'] = config['fMRIName']
    # qc_image_root indicates where the images are going
    params['qc_image_root'] = op.join(
        context.work_dir,
        config['Subject'] + '_{}.hcp_func_QC.'.format(config['fMRIName'])
    )
    context.gear_dict['QC-Params'] = params


def execute(context):
    SCRIPT_DIR = context.gear_dict['SCRIPT_DIR']
    command = [op.join(SCRIPT_DIR, 'hcpfunc_qc_mosaic.sh')]

    command = build_command_list(
        command,
        context.gear_dict['QC-Params'],
        include_keys=False
    )

    command.append('>')
    command.append(op.join(context.work_dir, 'logs', 'functionalqc.log'))

    stdout_msg = 'Pipeline logs (stdout, stderr) will be available ' + \
                 'in the file "pipeline_logs.zip" upon completion.'

    log.info('Functional QC Image Generation command: \n')
    exec_command(context, command, shell=True, stdout_msg=stdout_msg)
