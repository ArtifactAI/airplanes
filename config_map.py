import pandas as pd
import os

curr_dir = os.path.dirname(os.path.abspath(__file__))
config_table_path = os.path.join(curr_dir, 'config_table.csv')
map_table = pd.read_csv(config_table_path) 