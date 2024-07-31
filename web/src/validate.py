import os
import json

COLOR_CYAN = '\033[96m'
COLOR_GREEN = '\033[92m'
COLOR_RED = '\033[91m'
COLOR_RESET = '\033[0m'

def read_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def validate_json_files(dep_json_dir, out_json_dir):
    print(f"{COLOR_CYAN}~ JSON FILES ~{COLOR_RESET}")
    dep_json_files = set(f for f in os.listdir(dep_json_dir) if f.endswith('.json'))
    out_json_files = set(f for f in os.listdir(out_json_dir) if f.endswith('.json'))
    for file_name in dep_json_files:
        dep_file_path = os.path.join(dep_json_dir, file_name)
        if file_name in out_json_files:
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
    for file_name in out_json_files:
        if file_name not in dep_json_files:
            print(f"{file_name}: {COLOR_RED}File not found in dependency directory{COLOR_RESET}")

def validate_mmd_files(dep_mmd_dir, out_mmd_dir):
    print(f"{COLOR_CYAN}~ MMD FILES ~{COLOR_RESET}")
    dep_mmd_files = set(f for f in os.listdir(dep_mmd_dir) if f.endswith('.mmd'))
    out_mmd_files = set(f for f in os.listdir(out_mmd_dir) if f.endswith('.mmd'))
    for file_name in dep_mmd_files:
        dep_file_path = os.path.join(dep_mmd_dir, file_name)
        if file_name in out_mmd_files:
            out_file_path = os.path.join(out_mmd_dir, file_name)
            if os.path.getsize(dep_file_path) == os.path.getsize(out_file_path):
                print(f"{file_name}: {COLOR_GREEN}Match{COLOR_RESET}")
            else:
                print(f"{file_name}: {COLOR_RED}Mismatch{COLOR_RESET}")
        else:
            print(f"{file_name}: {COLOR_RED}File not found in output directory{COLOR_RESET}")
    for file_name in out_mmd_files:
        if file_name not in dep_mmd_files:
            print(f"{file_name}: {COLOR_RED}File not found in dependency directory{COLOR_RESET}")

# ----- MAIN EXECUTION CODE -----

if __name__ == "__main__":
    dep_json_dir = os.path.join("..", "dep", "json")
    out_json_dir = os.path.join("..", "out", "json")
    dep_mmd_dir = os.path.join("..", "dep", "mmd")
    out_mmd_dir = os.path.join("..", "out", "mmd")
    validate_json_files(dep_json_dir, out_json_dir)
    validate_mmd_files(dep_mmd_dir, out_mmd_dir)
