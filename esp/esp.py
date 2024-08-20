import os
from typing import Union, Dict

from config_map import map_table

class ConfigError(Exception):
    pass

def save_file(path, contents):

    # Ensure the directory exists
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(path, 'w') as file:
        file.write(contents)

def make_esp_input(vehicle_config)-> Union[Dict[str, str], ConfigError]: 

    current_dir = os.path.dirname(os.path.abspath(__file__))
    # TODO: also generate the master .csm file based on which components are included
    esp_boilerplate = {
        'wing': 'wing.csm',
        'htail': 'horizontal_tail.csm',
        'vtail': 'vertical_tail.csm',
        'vfin': 'vertical_fin.csm',
        'body': 'body.csm'
    }

    esp_parameters = map_table.groupby('esp_category')
    esp_files = {}
    csm_str = ""

    for category in esp_boilerplate.keys():
        component_exists = False
        parameters = esp_parameters.get_group(category)
        udc_str = ""

        # Specify if control surfaces exist
        if category == 'wing':
            if 'flaps' in vehicle_config and vehicle_config['flaps']['inboard_chord'] > 0:
                udc_str += "SET       wing:has_flaps                1\n"
            else:
                udc_str += "SET       wing:has_flaps                0\n"
            if 'ailerons' in vehicle_config and vehicle_config['ailerons']['inboard_chord'] > 0:
                udc_str += "SET       wing:has_ailerons                1\n"
            else:
                udc_str += "SET       wing:has_ailerons                0\n"
        if category == 'htail':
            if 'elevator' in vehicle_config and vehicle_config['elevator']['inboard_chord'] > 0:
                udc_str += "SET       htail:has_elevator                1\n"
            else:
                udc_str += "SET       htail:has_elevator                0\n"

        # TODO: if "all_moving_tail" is true...

        for index, row in parameters.iterrows():

            if row['json_category'] not in vehicle_config:
                # skip this parameter if it's not in the vehicle config
                # TODO: make this more efficient so you don't have to check at every parameter
                continue
            else:
                component_exists = True

            try:
                parameter = vehicle_config[row['json_category']][row['json_key']]
            except KeyError:
                return ConfigError(f"{row['json_category']} {row['json_key']} does not exist in the vehicle configuration file. Please update.")
            
            if row['esp_category'] == 'body':
                # Body parameters are a set of arrays, so treat these differently
                if row['esp_parameter'] == 'x_stations':
                    udc_str = f"CONPMTR {'body:nstations'} {len(parameter)}\n" + udc_str
                
                udc_str += f"DIMENSION {category + ':' + row['esp_parameter']} 1 body:nstations\n"
                udc_str += f"DESPMTR   {category + ":" +row['esp_parameter']:<25} \"{'; '.join(map(str, parameter))}\"\n"
            else:
                udc_str += f"DESPMTR   {category + ":" +row['esp_parameter']:<25} {parameter}\n"

            if index == parameters.index[-1]:
                udc_str += "END\n"

        if component_exists:
            udc_str = "INTERFACE . all\n" + udc_str
            esp_files[category] = udc_str

            # copy boilerplate from locally defined .csm files
            csm_file_path = os.path.join(current_dir, esp_boilerplate[category])

            with open(csm_file_path, 'r') as csm_file:
                csm_content = csm_file.read()

            csm_str += csm_content + "\n"

    esp_files['airplane'] = csm_str

    aero_surface_script_file_path = os.path.join(current_dir, 'make_aero_surface.udc')
    control_surface_script_file_path = os.path.join(current_dir, 'make_control_surface.udc')
    body_script_file_path = os.path.join(current_dir, 'make_body.udc')

    with open(aero_surface_script_file_path, 'r') as aero_surface_script_file:
        aero_surface_script_content = aero_surface_script_file.read()

    with open(control_surface_script_file_path, 'r') as control_surface_script_file:
        control_surface_script_content = control_surface_script_file.read()

    with open(body_script_file_path, 'r') as body_script_file:
        body_script_content = body_script_file.read()

    esp_files['aero_surface_script'] = aero_surface_script_content
    esp_files['control_surface_script'] = control_surface_script_content
    esp_files['body_script'] = body_script_content

    return esp_files
