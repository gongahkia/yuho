import os
import json

COLOR_GREEN = '\033[92m'
COLOR_RED = '\033[91m'
COLOR_RESET = '\033[0m'

def read_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def validate_json_files(dep_json_dir, out_json_dir):
    dep_files = set(os.listdir(dep_json_dir))
    out_files = set(os.listdir(out_json_dir))
    common_files = dep_files.intersection(out_files)
    for file_name in common_files:
        dep_file_path = os.path.join(dep_json_dir, file_name)
        out_file_path = os.path.join(out_json_dir, file_name)
        dep_data = read_json(dep_file_path)
        out_data = read_json(out_file_path)
        if dep_data == out_data:
            print(f"{COLOR_GREEN}{file_name}: Match{COLOR_RESET}")
        else:
            print(f"{COLOR_RED}{file_name}: Mismatch{COLOR_RESET}")


# ----- MAIN EXECUTION CODE -----

if __name__ == "__main__":
    dep_json_dir = os.path.join("dep", "json")
    out_json_dir = "out"
    validate_json_files(dep_json_dir, out_json_dir)
