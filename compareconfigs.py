import re
import os

# Function to read configuration file
def read_config_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r') as file:
        return file.read().splitlines()

# Function to parse configuration file
def parse_config(lines):
    config = {}
    current_section = None
    current_subsection = None
    current_key = None

    for line in lines:
        line = line.strip()
        if line.startswith('config'):
            current_section = line.split(' ')[1]
            config[current_section] = {}
        elif line.startswith('edit'):
            current_subsection = line.split(' ')[1].strip('"')
            config[current_section][current_subsection] = {}
        elif line.startswith('set') or line.startswith('unset'):
            if current_section and current_subsection:
                parts = line.split(' ')
                key = parts[1]
                value = ' '.join(parts[2:])
                config[current_section][current_subsection][key] = value
        elif line.startswith('next'):
            current_subsection = None
        elif line.startswith('end'):
            current_section = None

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
    with open(output_file, 'w') as file:
        for diff in differences:
            file.write(diff + '\n')

# Main function to load, parse, compare configurations, and write differences
def main():
    try:
        config1_path = input("Enter the path for the first configuration file: ")
        config2_path = input("Enter the path for the second configuration file: ")
        output_file = input("Enter the path for the output differences file: ")

        config1_lines = read_config_file(config1_path)
        config2_lines = read_config_file(config2_path)

        config1 = parse_config(config1_lines)
        config2 = parse_config(config2_lines)

        differences = compare_configs(config1, config2)

        if not differences:
            print("No differences found between the configurations.")
        else:
            write_differences_to_file(differences, output_file)
            print(f"Differences written to {output_file}")

    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

