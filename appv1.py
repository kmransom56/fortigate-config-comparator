import re
import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DIFF_FOLDER'] = 'diffs'

# Ensure the upload and diff folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DIFF_FOLDER'], exist_ok=True)

# Define a route to render the upload.html file
@app.route('/')
def home():
    return render_template('upload.html')

# Define a route to handle file uploads
@app.route('/upload', methods=['POST'])
def upload_files():
    if 'file1' not in request.files or 'file2' not in request.files:
        return redirect(request.url)

    file1 = request.files['file1']
    file2 = request.files['file2']

    if file1.filename == '' or file2.filename == '':
        return redirect(request.url)

    file1_path = os.path.join(app.config['UPLOAD_FOLDER'], file1.filename)
    file2_path = os.path.join(app.config['UPLOAD_FOLDER'], file2.filename)

    file1.save(file1_path)
    file2.save(file2_path)

    # Process the uploaded files and generate the difference file
    config1_lines = read_config_file(file1_path)
    config2_lines = read_config_file(file2_path)

    config1 = parse_config(config1_lines)
    config2 = parse_config(config2_lines)

    config1_name = "_".join(os.path.splitext(os.path.basename(file1_path))[0].split("_")[:2])
    config2_name = "_".join(os.path.splitext(os.path.basename(file2_path))[0].split("_")[:2])

    ignore_keys = ['hostname', 'set-date', 'set password', 'set passphrase', 'set psksecret', 'set secret',
                   'set secondary-secret', 'set passphrase ENC', 'set psksecret ENC', 'set secret ENC',
                   'set secondary-secret ENC']

    differences = compare_configs(config1, config2, config1_name, config2_name, ignore_keys)

    diff_file = os.path.join(app.config['DIFF_FOLDER'], 'configdiff.txt')
    write_differences_to_file(differences, diff_file)

    return render_template('result.html', diff_file='configdiff.txt')

# Define a route to download the difference file
@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['DIFF_FOLDER'], filename)

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
    differences = []

    # Convert ignore_keys to a set for faster lookup
    ignore_keys = set(ignore_keys or [])

    # Compare sections
    all_sections = set(config1.keys()).union(config2.keys())
    for section in all_sections:
        if section not in config1:
            differences.append(f"Section '{section}' found in {filename2} but not in {filename1}")
            continue
        if section not in config2:
            differences.append(f"Section '{section}' found in {filename1} but not in {filename2}")
            continue

        # Compare keys within the section
        all_keys = set(config1[section].keys()).union(config2[section].keys())
        for key in all_keys:
            if key in ignore_keys:
                continue
            if key not in config1[section]:
                differences.append(f"Key '{key}' in section '{section}' found in {filename2} but not in {filename1}")
                continue
            if key not in config2[section]:
                differences.append(f"Key '{key}' in section '{section}' found in {filename1} but not in {filename2}")
                continue
            if config1[section][key] != config2[section][key]:
                differences.append(f"Key '{key}' in section '{section}' differs between {filename1} and {filename2}")

    return differences

# Function to write differences to a file
def write_differences_to_file(differences, output_file):
    with open(output_file, 'w') as file:
        for difference in differences:
            file.write(difference + '\n')

def main():
    try:
        config1_path = 'path_to_config1'
        config2_path = 'path_to_config2'

        config1 = read_config_file(config1_path)
        config2 = read_config_file(config2_path)

        config1_name = "_".join(os.path.splitext(os.path.basename(config1_path))[0].split("_")[:2])
        config2_name = "_".join(os.path.splitext(os.path.basename(config2_path))[0].split("_")[:2])

        ignore_keys = ['hostname', 'set-date', 'set password', 'set passphrase', 'set psksecret', 'set secret',
                       'set secondary-secret', 'set passphrase ENC', 'set psksecret ENC', 'set secret ENC',
                       'set secondary-secret ENC']

        differences = compare(config, config2, config1_name, config2_name, ignore_keys)

        output_file = "configdiff.txt"
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
    app.run(debug=True)