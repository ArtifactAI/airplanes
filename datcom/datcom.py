import pandas as pd
import numpy as np

from config_map import map_table

def format_datcom_input(file_path=None, text=None):
    # Adds initial space to namelist lines, if it doesn't exist.
    # Breaks namelist lines that are in excess of 80 characters at the last comma.
    # Returns the formatted string or writes it to a file, depending on if file_path is provided.

    if text is not None:
        lines = text.splitlines()
    elif file_path is not None:
        with open(file_path, 'r') as file:
            lines = file.readlines()
    else:
        raise ValueError("Either file_path or text must be provided")

    formatted_lines = []
    for line in lines:
        line = line.rstrip()
        if line.startswith('$') and not line.startswith(' $'):
            line = ' ' + line
        if len(line) <= 80:
            formatted_lines.append(line)
        else:
            while len(line) > 80:
                break_index = line[:80].rfind(',')
                if break_index == -1:
                    break_index = 80
                formatted_lines.append(line[:break_index + 1])
                line = ' ' + line[break_index + 1:].strip()
            if line:
                formatted_lines.append(line)

    if file_path is not None:
        with open(file_path, 'w') as file:
            for line in formatted_lines:
                file.write(line + '\n')
    else:
        return '\n'.join(formatted_lines)


def compile_namelist_fltcon(config_json):
    flight_cond = config_json['flight_condition']

    if 'mach_numbers' in flight_cond:
        speeds = flight_cond['mach_numbers']
        speed_type = 'mach'
    elif 'velocities' in flight_cond:
        speeds = flight_cond['velocities']
        speed_type = 'velocity'

    altitudes = flight_cond['altitudes']
    alphas = flight_cond['alpha']

    datcom_str = f" $FLTCON NMACH={len(speeds):.1f}, NALT={len(altitudes):.1f}"
    if speed_type == 'mach':
        datcom_str += f", MACH(1)={', '.join(f'{m:.1f}' for m in speeds)}"
    elif speed_type == 'velocity':
        datcom_str += f", VINF(1)={', '.join(f'{v:.1f}' for v in speeds)}"

    datcom_str += f", NALT={len(altitudes):.1f}, ALT(1)={', '.join(f'{a:.1f}' for a in altitudes)}"
    datcom_str += f", NALPHA={len(alphas):.1f}, ALSCHD(1)={', '.join(f'{a:.1f}' for a in alphas)}"
    datcom_str +='$'

    return format_datcom_input(text=datcom_str) + '\n'

