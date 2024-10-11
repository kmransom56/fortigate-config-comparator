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
    skip_public_key = False

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        if line.startswith('config '):
            current_section = line[7:]
            config[current_section] = {}
            current_subsection = None
        elif current_section is not None:
            # Handle subsections or other configurations here
            pass

    return config

# Function to compare configurations
def compare_configs(config1, config2, filename1, filename2, ignore_keys=None):
    if ignore_keys is None:
        ignore_keys = []
    differences = []

    all_sections = set(config1.keys()) | set(config2.keys())

    for section in all_sections:
        if section not in config1:
            differences.append(f"[Section Missing in {filename1}]\n  Section: '{section}' is in {filename2} but not in {filename1}\n")
        elif section not in config2:
            differences.append(f"[Section Missing in {filename2}]\n  Section: '{section}' is in {filename1} but not in {filename2}\n")
        else:
            section1 = config1[section]
            section2 = config2[section]

            if isinstance(section1, dict) and isinstance(section2, dict):
                all_subsections = set(section1.keys()) | set(section2.keys())

                for subsection in all_subsections:
                    if subsection not in section1:
                        differences.append(f"[Subsection Missing in {filename1}]\n  Subsection: '{subsection}' in section '{section}' is in {filename2} but not in {filename1}\n")
                    elif subsection not in section2:
                        differences.append(f"[Subsection Missing in {filename2}]\n  Subsection: '{subsection}' in section '{section}' is in {filename1} but not in {filename2}\n")
                    else:
                        subsection1 = section1[subsection]
                        subsection2 = section2[subsection]

                        if isinstance(subsection1, dict) and isinstance(subsection2, dict):
                            all_keys = set(subsection1.keys()) | set(subsection2.keys())

                            for key in all_keys:
                                if any(ignore_word in key for ignore_word in ignore_keys):
                                    continue
                                if 'image-base64' in key or 'vpn certificate' in key:
                                    continue
                                if key not in subsection1:
                                    differences.append(f"[Key Missing in {filename1}]\n  Key: '{key}' in subsection '{subsection}' of section '{section}' is in {filename2} but not in {filename1}\n")
                                elif key not in subsection2:
                                    differences.append(f"[Key Missing in {filename2}]\n  Key: '{key}' in subsection '{subsection}' of section '{section}' is in {filename1} but not in {filename2}\n")
                                elif subsection1[key] != subsection2[key]:
                                    differences.append(f"[Value Difference]\n  Section: '{section}'\n  Subsection: '{subsection}'\n  Key: '{key}'\n  {filename1}: '{subsection1[key]}'\n  {filename2}: '{subsection2[key]}'\n")
                        else:
                            if subsection1 != subsection2:
                                differences.append(f"[Subsection Value Difference]\n  Section: '{section}'\n  Subsection: '{subsection}'\n  {filename1}: '{subsection1}'\n  {filename2}: '{subsection2}'\n")
            else:
                if section1 != section2:
                    differences.append(f"[Section Value Difference]\n  Section: '{section}'\n  {filename1}: '{section1}'\n  {filename2}: '{section2}'\n")

    return differences

# Function to write differences to a file
def write_differences_to_file(differences, output_file):
    with open(output_file, 'w') as file:
        if not differences:
            file.write("No differences found between the configurations.\n")
        else:
            for diff in differences:
                file.write(diff + '\n')

# Main function to load, parse, compare configurations, and write differences
def main():
    try:
        # Set default directory
        default_dir = os.getcwd()

        # Get input files with default paths
        config1_path = input(f"Enter the name of the first configuration file (default directory: {default_dir}): ")
        config2_path = input(f"Enter the name of the second configuration file (default directory: {default_dir}): ")

        # Prepend the default directory if the user didn't provide a full path
        config1_path = os.path.join(default_dir, config1_path) if not os.path.isabs(config1_path) else config1_path
        config2_path = os.path.join(default_dir, config2_path) if not os.path.isabs(config2_path) else config2_path

        config1_lines = read_config_file(config1_path)
        config2_lines = read_config_file(config2_path)

        config1 = parse_config(config1_lines)
        config2 = parse_config(config2_lines)

        # Extract relevant filename parts
        config1_name = "_".join(os.path.splitext(os.path.basename(config1_path))[0].split("_")[:2])
        config2_name = "_".join(os.path.splitext(os.path.basename(config2_path))[0].split("_")[:2])

        # You can customize this list based on your needs
        ignore_keys = ['hostname', 'set-date', 'set password', 'set passphrase', 'set psksecret', 'set secret',
                       'set secondary-secret', 'set passphrase ENC', 'set psksecret ENC', 'set secret ENC',
                       'set secondary-secret ENC']

        differences = compare_configs(config1, config2, config1_name, config2_name, ignore_keys)

        output_file = "configdiff.txt"  # Constant output file name
        write_differences_to_file(differences, output_file)
        print(f"Differences written to {output_file}")

    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        print("Traceback:")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
