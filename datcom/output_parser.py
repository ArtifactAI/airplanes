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
        columns = []

        for line in lines:
            # find column header names. Column headers start with 0... ALPHA or 0... DELTA
            if re.match(r'^\s*0\s*ALPHA', line) or re.match(r'^\s*0\s*DELTA', line):
                columns = re.split(r'\s{2,}', re.sub(r'^\s*0\s*', '', line.strip()))
                break

        if set(list(main_table_columns.keys())) == set(columns):
            table_types.append('main')
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


def parse_main_table(table_content):
    lines = table_content.split('\n')
    data = []
    column_names = list(main_table_columns.keys())
    start_index = None

    # Find the line where the data starts
    for i, line in enumerate(lines):
        if line.startswith('0 ALPHA'):
            start_index = i + 2
            break

    if start_index is not None:
        for line in lines[start_index:]:
            if line.startswith('0'):
                # End of the table has been reached
                break
            row = []
            start = 1  # Start after the first space
            for col, width in main_table_columns.items():
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

    # Check if CYB and CNB columns have a value in the first row but NaN after
    # Datcom will only populate the first row if CYB and CNB are indepedent of alpha
    for col in ['CYB', 'CNB']:
        if col in df.columns:
            first_value = df[col].iloc[0]
            if pd.notna(first_value) and df[col].iloc[1:].isna().all():
                df[col] = first_value

    return df

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
        if table_type == 'main':
            df = parse_main_table(table)
            dataframes.append(df)
            metadata.append(get_table_metadata(table))