def compile_planform_namelist(namelist_map, config_json):
    # Used for WGPLNF, HTPLNF, and (maybe VPLNF)
    # namelist_map is a table that contains the vehicle config json category and keys for each datcom parameter in the namelist

    namelist = namelist_map['datcom_namelist'].iloc[0]

    # Collect a list of unique json_category entries in this namelist_map
    unique_categories = namelist_map['json_category'].unique().tolist()

    if not any(category in config_json for category in unique_categories):
        return ""
    
    outboard_chord = 0
    for category in unique_categories:
        if "outboard_panel_chord" in config_json[category]:
            outboard_chord = config_json[category]["outboard_panel_chord"]
            break

    # By default, the wing is defined by the inboard panel. If there is an outboard panel, then that chord (the tip chord) will be set, meaning there is an inboard AND outboard panel.
    has_outboard_panel = outboard_chord > 0 

    chords_settled = False
    semispan_settled = False
    dihedral_settled = False
    sweep_settled = False

    parameter_strs = []
    # get the vehicle config parameter associated with the datom parameter
    for index, row in namelist_map.iterrows():

        if row['json_category'] not in config_json or row['json_key'] not in config_json[row['json_category']]:
            # skip this parameter if it's not in the vehicle config json
            continue

        datcom_parameter = row['datcom_parameter']

        if datcom_parameter == 'SSPNOP' or datcom_parameter == 'SSPN':
            if semispan_settled is False:
                if has_outboard_panel:
                    parameter_strs.append(f"SSPNOP={config_json[row['json_category']]['outboard_panel_semispan']:.1f}")   
                    SSPN_value = config_json[row['json_category']]['inboard_panel_semispan'] + config_json[row['json_category']]['outboard_panel_semispan'] 
                else:
                    SSPN_value = config_json[row['json_category']]['inboard_panel_semispan']

                # TODO: This is a hack. Need to compute the actual exposed semispan value from vehicle geometry.
                # Compute exposed semispan by subtracting body half-width from the semispan
                parameter_strs.append(f"SSPNE={0.95*SSPN_value:.1f}")    
                parameter_strs.append(f"SSPN={SSPN_value:.1f}")    
                semispan_settled = True

        elif datcom_parameter == 'CHRDBP' or datcom_parameter == 'CHRDTP':
            if chords_settled is False:
                if has_outboard_panel:
                    CHRDTP_value = config_json[row['json_category']]['outboard_panel_chord']
                    CHRDBP_value = config_json[row['json_category']]['inboard_panel_chord']
                    parameter_strs.append(f"CHRDBP={CHRDBP_value:.2f}") 
                else:
                    CHRDTP_value = config_json[row['json_category']]['inboard_panel_chord']
                    
                parameter_strs.append(f"CHRDTP={CHRDTP_value:.2f}")  
                chords_settled = True

        elif datcom_parameter == 'DHDADI' or datcom_parameter == 'DHDADO':
            if dihedral_settled is False:
                if has_outboard_panel:
                    DHDADO_value = config_json[row['json_category']]['outboard_panel_dihedral']
                    parameter_strs.append(f"DHDADO={DHDADO_value:.1f}")    
                    #SSPNDD: semispan of outboard panel with dihedral:
                    SSPNDD_value = config_json[row['json_category']]['outboard_panel_semispan'] * np.cos(np.radians(DHDADO_value))
                    parameter_strs.append(f"SSPNDD={SSPNDD_value:.1f}")    

                DHDADI_value = config_json[row['json_category']]['inboard_panel_dihedral']
                parameter_strs.append(f"DHDADI={DHDADI_value:.1f}")    
                dihedral_settled = True

        elif datcom_parameter == 'SAVSO' or datcom_parameter == 'SAVSI':
            if sweep_settled is False:
                if has_outboard_panel:
                    SAVSO_value = config_json[row['json_category']]['outboard_panel_sweep']
                    parameter_strs.append(f"SAVSO={SAVSO_value:.1f}")    

                SAVSI_value = config_json[row['json_category']]['inboard_panel_sweep']
                parameter_strs.append(f"SAVSI={SAVSI_value:.1f}")    
                sweep_settled = True

        else:
            datcom_value = config_json[row['json_category']][row['json_key']]
            parameter_strs.append(f"{datcom_parameter}={datcom_value:.4f}")    

    if namelist in ['HTPLNF', 'VTPLNF', 'VFPLNF']:
        parameter_strs.append(f"TYPE=1.0")

    namelist_str = " $" + namelist + " " + ", ".join(parameter_strs) + '$'
    return format_datcom_input(text=namelist_str) + '\n'

def compile_section_namelist(namelist_map, config_json):
    # Check special case where NACA 4-digit airfoil is used to define the section
    # This is the only case currently supported

    unique_categories = namelist_map['json_category'].unique().tolist()
    if not any(category in config_json for category in unique_categories):
        return ""
    
    namelist = namelist_map['datcom_namelist'].iloc[0]

    namelist_str = ""

    if namelist == 'WGSCHR':
        namelist_str += "NACA-W-4-" + config_json['wing_section']['naca_4_series_code']
    elif namelist == 'HTSCHR':
        namelist_str += "NACA-H-4-" + config_json['horizontal_tail_section']['naca_4_series_code']
    elif namelist == 'VTSCHR':
        namelist_str += "NACA-V-4-" + config_json['vertical_tail_section']['naca_4_series_code']
    elif namelist == 'VFSCHR':
        namelist_str += "NACA-F-4-" + config_json['vertical_fin_section']['naca_4_series_code']

    return namelist_str + '\n'

def compile_body_namelist(config_json):
    x_stations = config_json['fuselage']['x_stations']
    half_widths = config_json['fuselage']['half_widths']
    ellipse_ratios = config_json['fuselage']['ellipse_ratios']
    axis_offsets = config_json['fuselage']['axis_offsets']

    parameter_strs = []
    parameter_strs.append(f" X(1)={', '.join(f'{x:.1f}' for x in x_stations)}")
    parameter_strs.append(f" R(1)={', '.join(f'{r:.2f}' for r in half_widths)}")
    
    half_heights = abs(np.array(half_widths) * np.array(ellipse_ratios))
    zl = -half_heights + axis_offsets
    zu = half_heights + axis_offsets

    parameter_strs.append(f" ZL(1)={', '.join(f'{z:.2f}' for z in zl)}")
    parameter_strs.append(f" ZU(1)={', '.join(f'{z:.2f}' for z in zu)}")

    namelist_str = f" $BODY NX={len(x_stations):.1f},\n" + ",\n".join(parameter_strs) + '$'
    return format_datcom_input(text=namelist_str) + '\n'

