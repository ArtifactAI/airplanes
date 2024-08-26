import unittest
import json
import pandas as pd
import numpy as np

from datcom import make_datcom_input
from datcom import parse_datcom_output
from datcom.aero_plots import pitch_plane_dataset, plot_pitch_plane
from datcom import aero_coefficients

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

# class TestAeroPlots(unittest.TestCase):
#     def setUp(self):
#         # Sample data for testing
#         self.alpha_range = [0, 5]
#         self.coefficients = [aero_coefficients(np.radians(alpha)) for alpha in self.alpha_range]

#     def test_pitch_plane_dataset(self):
#         drag, lift, pitching = pitch_plane_dataset(self.coefficients)
        
#         # Check lengths
#         self.assertEqual(len(drag), len(self.coefficients))
#         self.assertEqual(len(lift), len(self.coefficients))
#         self.assertEqual(len(pitching), len(self.coefficients))
        
#         # Check values
#         self.assertAlmostEqual(drag[0], -0.1)
#         self.assertAlmostEqual(lift[0], -0.2)
#         self.assertAlmostEqual(pitching[0], 0.01)

#     def test_plot_pitch_plane(self):
#         # This test ensures that the plotting function runs without errors
#         try:
#             plot_pitch_plane([self.coefficients], ['Test Label'])
#         except Exception as e:
#             self.fail(f"plot_pitch_plane raised an exception: {e}")

if __name__ == '__main__':
    unittest.main()
