import pandas as pd
import re

reference_data = ['mach', 'altitude', 'velocity', 'pressure', 'temperature', 'reynolds', 'S_ref', 'c_ref', 'b_ref', 'x_ref', 'z_ref']

main_table_columns = {
    'ALPHA': 9,
    'CD': 9,
    'CL': 9,
    'CM': 9,
    'CN': 9,
    'CA': 9,
    'XCP': 9,
    'CLA': 13,
    'CMA': 13,
    'CYB': 13,
    'CNB': 13,
    'CLB': 13
}

damping_table_columns = {
    'ALPHA': 9,
    'CLQ': 13,
    'CMQ': 13,
    'CLAD': 13,
    'CMAD': 13,
    'CLP': 13,
    'CYP': 13,
    'CNP': 13,
    'CNR': 13,
    'CLR': 13
}

symmetric_control_surface_columns = {
    'DELTA': 9,
    'CYB': 13,
    'CNB': 13,
    'CLB': 13
}

table type
starting regex
data_start_regex
column headers and widths dict

table_types = {
    'main': {
        'starting_regex': re.compile(r'1\s+AUTOMATED STABILITY AND CONTROL METHODS'),
        'column_headers_and_widths': main_table_columns
    }
}

def extract_tables(file_content):
    table_pattern = re.compile(r'1\s+AUTOMATED STABILITY AND CONTROL METHODS')
    end_pattern = re.compile(r'^1', re.MULTILINE)

    tables = []
    start_indices = [m.start() for m in table_pattern.finditer(file_content)]
    end_indices = []

    for start in start_indices:
        end_match = end_pattern.search(file_content, start + 1)
        end = end_match.start() if end_match else len(file_content)
        end_indices.append(end)
        tables.append(file_content[start:end])

    # start_line_numbers = [file_content.count('\n', 0, start) + 1 for start in start_indices]
    # end_line_numbers = [file_content.count('\n', 0, end) + 1 for end in end_indices]

    return tables

def get_table_type(tables):

    table_types = []

    for table in tables:
        lines = table.split('\n')

        if 'CHARACTERISTICS AT ANGLE OF ATTACK AND IN SIDESLIP' in lines[1]:
            table_types.append('main')
        elif 'DYNAMIC DERIVATIVES' in lines[1]:
            table_types.append('aero_damping')
        elif 'CHARACTERISTICS OF HIGH LIFT AND CONTROL DEVICES' in lines[1]:
            # determine if this table is for a symmetric or asymmetric control surface
            for line in lines:
                if re.match(r'^0\s+DELTA\s+', line):
                    table_types.append('symmetric_control_surface')
                    break
                elif re.match(r'^0\(DELTAL-DELTAR\)', line):
                    table_types.append('asymmetric_control_surface')
                    break
        else:
            table_types.append('unknown')

    return tables, table_types

def get_table_metadata(table):

    lines = table.split('\n')
    for index, line in enumerate(lines):
        if 'FLIGHT CONDITIONS' in line:
            break
    
    units_line = lines[index + 3]
    units = re.split(r'\s{2,}', units_line) # magically, this should capture the blank space that is the Mach number unit

    numbers_line = lines[index + 4]
    numbers_line = numbers_line.lstrip('0').strip()
    numbers = re.split(r'\s{2,}', numbers_line)

    metadata = {}
    for i, key in enumerate(reference_data):
        if i < len(units) and i < len(numbers):
            metadata[key] = {
                'value': numbers[i].strip(),
                'unit': units[i].strip()
            }
        else:
            metadata[key] = {
                'value': None,
                'unit': None
            }

    return metadata


def parse_table(table_content, table_type):
    lines = table_content.split('\n')
    data = []
    start_index = None

    if table_type == 'main':
        column_reference = main_table_columns
    elif table_type == 'damping':
        column_reference = damping_table_columns
        
    column_names = list(column_reference.keys())

    # Find the line where the data starts
    for i, line in enumerate(lines):
        if re.match(r'^0\s+ALPHA', line):
            start_index = i + 2
            break

    if start_index is not None:
        for line in lines[start_index:]:
            if line.startswith('0'):
                # End of the table has been reached 
                # TODO: include downwash data, which may be present after this line
                break
            row = []
            start = 1  # Start after the first space
            for col, width in column_reference.items():
                value = line[start:start+width].strip()
                row.append(value)
                start += width
            data.append(row)

    df = pd.DataFrame(data, columns=column_names)
    
    # Convert numeric columns to float
    for col in df.columns:
        df[col] = pd.to_numeric(df[col])

    # Remove rows where all values are NaN
    df = df.dropna(how='all')

    # Drop columns where the header is CLAD or CMAD
    # TODO: consider adding these damping derivatives back in; for most models, they don't exist
    df = df.drop(columns=['CLAD', 'CMAD'], errors='ignore')

    # Check if CYB and CNB columns have a value in the first row but NaN after
    # Datcom will only populate the first row if CYB and CNB are indepedent of alpha
    # TODO: check if this is also true for CLQ and CMQ
    for col in ['CYB', 'CNB', 'CLQ', 'CMQ']:
        if col in df.columns:
            first_value = df[col].iloc[0]
            if pd.notna(first_value) and df[col].iloc[1:].isna().all():
                df[col] = first_value

    return df

def parse_control_surfaces(table_content):
    lines = table_content.split('\n')
    data = []
    start_index = None

    column_names = ['DELTA', 'D_CL', 'D_CM', 'D_CL_max', 'D_CD_min']

    # Find the line where the data starts
    for i, line in enumerate(lines):
        if re.match(r'^0\s+DELTA', line):
            start_index = i + 3
            break
    
    if start_index is not None:
        for line in lines[start_index:]:
            if line.startswith('0'):
                # End of the table has been reached 
                break
            values = re.findall(r'\S+', line)
            values = values[:5] # TODO: add in (CLA)D, (CH)A, and (CH)D
            data.append(values)

        df = pd.DataFrame(data, columns=column_names) 

    next... get the second half of the table, with induced drag coefficient


    values = re.findall(r'\S+', line)
    # Find the line where the data starts
    for i, line in enumerate(lines):
        if table_type == 'symmetric_control_surface':
            if re.match(r'^0\s+DELTA\s+', line):
                start_index = i + 2
                break
        elif table_type == 'asymmetric_control_surface':
            if re.match(r'^0\s+ALPHA\s+', line):
                start_index = i + 2
                break


    for col in df.columns:
        df[col] = pd.to_numeric(df[col])


def parse_datcom_output(file_path):
    with open(file_path, 'r') as file:
        file_content = file.read()
    
    tables = extract_tables(file_content)
    tables, table_types = get_table_type(tables)

    dataframes = []

    for table, table_type in zip(tables, table_types):
        if table_type == 'main':
            df = parse_main_table(table)
            dataframes.append(df)

    return dataframes

if __name__ == "__main__":
    # tables = parse_datcom_output('datcom.out')
    file_path = 'datcom.out'

    with open(file_path, 'r') as file:
        file_content = file.read()
    tables = extract_tables(file_content)
    tables, table_types = get_table_type(tables)

    dataframes = []
    metadata = []

    for table, table_type in zip(tables, table_types):
        metadata.append(get_table_metadata(table))
        if table_type == 'main':
            df = parse_table(table, table_type)
            dataframes.append(df)
        elif table_type == 'aero_damping':
            df = parse_table(table, table_type)
            dataframes.append(df)
        else:
            dataframes.append(None)

# TODO: get the last main table. In the future, coordinate it with the input file buildup, but it should be the last.