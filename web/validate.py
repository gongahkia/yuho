import os
import json

COLOR_GREEN = '\033[92m'
COLOR_RED = '\033[91m'
COLOR_RESET = '\033[0m'

def read_json(file_path):
    """Reads a JSON file and returns its contents."""
    with open(file_path, 'r') as file:
        return json.load(file)

def validate_json_files(dep_json_dir, out_json_dir):
    """Validates JSON files in the specified directories."""
    dep_files = set(os.listdir(dep_json_dir))
    out_files = set(os.listdir(out_json_dir))
    
    # Iterate over files in the dependency directory
    for file_name in dep_files:
        dep_file_path = os.path.join(dep_json_dir, file_name)
        if file_name in out_files:
            out_file_path = os.path.join(out_json_dir, file_name)
            try:
                dep_data = read_json(dep_file_path)
                out_data = read_json(out_file_path)
                if dep_data == out_data:
                    print(f"{file_name}: {COLOR_GREEN}Match{COLOR_RESET}")
                else:
                    print(f"{file_name}: {COLOR_RED}Mismatch{COLOR_RESET}")
            except json.JSONDecodeError:
                print(f"{file_name}: {COLOR_RED}Error in JSON format{COLOR_RESET}")
            except Exception as e:
                print(f"{file_name}: {COLOR_RED}Error - {e}{COLOR_RESET}")
        else:
            print(f"{file_name}: {COLOR_RED}File not found in output directory{COLOR_RESET}")

    # Report files in the output directory that are not in the dependency directory
    for file_name in out_files:
        if file_name not in dep_files:
            print(f"{file_name}: {COLOR_RED}File not found in dependency directory{COLOR_RESET}")

# ----- MAIN EXECUTION CODE -----

if __name__ == "__main__":
    dep_json_dir = os.path.join("dep", "json")
    out_json_dir = os.path.join("out", "json")
    validate_json_files(dep_json_dir, out_json_dir)
