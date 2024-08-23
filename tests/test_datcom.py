import unittest
import json
import pandas as pd

from datcom import make_datcom_input
from datcom import parse_datcom_output

class TestDatcom(unittest.TestCase):
    def test_make_datcom_input(self):
        # Load sample configuration
        with open('configurations/basic_uav.json') as f:
            config = json.load(f)
        
        # Call the function to test
        datcom_input = make_datcom_input(config)

        # Assert that esp_files is a dictionary
        self.assertIsInstance(datcom_input, str)

        # Assert that each value in esp_files is not empty
        self.assertTrue(datcom_input.strip(), f"The content is empty")

class TestDatcomOutputParser(unittest.TestCase):
    def test_parse_datcom_output(self):
        datcom_output = parse_datcom_output('./tests/data/datcom.out')

        required_fields = ['rigid_body_static', 'rigid_body_dynamic', 'elevator', 'ailerons']
        for field in required_fields:
            self.assertIn(field, datcom_output, f"'{field}' is missing from the output")
            if field == 'elevator':
                self.assertIsInstance(datcom_output[field]['coef_increments'], pd.DataFrame, f"'{field}' does not contain the required data")
                self.assertFalse(datcom_output[field]['coef_increments'].empty, f"'{field}' DataFrame is empty")
                self.assertIsInstance(datcom_output[field]['induced_drag_increments'], pd.DataFrame, f"'{field}' does not contain the required data")
                self.assertFalse(datcom_output[field]['induced_drag_increments'].empty, f"'{field}' DataFrame is empty")
            elif field == 'ailerons':
                self.assertIsInstance(datcom_output[field]['roll_coefficient'], pd.DataFrame, f"'{field}' does not contain the required data")
                self.assertFalse(datcom_output[field]['roll_coefficient'].empty, f"'{field}' DataFrame is empty")
                self.assertIsInstance(datcom_output[field]['yaw_coefficient'], pd.DataFrame, f"'{field}' does not contain the required data")
                self.assertFalse(datcom_output[field]['yaw_coefficient'].empty, f"'{field}' DataFrame is empty")
            else:
                self.assertIsInstance(datcom_output[field], pd.DataFrame, f"'{field}' is not a pandas DataFrame")
                self.assertFalse(datcom_output[field].empty, f"'{field}' DataFrame is empty")

        self.assertIsInstance(datcom_output, dict)


if __name__ == '__main__':
    unittest.main()
