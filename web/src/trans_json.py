# HELL YEAH IT WORKS

import re
import json

COLOR_GREEN = '\033[92m'
COLOR_RESET = '\033[0m'

def read_yuho_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def parse_yuho_to_json(yuho_data):

    section_number = re.search(r'sectionNumber\s*:=\s*(\d+)', yuho_data).group(1)
    section_description = re.search(r'sectionDescription\s*:=\s*"(.*?)"', yuho_data).group(1)
    definition = re.search(r'definition\s*:=\s*"(.*?)"', yuho_data).group(1)
    result = {}

    punishment_pattern = re.compile(
        r'\b(\w+)\s*:=\s*{\s*imprisonmentDuration\s*:=\s*(\d+\s*year|life imprisonment|pass|[\w\s]+)\s*.*?fine\s*:=\s*(pass|money)\s*.*?supplementaryPunishment\s*:=\s*(pass|"(.*?)")', 
        re.DOTALL
    )
    punishments = punishment_pattern.findall(yuho_data)

    for punishment in punishments:
        punishment_name = punishment[0]
        imprisonment_duration = punishment[1].strip()
        fine = None if punishment[2] == "pass" else punishment[2]
        supplementary_punishment = None if punishment[3] == "pass" else punishment[3].strip().strip('"')
        result[punishment_name] = {
            "imprisonmentDuration": imprisonment_duration if imprisonment_duration != "pass" else None,
            "fine": fine,
            "supplementaryPunishment": supplementary_punishment if supplementary_punishment else None
        }

    output_json = {
        "sectionNumber": int(section_number),
        "sectionDescription": section_description,
        "definition": definition,
        "result": result
    }

    return output_json

# ----- MAIN EXECUTION CODE -----

def main():
    yuho_files = [
        ('../dep/yh/cheating.yh', '../out/json/cheating.json'),
        ('../dep/yh/murder.yh', '../out/json/murder.json'),
        ('../dep/yh/theft.yh', '../out/json/theft.json'),
        ('../dep/yh/extortion.yh', '../out/json/extortion.json'),
        ('../dep/yh/trespass.yh', '../out/json/trespass.json')  
    ]
    for yuho_file_path, write_file_path in yuho_files:
        yuho_data = read_yuho_file(yuho_file_path)
        json_output = parse_yuho_to_json(yuho_data)
        json_string = json.dumps(json_output, indent=4)
        with open(write_file_path, 'w') as json_file:
            json_file.write(json_string)
        print(f"{COLOR_GREEN}Finished writing {write_file_path}{COLOR_RESET}")

if __name__ == "__main__":
    main()
