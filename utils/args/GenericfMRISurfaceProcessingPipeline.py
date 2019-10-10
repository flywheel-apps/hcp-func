import os, os.path as op
from .common import build_command_list, exec_command

def build(context):
# if [[ -z "${FW_CONFIG_RegName}" ]] || [[ $(toupper "${FW_CONFIG_RegName}") = "EMPTY" ]]; then
#   RegName="${hcpstruct_RegName}"
# else
#   RegName="${FW_CONFIG_RegName}"
# fi
    config = context.config
    params = {}
    params['path'] = context.work_dir
    params['subject'] = config['Subject']
    params['fmriname'] = config['fMRIName']
    #LowResMesh usually 32k vertices ("59" = 1.60mm)
    params['lowresmesh'] = "32"
    #****config option?****** #generally "2", "1.60"
    params['fmrires'] = "2"
    # Smoothing during CIFTI surface and subcortical resampling
    params['smoothingFWHM'] = params['fmrires']
    # GrayordinatesResolution usually 2mm ("1.60" also available)
    params['grayordinatesres'] = "2"
    if 'RegName' in config.keys():
        params['regname'] = config['RegName']
    elif 'RegName' in context.custom_dict['hcp_struct_config']['config'].keys():
        params['regname'] = context.custom_dict['hcp_struct_config']['config']['RegName']
        config['RegName'] = params['regname']
    else:
        raise Exception('Could not set "RegName" with current configuration.')

    params['printcom'] = ' '
    context.custom_dict['Surf-params'] = params
    
def validate(context):
    pass 

def execute(context):
    environ = context.custom_dict['environ']
    # Start by building command to execute
    command = []
    command.extend(context.custom_dict['command_common'])
    command.append(
               op.join(environ['HCPPIPEDIR'],'fMRISurface',
               'GenericfMRISurfaceProcessingPipeline.sh')
    )
    command = build_command_list(command,context.custom_dict['Surf-params'])

    stdout_msg = 'Pipeline logs (stdout, stderr) will be available ' + \
                 'in the file "pipeline_logs.zip" upon completion.'

    context.log.info('fMRI Surface Processing command: \n')
    exec_command(context, command, stdout_msg = stdout_msg)