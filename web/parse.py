import json
import re

def read_yuho_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def parse_yuho_to_json(yuho_data):
    section_number = re.search(r'sectionNumber\s*:=\s*(\d+)', yuho_data).group(1)
    section_description = re.search(r'sectionDescription\s*:=\s*"(.*?)"', yuho_data).group(1)
    definition = re.search(r'definition\s*:=\s*"(.*?)"', yuho_data).group(1)

    result = {}
    punishments = ["ofGeneric", "ofMotorVehicle", "ofDwellingHouse", "ofClerkOrServant", "afterPreparationCausingDeath"]
    for punishment in punishments:
        imprisonment_duration = re.search(rf'{punishment}\s*:=\s*{{.*?imprisonmentDuration\s*:=\s*(\d+\s*year).*?}}', yuho_data, re.DOTALL).group(1)
        fine = re.search(rf'{punishment}.*?fine\s*:=\s*(pass|money)', yuho_data, re.DOTALL).group(1)
        supplementary_punishment_match = re.search(rf'{punishment}.*?supplementaryPunishment\s*:=\s*(pass|"(.*?)")', yuho_data, re.DOTALL)
        supplementary_punishment = supplementary_punishment_match.group(1) if supplementary_punishment_match.group(1) == "pass" else supplementary_punishment_match.group(2)

        result[punishment] = {
            "imprisonmentDuration": imprisonment_duration,
            "fine": None if fine == "pass" else fine,
            "supplementaryPunishment": None if supplementary_punishment == "pass" else supplementary_punishment
        }

    output_json = {
        "sectionNumber": int(section_number),
        "sectionDescription": section_description,
        "definition": definition,
        "result": result
    }

    return output_json

# ----- EXECUTION CODE -----

def main():
    yuho_file_path = 'dep/yh/theft.yh'
    write_file_path = 'out/theft.json'
    yuho_data = read_yuho_file(yuho_file_path)
    json_output = parse_yuho_to_json(yuho_data)
    json_string = json.dumps(json_output, indent=4)
    with open(write_file_path, 'w') as json_file:
        json_file.write(json_string)
    # print(json_string)
    print('finished writing to json file')

if __name__ == "__main__":
    main()
