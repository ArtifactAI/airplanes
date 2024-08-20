import unittest
import json
from datcom import make_datcom_input

class TestDatcom(unittest.TestCase):
    def test_make_esp_input(self):
        # Load sample configuration
        with open('configurations/basic_uav.json') as f:
            config = json.load(f)
        
        # Call the function to test
        datcom_input = make_datcom_input(config)

        # Assert that esp_files is a dictionary
        self.assertIsInstance(datcom_input, str)

        # Assert that each value in esp_files is not empty
        self.assertTrue(datcom_input.strip(), f"The content is empty")


if __name__ == '__main__':
    unittest.main()
