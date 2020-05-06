"""
Builds, validates, and excecutes parameters for the HCP script 
/opt/HCP-Pipelines/fMRIVolume/GenericfMRIVolumeProcessingPipeline.sh
part of the hcp-func gear
"""
import logging
import os
import os.path as op
import re
from collections import OrderedDict

from tr import tr

from .common import build_command_list, exec_command

log = logging.getLogger(__name__)


def build(context):
    config = context.config
    inputs = context._invocation['inputs']
    environ = context.gear_dict['environ']

    params = OrderedDict()

    # Initialize parameters.
    # 'unwarpdir' must be correctly derived from metadata
    params['unwarpdir'] = ""
    # use "FLIRT" to run FLIRT-based mcflirt_acc.sh, or "MCFLIRT" to
    # run MCFLIRT-based mcflirt.sh
    params['mctype'] = "MCFLIRT"
    # Initialize "NONE"s
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
    # this is set in utils/gear_preliminaries.py:set_subject.
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

    if 'PhaseEncodingDirection' in obj['info'].keys():
        params['unwarpdir'] = tr("ijk", "xyz",
                                 obj['info']['PhaseEncodingDirection'])

    # TODO: **??config option??** #generally "2", but "1.60" an option
    params['fmrires'] = "2"

    params['biascorrection'] = config['BiasCorrection']

    params['mctype'] = config['MotionCorrection']

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
        params['topupconfig'] = "NONE"

        if (
            ('EchoTime' in inputs["SiemensGREMagnitude"]['object']['info'].keys()) and
            ('EchoTime' in inputs["SiemensGREPhase"]['object']['info'].keys())
        ):
            echotime1 = inputs["SiemensGREMagnitude"]['object']['info']['EchoTime']
            echotime2 = inputs["SiemensGREPhase"]['object']['info']['EchoTime']
            params['echodiff'] = (echotime2 - echotime1) * 1000.0
            params['echodiff'] = format(params['echodiff'], '.15f')
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

            pedirfMRI_plane = re.sub(r'[+-]', '', params['unwarpdir'])

            # NOT USED: pedirSE_plane = re.sub(r'[+-]','', pedirSE1)

            # Check SpinEcho phase-encoding directions
            if (
                ((pedirfMRI_plane, pedirSE1, pedirSE2) == ("x", "x", "x-")) or
                ((pedirfMRI_plane, pedirSE1, pedirSE2) == ("y", "y", "y-"))
            ):
                params['SEPhasePos'] = SpinEchoPhase1
                params['SEPhaseNeg'] = SpinEchoPhase2
            elif (
                ((pedirfMRI_plane, pedirSE1, pedirSE2) == ("x", "x-", "x")) or
                ((pedirfMRI_plane, pedirSE1, pedirSE2) == ("y", "y-", "y"))
            ):
                params['SEPhasePos'] = SpinEchoPhase2
                params['SEPhaseNeg'] = SpinEchoPhase1
                log.warning(
                    "SpinEcho phase-encoding directions were swapped. \
                        Continuing!")
            # The following parameter is not used.
            # params['seunwarpdir'] = pedirSE_plane
        else:
            raise Exception(
                "The 'PhaseEncodingDirection' field not found in the " +
                "'SpinEchoPositive' or 'SpinEchoPositive' Inputs."
            )
    # Else if General Electric Field Map
    elif "GeneralElectricFieldMap" in inputs.keys():
        # TODO: how do we handle GE fieldmap? where do we get deltaTE?
        raise Exception("Cannot currently handle GeneralElectricFieldmap!")

    if 'GradientCoeff' in inputs.keys():
        params['gdcoeffs'] = context.get_input_path('GradientCoeff')

    params['printcom'] = " "

    context.gear_dict['Vol-params'] = params


def validate(context):
    """
    Ensure that the fMRI Volume Processing Parameters are valid.
    Raise Exceptions and exit if not valid.
    """

    params = context.gear_dict['Vol-params']
    inputs = context._invocation['inputs']

    # A Distortion Correction method is reauired for fMRI Volume Processing
    if params['dcmethod'] == "NONE":
        raise Exception(
            'Distortion Correction must be either "TOPUP" or ' +
            '"SiemensFieldMap" to proceed with fMRI Volume Processing.' +
            'Please provide valid Spin Echo Positive/Negative or ' +
            'Siemens GRE Phase/Magnitude field maps.'
        )

    # Ensure that SE-Based BiasCorrection is only used with TOPUP
    # Distortion Correction
    if (params['dcmethod'] != "TOPUP") and (params['biascorrection'] == 'SEBased'):
        raise Exception('SE-Based BiasCorrection only available when ' +
                        'providing Pos and Neg SpinEchoFieldMap scans')

    # Make sure that the user has not tried to use ">1 CASE":
    # "^" is the exclusive or (XOR) operator
    if (not (
        (
            ('SpinEchoNegative' in inputs.keys()) and
            ('SpinEchoPositive' in inputs.keys())
        ) ^
        (
            ('SiemensGREMagnitude' in inputs.keys()) and
            ('SiemensGREPhase' in inputs.keys())
        )
    )
    ):
        raise Exception(
            "Please use only one of Siemens Field Map, TopUp, or " +
            "General Electric Field Map."
        )
    # Examine Siemens Field Map input
    elif (
        ('SiemensGREMagnitude' in inputs.keys()) and
        ('SiemensGREPhase' in inputs.keys())
    ):

        if params['echodiff'] == 0:
            raise Exception(
                'EchoTime1 and EchoTime2 are the same \
                    (Please ensure Magnitude input is TE1)! Exiting.')
        elif params['echodiff'] == 'NONE':
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

            pedirfMRI_plane = re.sub(r'[+-]', '', params['unwarpdir'])

            # Check SpinEcho phase-encoding directions
            if not (
                ((pedirfMRI_plane, pedirSE1, pedirSE2) == ("x", "x", "x-")) or
                ((pedirfMRI_plane, pedirSE1, pedirSE2) == ("y", "y", "y-")) or
                ((pedirfMRI_plane, pedirSE1, pedirSE2) == ("x", "x-", "x")) or
                ((pedirfMRI_plane, pedirSE1, pedirSE2) == ("y", "y-", "y"))
            ):
                raise Exception(
                    "SpinEcho phase-encoding directions " +
                    "({},{}) ".format(pedirSE1, pedirSE2) +
                    "invalid or do not match fMRI acquisition " +
                    "plane ({}).".format(pedirfMRI_plane)
                )

    elif "GeneralElectricFieldMap" in inputs.keys():
        raise Exception("Cannot currently handle GeneralElectricFieldmap!")


def execute(context):
    # We want to take care of delivering the directory structure right away
    # when we unzip the hcp-struct zip
    environ = context.gear_dict['environ']
    config = context.config
    os.makedirs(context.work_dir+'/' + config['Subject'], exist_ok=True)

    # Start by building command to execute
    command = []
    command.extend(context.gear_dict['command_common'])
    command.append(
        op.join(environ['HCPPIPEDIR'], 'fMRIVolume',
                'GenericfMRIVolumeProcessingPipeline.sh')
    )
    command = build_command_list(command, context.gear_dict['Vol-params'])

    stdout_msg = 'Pipeline logs (stdout, stderr) will be available ' + \
                 'in the file "pipeline_logs.zip" upon completion.'

    log.info('GenericfMRIVolumeProcessingPipeline command: \n')
    exec_command(context, command, stdout_msg=stdout_msg)
