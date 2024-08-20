import unittest
import json
from esp import make_esp_input

class TestESP(unittest.TestCase):
    def test_make_esp_input(self):
        # Load sample configuration
        with open('configurations/basic_uav.json') as f:
            config = json.load(f)
        
        # Call the function to test
        esp_files = make_esp_input(config)

        # Assert that esp_files is a dictionary
        self.assertIsInstance(esp_files, dict)

        # Assert that each value in esp_files is not empty
        for key, value in esp_files.items():
            self.assertIsInstance(value, str)
            self.assertTrue(value.strip(), f"The content for '{key}' is empty")

        # Print the keys of esp_files for debugging
        print(f"ESP files generated: {list(esp_files.keys())}")

if __name__ == '__main__':
    unittest.main()
