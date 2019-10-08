import os, os.path as op
import shutil
from tr import tr
from .common import build_command_list, exec_command

def build(context):
    config = context.config
    inputs = context._invocation['inputs']
    environ = context.custom_dict['environ']

    # Install FreeSurfer license file
    shutil.copy(context.get_input_path('FreeSurferLicense'),
                op.join(environ['FREESURFER_HOME'],'license.txt'))

    params = {}
    
    # Initialize "NONE"s
    params['unwarpdir'] = "" #must be correctly derived from metadata
    #use "FLIRT" to run FLIRT-based mcflirt_acc.sh, or "MCFLIRT" to run MCFLIRT-based mcflirt.sh
    params['mctype'] = "MCFLIRT"  
    None_Params = [
        'echodiff', 
        'echospacing',
        'dcmethod',
        'fmapgeneralelectric',
        'SEPhaseNeg',
        'SEPhasePos',
        'fmapmag',
        'fmapphase',
        'fmriscout',
        'biascorrection',
        'gdcoeffs' 
    ]
    for key in None_Params:
        params[key] = 'NONE'

    params['path'] = context.work_dir
    # The subject may have three different ways to be set:
    # 1) UI 2) hcp-struct.json zip 3) container
    params['subject'] = config['Subject']
    params['fmriname'] = config['fMRIName']
    params['fmritcs'] = context.get_input_path('fMRITimeSeries')

    # TODO: confirm parameters match fMRITimeSeries?
    if 'fMRIScout' in inputs.keys():
        params['fmriscout'] = context.get_input_path('fMRIScout')

    # Read necessary acquisition params from fMRI
    obj = inputs['fMRITimeSeries']['object']
    if 'EffectiveEchoSpacing' in obj['info'].keys():
        params['echospacing'] = obj['info']['EffectiveEchoSpacing']
        
    obj = inputs['fMRITimeSeries']['object']
    if 'PhaseEncodingDirection' in obj['info'].keys():
       params['unwarpdir'] = tr("ijk", "xyz", 
                                obj['info']['PhaseEncodingDirection'])

    #****config option?****** #generally "2", "1.60"
    params['fmrires'] = "2"

    #Topup config if using TOPUP, set to NONE if using regular FIELDMAP
    params['topupconfig']=op.join(environ['HCPPIPEDIR_Config'],'b02b0.cnf')

    # TODO: BiasCorrection must be NONE, Legacy, or SEBased! enum default NONE
    params['biascorrection'] = config['BiasCorrection']

    # TODO: MotionCorrection must be MCFLIRT or FLIRT!, enum default MCFLIRT
    params['mctype'] = config['MotionCorrection']

    # TODO: DOF must be 6 or 12 (put in ENUM), default 6
    params['dof'] = config['AnatomyRegDOF']

    # Parse Inputs
    # If SiemensFieldMap
    if (
        ('SiemensGREMagnitude' in inputs.keys()) and
        ('SiemensGREPhase' in inputs.keys())
    ):
        params['fmapmag'] = context.get_input_path('SiemensGREMagnitude')
        params['fmapphase'] = context.get_input_path('SiemensGREPhase')
        params['dcmethod'] = "SiemensFieldMap"
        if (
          ('EchoTime' in inputs["SiemensGREMagnitude"]['object']['info'].keys()) and
          ('EchoTime' in inputs["SiemensGREPhase"]['object']['info'].keys())
        ):
            echotime1 = inputs["SiemensGREMagnitude"]['object']['info']['EchoTime']
            echotime2 = inputs["SiemensGREPhase"]['object']['info']['EchoTime']
            params['echodiff'] = (echotime2 - echotime1) * 1000.0
    # Else if TOPUP
    elif (
        ('SpinEchoNegative' in inputs.keys()) and
        ('SpinEchoPositive' in inputs.keys())
    ):
        params['dcmethod'] = "TOPUP"
        SpinEchoPhase1 = context.get_input_path("SpinEchoPositive")
        SpinEchoPhase2 = context.get_input_path("SpinEchoNegative")
        # Topup config if using TOPUP, set to NONE if using regular FIELDMAP
        params['topupconfig'] = environ['HCPPIPEDIR_Config'] + "/b02b0.cnf"
        if (
            'EffectiveEchoSpacing' in
            inputs["SpinEchoPositive"]['object']['info'].keys()
        ):
            params['seechospacing'] = \
                inputs["SpinEchoPositive"]['object']['info']['EffectiveEchoSpacing']
            if (
                ('PhaseEncodingDirection' in
                inputs["SpinEchoPositive"]['object']['info'].keys()
                )
                and
                ('PhaseEncodingDirection' in
                inputs["SpinEchoNegative"]['object']['info'].keys()
                )
            ):
                pedirSE1 = \
                   inputs["SpinEchoPositive"]['object']['info']['PhaseEncodingDirection']
                pedirSE2 = \
                   inputs["SpinEchoNegative"]['object']['info']['PhaseEncodingDirection']
                pedirSE1 = tr("ijk", "xyz", pedirSE1)
                pedirSE2 = tr("ijk", "xyz", pedirSE2)
                # Check SpinEcho phase-encoding directions
                if (
                    ((pedirSE1, pedirSE2) == ("x", "x-")) or
                    ((pedirSE1, pedirSE2) == ("y", "y-"))
                ):
                    params['SEPhasePos'] = SpinEchoPhase1
                    params['SEPhaseNeg'] = SpinEchoPhase2
                elif (
                    ((pedirSE1, pedirSE2) == ("x-", "x")) or
                    ((pedirSE1, pedirSE2) == ("y-", "y"))
                ):
                    params['SEPhasePos'] = SpinEchoPhase2
                    params['SEPhaseNeg'] = SpinEchoPhase1
                    context.log.warning(
                        "SpinEcho phase-encoding directions were swapped. \
                         Continuing!")
                params['seunwarpdir'] = pedirSE1.replace(
                    '-', '').replace('+', '')
    # Else if General Electric Field Map
    elif "GeneralElectricFieldMap" in inputs.keys():
        # TODO: how do we handle GE fieldmap? where do we get deltaTE?
        raise Exception("Cannot currently handle GeneralElectricFieldmap!")

    params['unwarpdir'] = config['StructuralUnwarpDirection']
    if 'GradientCoeff' in inputs.keys():
        params['gdcoeffs'] = context.get_input_path('GradientCoeff')

    params['printcom'] = "\"\""

    context.custom_dict['Vol-params'] = params

