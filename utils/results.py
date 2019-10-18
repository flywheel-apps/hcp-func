import os, os.path as op
import json
import subprocess as sp
from zipfile import ZipFile, ZIP_DEFLATED
import shutil
import glob


# ################################################################################
# # Clean-up and prepare outputs

def save_config(context):
    # Add current gear config.json to output for reference in subsequent gears
    # - For now, don't copy full input json since it might contain identifiers from DICOM etc
    # - add/update .config.RegName since it might not have been included in config (pre-MSM availability)
    # - add/update .config.Subject since it might later be pulled from other session metadata
    # - This jq call does the value replacement, then selects just .config but stores it back into a
    #    new element called ".config" so the new file can be read as though it was flywheel config.json
    config = {}
    hcpstruct_config={'config': config}
    for key in [
        'RegName',
        'Subject',
        'fMRIName',
        'BiasCorrection',
        'MotionCorrection',
        'AnatomyRegDOF'
    ]:
        if key in context.config.keys():
            config[key]=context.config[key]
    
    config['FinalfMRIResolution'] = \
                context.gear_dict['Surf-params']['fmrires']
    config['GrayordinatesResolution'] = \
         context.gear_dict['Surf-params']['grayordinatesres']
    config['LowResMesh'] = \
         context.gear_dict['Surf-params']['lowresmesh']
    config['SmoothingFWHM'] = \
         context.gear_dict['Surf-params']['smoothingFWHM']

    with open(op.join(
                context.work_dir,context.config['Subject'],
                '{}_{}_hcpfunc_config.json'.format(
                    context.config['Subject'],
                    context.config['fMRIName']
                )
            ),'w') as f:
        json.dump(hcpstruct_config, f, indent=4)

def preserve_whitelist_files(context):
    for fl in context.gear_dict['whitelist']:
        if not context.gear_dict['dry-run']:
            context.log.info('Copying file to output: {}'.format(fl))
            shutil.copy(fl,context.output_dir)


# # If pipeline successful, zip outputs and clean up
# outputzipname=${Subject}_${fMRIName}_hcpfunc.zip
# echo -e "${CONTAINER} [$(timestamp)] Zipping output file ${outputzipname}"
# ziplistfile=${OUTPUT_DIR}/${outputzipname}.list.txt
# rm -f ${ziplistfile}
# rm -f ${OUTPUT_DIR}/${outputzipname}
# cd ${StudyFolder}
# # include all remaining files in functional output zip
# find ${Subject} -type f > ${ziplistfile}
# cat ${ziplistfile} | zip ${OUTPUT_DIR}/${outputzipname} -@ > ${OUTPUT_DIR}/${outputzipname}.log
# rm -f ${ziplistfile}   
def zip_output(context):
    config = context.config

    outputzipname= op.join(context.output_dir, 
      '{}_{}_hcpfunc.zip'.format(config['Subject'],config['fMRIName']))
    
    context.log.info('Zipping output file {}'.format(outputzipname))
    if not context.gear_dict['dry-run']:
        ##################Delete extraneous preprocessing files####################
        for dir in ['prevols','postvols']:
            try:
                shutil.rmtree(
                    op.join(
                        context.work_dir,
                        config['Subject'],
                        config['fMRIName'],
                        'OneStepResampling',
                        dir
                    )
                )
            except:
                pass

        del_niftis = glob.glob(
            op.join(
                context.work_dir,
                config['Subject'],
                config['fMRIName'],
                'MotionMatrices',
                '*.nii.gz'
            )
        )
        for nifti in del_niftis:
            os.remove(nifti)
        ############################################################################        
        try:
            os.remove(outputzipname)
        except:
            pass

        os.chdir(context.work_dir)
        outzip = ZipFile(outputzipname,'w',ZIP_DEFLATED)
        for root, _, files in os.walk(config['Subject']):
            for fl in files:
                fl_path = op.join(root,fl)
                if fl_path not in context.gear_dict['hcp_struct_list']:
                    outzip.write(fl_path)
        outzip.close()
# # zip pipeline logs
# logzipname=pipeline_logs.zip
# echo -e "${CONTAINER} [$(timestamp)] Zipping pipeline logs to ${logzipname}"
# cd ${OUTPUT_DIR}
# zip -r ${OUTPUT_DIR}/${logzipname} ${LogFileDir}/ > ${OUTPUT_DIR}/${logzipname}.log

def zip_pipeline_logs(context):
    # zip pipeline logs
    logzipname=op.join(context.output_dir, 'pipeline_logs.zip')
    context.log.info('Zipping pipeline logs to {}'.format(logzipname))
    
    try:
        os.remove(logzipname)
    except:
        pass

    os.chdir(context.work_dir)
    logzipfile = ZipFile(logzipname,'w',ZIP_DEFLATED)
    for root, _, files in os.walk('logs'):
        for fl in files:
            logzipfile.write(os.path.join(root, fl))

def cleanup(context):
    # Move all images to output directory
    # TODO: I can do this with a shutil...include hooks for "dry-run"
    try:
        command = 'cp '+ context.work_dir+'/*.png ' + context.output_dir + '/'
        p = sp.Popen(
            command,
            shell=True
        )
        p.communicate()
    except:
        context.log.error('There are no images to save.')
    save_config(context)
    zip_output(context)
    zip_pipeline_logs(context)
    preserve_whitelist_files(context)
    # Write Metadata to file
    if 'analysis' in context.gear_dict['metadata'].keys():
        info = context.gear_dict['metadata']['analysis']['info']
        ## TODO: The below is a work around until we get the .metadata.json 
        ## file functionality working
        # Initialize the flywheel client
        fw = context.client
        analysis_id = context.destination['id']
        # Update metadata
        analysis_object = fw.get(analysis_id)
        analysis_object.update_info(info)
    # List final directory to log
    context.log.info('Final output directory listing: \n')
    os.chdir(context.output_dir)
    duResults = sp.Popen('du -hs *',shell=True,stdout=sp.PIPE, stderr=sp.PIPE,
                universal_newlines=True)
    stdout, _ = duResults.communicate()
    context.log.info('\n' + stdout)           