def compile_control_surface_namelist(namelist_map, config_json, surface_type):
    # Used for WGFLNF, HTPLNF, and (maybe VPLNF)
    # namelist_map is a table that contains the vehicle config json category and keys for each datcom parameter in the namelist

    namelist = namelist_map['datcom_namelist'].iloc[0]
    parameter_strs = []

    for index, row in namelist_map.iterrows():

        if row['json_category'] == surface_type:
            if row['json_key'] == 'deflections':
                parameter_strs.append(f"NDELTA={len(config_json[surface_type]['deflections']):.1f}")
                parameter_value = config_json[surface_type]['deflections']
                parameter_strs.append(f"{row['datcom_parameter']}(1)={', '.join(f'{p:.1f}' for p in parameter_value)}")
            elif row['json_key'] == 'differential_deflections':
                parameter_strs.append(f"NDELTA={len(config_json[surface_type]['differential_deflections']):.1f}")
                parameter_value = config_json[surface_type]['differential_deflections']
                parameter_strs.append(f"DELTAL(1)={', '.join(f'{p:.1f}' for p in parameter_value)}")
                parameter_strs.append(f"DELTAR(1)={', '.join(f'{-p:.1f}' for p in parameter_value)}")
            else:
                parameter_strs.append(f"{row['datcom_parameter']}={config_json[surface_type][row['json_key']]:.3f}")

    #TODO: allow different types of flaps and ailerons
    if surface_type in ['flaps', 'elevator']:
        parameter_strs.append("NTYPE=1.0")
        parameter_strs.append("FTYPE=1.0")
    elif surface_type == 'ailerons':
        parameter_strs.append("STYPE=4.0")

    namelist_str = " $" + namelist + " " + ", ".join(parameter_strs) + '$'
    return format_datcom_input(text=namelist_str) + '\n'


def compile_namelist(namelist_map, config_json):
    # namelist_map is a table that contains the vehicle config json category and keys for each datcom parameter in the namelist
    namelist = namelist_map['datcom_namelist'].iloc[0]
    parameter_strs = []

    for index, row in namelist_map.iterrows():

        if row['json_category'] not in config_json or row['json_key'] not in config_json[row['json_category']]:
            # skip this parameter if it's not in the vehicle config json
            continue

        parameter_value = config_json[row['json_category']][row['json_key']]

        if isinstance(parameter_value, (list, tuple)):
            parameter_strs.append(
                f"{row['datcom_parameter']}(1)={', '.join(f'{p:.1f}' for p in parameter_value)}"
            )
        else:
            parameter_strs.append(
                f"{row['datcom_parameter']}={parameter_value:.1f}"
            )

    if parameter_strs: 
        namelist_str = " $" + namelist + " " + ", ".join(parameter_strs) + '$'
        namelist_str = format_datcom_input(text=namelist_str) + '\n'
    else:
        namelist_str = ""

    return namelist_str

