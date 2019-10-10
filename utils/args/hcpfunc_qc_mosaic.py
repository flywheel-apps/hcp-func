import os, os.path as op
from collections import OrderedDict
from .common import build_command_list, exec_command

def build(context):
    config = context.config
    params = OrderedDict()
    params['qc_scene_root'] = op.join(context.work_dir, config['Subject'])
    params['qc_output_folder'] = context.work_dir
    params['qc_image_root'] = op.join(
        op.join(
            context.output_dir,config['Subject'] + \
            '_{}.hcp_func_QC.'.format(config['fMRIName'])
        )
    )
    context.custom_dict['QC-Params'] = params

def validate(context):
    pass

def execute(context):
    SCRIPT_DIR = context.custom_dict['SCRIPT_DIR']
    command = [op.join(SCRIPT_DIR,'hcpfunc_qc_mosaic.sh')]

    command = build_command_list(
        command, context.custom_dict['QC-Params'], include_keys = False
    )

    command.append('>')
    command.append(op.join(context.work_dir,'logs'))

    stdout_msg = 'Pipeline logs (stdout, stderr) will be available ' + \
                 'in the file "pipeline_logs.zip" upon completion.'

    context.log.info('Functional QC Image Generation command: \n')
    exec_command(context, command, stdout_msg = stdout_msg)