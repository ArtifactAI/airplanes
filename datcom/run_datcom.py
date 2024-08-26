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