def make_datcom_input(vehicle_config):
    namelists = map_table['datcom_namelist'].unique().tolist()
    
    fltcon_str = ""
    synths_optins_str = ""
    body_str = ""
    wing_str = ""
    empannage_str = ""
    flaps_str = ""
    ailerons_str = ""
    elevator_str = ""

    datcom_str = ""
    control_surfaces = [False, False, False] # [flaps, elevator, ailerons]

    for namelist in namelists:
        namelist_map = map_table.groupby('datcom_namelist').get_group(namelist)

        # Compilation happens in a specific order since the "SAVE" and "NEXT CASE" cards are used when control surfaces are present
        if namelist == 'FLTCON':
            fltcon_str += compile_namelist_fltcon(vehicle_config)
        elif namelist in ['SYNTHS', 'OPTINS']:
            synths_optins_str += compile_namelist(namelist_map, vehicle_config)
        elif namelist in['BODY']:
            body_str += compile_body_namelist(vehicle_config)
        elif namelist == 'WGPLNF':
            wing_str += compile_planform_namelist(namelist_map, vehicle_config)
        elif namelist == 'WGSCHR':
            wing_str += compile_section_namelist(namelist_map, vehicle_config)
        elif namelist in ['HTPLNF', 'VTPLNF', 'VFPLNF']:
            empannage_str += compile_planform_namelist(namelist_map, vehicle_config)
        elif namelist in ['HTSCHR', 'VTSCHR', 'VFSCHR']:
            empannage_str += compile_section_namelist(namelist_map, vehicle_config)
        elif namelist == 'SYMFLP': 
            if 'flaps' in vehicle_config and vehicle_config['flaps']['inboard_chord'] > 0:
                control_surfaces[0] = True
                flaps_str += compile_control_surface_namelist(namelist_map, vehicle_config, 'flaps')
            if 'elevator' in vehicle_config and vehicle_config['elevator']['inboard_chord'] > 0:
                control_surfaces[1] = True
                elevator_str += compile_control_surface_namelist(namelist_map, vehicle_config, 'elevator')
        elif namelist == 'ASYFLP' and 'ailerons' in vehicle_config and vehicle_config['ailerons']['inboard_chord'] > 0:
            control_surfaces[2] = True
            ailerons_str += compile_control_surface_namelist(namelist_map, vehicle_config, 'ailerons')
  
    datcom_str = fltcon_str + synths_optins_str + body_str + wing_str 
    
    if control_surfaces == [True, False, False]:
        # If just flaps, the empannage must be done in a separate case since SYMFLP is assigned to the aft-most lifting surface
        datcom_str += flaps_str
        datcom_str += "SAVE\nNEXT CASE\nCASEID ADD EMPANNAGE\n"
    elif control_surfaces == [False, True, False]:
        datcom_str += elevator_str
    elif control_surfaces == [False, False, True]:
        datcom_str += ailerons_str
    elif control_surfaces == [True, True, False]:
        datcom_str += flaps_str
        datcom_str += "SAVE\nNEXT CASE\nCASEID ADD ELEVATOR AND EMPANNAGE\n"
        datcom_str += elevator_str
    elif control_surfaces == [True, False, True]:
        datcom_str += flaps_str
        datcom_str += "SAVE\nNEXT CASE\nCASEID ADD AILERONS AND EMPANNAGE\n"
        datcom_str += ailerons_str
    elif control_surfaces == [False, True, True]:
        datcom_str += ailerons_str
        datcom_str += "SAVE\nNEXT CASE\nCASEID ADD AILERONS AND EMPANNAGE\n"
        datcom_str += elevator_str
    elif control_surfaces == [True, True, True]:
        datcom_str += flaps_str
        datcom_str += "SAVE\nNEXT CASE\nCASEID ADD AILERONS\n"
        datcom_str += ailerons_str
        datcom_str += "SAVE\nNEXT CASE\nCASEID ADD ELEVATOR AND EMPANNAGE\n"
        datcom_str += elevator_str

    datcom_str += empannage_str
    return datcom_str

async def run_datcom_executable(input_file_path, output_file_path):
        # Run the datcom executable and save the .out file in the same directory as the input file
        import os, subprocess

        # Extract the directory containing the input file
        output_file_dir = os.path.dirname(output_file_path)

        # Location of datcom executable packaged with the application
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Determine the correct executable based on the operating system
        if os.name == 'nt':  # Windows
            datcom_executable_path = os.path.join(current_dir, "datcom_win.exe")
        else:  # macOS or other
            datcom_executable_path = os.path.join(current_dir, "datcom_mac.exe")
        
        os.chdir(output_file_dir)
        process = subprocess.Popen([datcom_executable_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Send the input file path when prompted
        output, errors = process.communicate(input=input_file_path)

        if process.returncode == 0:
            print("DATCOM execution successful.")
            print("Output:", output)
        else:
            print("Error in DATCOM execution")
            print("Errors:", errors)

        # Delete any 'for*.dat' files in the input_file_dir
        for file in os.listdir(output_file_dir):
            if file.startswith('for') and file.endswith('.dat'):
                os.remove(os.path.join(output_file_dir, file)) # Delete any 'for*.dat' files in the default_save_dir
                print(f"Deleted {file}")