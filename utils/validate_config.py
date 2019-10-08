import json
from zipfile import ZipFile

def preprocess_hcp_struct_zip(context):
    # Grab the whole file list from the hcp-struct zip,
    # put it in a list to parse through. So these will be the files 
    # that do not get compressed into the hcp-func output
    hcp_struct_zip = context.get_input_path('StructZip')
    hcp_struct_list = []
    hcp_struct_config = {}
    zf = ZipFile(hcp_struct_zip)
    for fl in zf.filelist:
        if not fl.is_dir():
            hcp_struct_list.append(fl.filename)
            # grab exported hcp-struct config
            if 'hcpstruct_config.json' in fl.filename:
                json_file = zf.open(fl.filename)
                hcp_struct_config = json.load(json_file)
    
    if len(hcp_struct_config) == 0:
        raise Exception( 
            'Could not find the hcp-struct configuration within the ' + \
            'exported zip-file, {}.'.format(context.get_input_path('StructZip'))
        )
        
    context.custom_dict['hcp_struct_list'] = hcp_struct_list
    context.custom_dict['hcp_struct_config'] = hcp_struct_config    

def validate_config_against_manifest(context):
    """
    This function compares the automatically produced configuration file (config.json)
    to the contstraints listed in the manifest (manifest.json). This adds a layer
    of redundancy and transparency to that the process in the web-gui and the SDK.
    This function:
    - checks for the existence of required inputs and the file type of all inputs
    - checks for the ranges of values on config parameters
    - checks for the length of arrays submitted
    """
    c_config = context.config
    manifest = json.load(open('/flywheel/v0/manifest.json','r',errors='ignore'))
    m_config = manifest['config']
    errors = []
    if 'config' in manifest.keys():
        for key in m_config.keys():
            m_item = m_config[key]
            # Check if config value is optional
            if key not in c_config.keys():
                if 'optional' not in m_item.keys():
                    errors.append(
                        'The config parameter, {}, is not optional.'.format(key)
                    )
                elif not m_item['optional']:
                    errors.append(
                        'The config parameter, {}, is not optional.'.format(key)
                    )
            else:
                c_val = c_config[key]
                if 'maximum' in m_item.keys():
                    if c_val > m_item['maximum']:
                        errors.append(
                            'The value of {}, {}, exceeds '.format(key,c_val) + \
                            'the maximum of {}.'.format(m_item['maximum'])
                        )
                if 'minimum' in m_item.keys():
                    if c_val < m_item['minimum']:
                        errors.append(
                            'The value of {}, {}, is less than '.format(key,c_val) + \
                            'the minimum of {}.'.format(m_item['minimum'])
                        )
                if 'items' in m_item.keys():
                    if 'maxItems' in m_item['items'].keys():
                        maxItems = m_item['items']['maxItems']
                        if len (c_val) > maxItems:
                            errors.append(
                                'The array {} has {} '.format(key,len(c_val)) + \
                                'elements. More than the {} '.format(maxItems) + \
                                'required.'
                            )
                    if 'minItems' in m_item['items'].keys():
                        minItems = m_item['items']['minItems']
                        if len (c_val) > minItems:
                            errors.append(
                                'The array {} has {} '.format(key,len(c_val)) + \
                                'elements. Less than the {} '.format(minItems) + \
                                'required.'
                            )
    if 'inputs' in manifest.keys():
        c_inputs = context._invocation['inputs']
        m_inputs = manifest['inputs']
        for key in m_inputs.keys():
            # if a manifest input is not in the invocation inputs
            # check if it needs to be
            if key not in c_inputs.keys():
                m_input = m_inputs[key]
                if 'optional' not in m_input.keys():
                    errors.append(
                        'The input, {}, is not optional.'.format(key)
                    )
                elif not m_input['optional']:
                    errors.append(
                        'The input, {}, is not optional.'.format(key)
                    )
            # Or if it is there, check to see if it is the right type
            elif 'type' in m_inputs[key].keys():
                m_f_type = m_inputs[key]['type']['enum'][0] ##??
                c_f_type = c_inputs[key]['object']['type']
                if m_f_type != c_f_type:
                    errors.append(
                    'The input, {}, '.format(key) + \
                    ' is a "{}" file.'.format(c_f_type) + \
                    ' It needs to be a "{}" file.'.format(m_f_type)
                    )
    if len(errors) > 0:
        raise Exception(
        'Your gear is not configured correctly: \n{}'.format('\n'.join(errors))
        )