def validate(context):
    """
    Ensure that the fMRI Volume Processing Parameters are valid.
    Raise Exceptions and exit if not valid.
    """

    params = context.custom_dict['Vol-params']
    inputs = context._invocation['inputs']    

    if (params['dcmethod']!= "TOPUP") and (params['biascorrection']=='SEBased'):
        raise Exception('SE-Based BiasCorrection only available when ' + \
            'providing Pos and Neg SpinEchoFieldMap scans')

    # Examine Siemens Field Map input
    if (
        ('SiemensGREMagnitude' in inputs.keys()) and
        ('SiemensGREPhase' in inputs.keys())
    ):
        if 'echodiff' in params.keys():
            if params['echodiff'] == 0:
                raise Exception(
                    'EchoTime1 and EchoTime2 are the same \
                        (Please ensure Magnitude input is TE1)! Exiting.')
        else:
            raise Exception(
                'No EchoTime metadata found in FieldMap input file!  Exiting.')
    # Examine TOPUP input
    elif (
        ('SpinEchoNegative' in inputs.keys()) and
        ('SpinEchoPositive' in inputs.keys())
    ):
        if (
            ('PhaseEncodingDirection' in
             inputs["SpinEchoPositive"]['object']['info'].keys()) and
            ('PhaseEncodingDirection' in
             inputs["SpinEchoNegative"]['object']['info'].keys())
        ):
            pedirSE1 = \
                inputs["SpinEchoPositive"]['object']['info']['PhaseEncodingDirection']
            pedirSE2 = \
                inputs["SpinEchoNegative"]['object']['info']['PhaseEncodingDirection']
            pedirSE1 = tr("ijk", "xyz", pedirSE1)
            pedirSE2 = tr("ijk", "xyz", pedirSE2)
            if pedirSE1 == pedirSE2:
                raise Exception(
                    "SpinEchoPositive and SpinEchoNegative have the same \
                        PhaseEncodingDirection " + str(pedirSE1) + " !")
            if (
               not (( (pedirSE1, pedirSE2) == ("x", "x-")) or
                ( (pedirSE1, pedirSE2) ==  ("y","y-") )) and
               not (( (pedirSE1, pedirSE2) ==  ("x-", "x")) or
                ( (pedirSE1, pedirSE2) ==  ("y-","y")))
            ):
                    raise Exception(
                        "Unrecognized SpinEcho phase-encoding directions " +
                        str(pedirSE1) + ", " + str(pedirSE2) + ".")
        else:
            raise Exception(
                "SpinEchoPositive or SpinEchoNegative input \
                is missing PhaseEncodingDirection metadata!")
    elif "GeneralElectricFieldMap" in inputs.keys():
        raise Exception("Cannot currently handle GeneralElectricFieldmap!")


def execute(context):
    # We want to take care of delivering the directory structure right away
    # when we unzip the hcp-struct zip
    environ = context.custom_dict['environ']
    config = context.config
    os.makedirs(context.work_dir+'/'+ config['Subject'], exist_ok=True)

    # Start by building command to execute
    command = []
    command.extend(context.custom_dict['command_common'])
    command.append(
               op.join(environ['HCPPIPEDIR'],'fMRISurface'
               'GenericfMRIVolumeProcessingPipeline.sh')
               )
    command = build_command_list(command,context.custom_dict['Vol-params'])

    stdout_msg = 'Pipeline logs (stdout, stderr) will be available ' + \
                 'in the file "pipeline_logs.zip" upon completion.'

    context.log.info('GenericfMRIVolumeProcessingPipeline command: \n')
    exec_command(context,command,stdout_msg = stdout_msg)
