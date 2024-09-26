import re
import os
import traceback           
DEFAULT_DIRECTORY = r"C:/Users/keith.ransom/OneDrive - Inspire Brands/Documents/Fortigate configs"

# Function to read configuration file
def read_config_file(file_path):
    full_path = os.path.join(DEFAULT_DIRECTORY, file_path)
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"File not found: {full_path}")
    
    with open(full_path, 'r') as file:
        return file.read().splitlines()

# Function to parse configuration file
def parse_config(lines):
    config = {}
    current_section = None
    current_subsection = None

    for line_num, line in enumerate(lines, start=1):
        line = line.strip()

        if line.startswith('config'):
            current_section = line.split(' ', 1)[1].strip()
            config[current_section] = {}
            current_subsection = 'global'  # Reset subsection when entering a new section
        elif line.startswith('edit'):
            parts = line.split(' ', 1)
            if len(parts) < 2:
                print(f"Warning: Malformed 'edit' line at line {line_num}: {line}")
                continue
            current_subsection = parts[1].strip('"')
            if current_section not in config:
                print(f"Warning: 'edit' without 'config' at line {line_num}: {line}")
                current_section = "unknown_section"
                config[current_section] = {}
            config[current_section][current_subsection] = {}
        elif line.startswith('set') or line.startswith('unset'):
            parts = line.split(' ', 2)
            if len(parts) < 3:
                print(f"Warning: Malformed 'set' or 'unset' line at line {line_num}: {line}")
                continue
            key = parts[1]
            value = parts[2].strip('"')
            config[current_section][current_subsection][key] = value

    return config
# Function to compare configurations
def compare_configs(config1, config2):
    differences = []

    for section in config1:
        if section not in config2:
            differences.append(f'Section {section} missing in config2')
            continue
        
        for subsection in config1[section]:
            if subsection not in config2[section]:
                differences.append(f'Subsection {subsection} in section {section} missing in config2')
                continue
            
            for key in config1[section][subsection]:
                if key not in config2[section][subsection]:
                    differences.append(f'Key {key} in subsection {subsection} of section {section} missing in config2')
                elif config1[section][subsection][key] != config2[section][subsection][key]:
                    differences.append(f'Value for key {key} in subsection {subsection} of section {section} differs:\n\tconfig1: {config1[section][subsection][key]}\n\tconfig2: {config2[section][subsection][key]}')

    for section in config2:
        if section not in config1:
            differences.append(f'Section {section} missing in config1')

    return differences

# Function to write differences to a file
def write_differences_to_file(differences, output_file):
    full_path = os.path.join(DEFAULT_DIRECTORY, output_file)
    with open(full_path, 'w') as file:
        for diff in differences:
            file.write(diff + '\n')

# Main function to load, parse, compare configurations, and write differences
def main():
    try:
        print(f"Using default directory: {DEFAULT_DIRECTORY}")
        print("Please enter file names without the full path.")
        config1_path = input("Enter the name of the first configuration file: ")
        config2_path = input("Enter the name of the second configuration file: ")
        output_file = input("Enter the name for the output differences file: ")

        print(f"Reading file 1: {config1_path}")
        config1_lines = read_config_file(config1_path)
        print(f"Reading file 2: {config2_path}")
        config2_lines = read_config_file(config2_path)

        print("Parsing config 1")
        config1 = parse_config(config1_lines)
        print("Parsing config 2")
        config2 = parse_config(config2_lines)

        print("Comparing configs")
        differences = compare_configs(config1, config2)

        if not differences:
            print("No differences found between the configurations.")
        else:
            full_output_path = os.path.join(DEFAULT_DIRECTORY, output_file)
            print(f"Writing differences to {full_output_path}")
            write_differences_to_file(differences, output_file)
            print(f"Differences written to {full_output_path}")

    except FileNotFoundError as e:
        print(f"File not found error: {e}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    main()

