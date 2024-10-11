file_path = 'data.txt'

# Try reading the file with a simple read to inspect the content
with open(file_path, 'r', encoding='ISO-8859-1') as file:
    for _ in range(10):  # Read the first 10 lines
        print(file.readline())