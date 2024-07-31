import re
import json

def read_yuho_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def parse_yuho_to_json(yuho_data):
    section_number = re.search(r'sectionNumber\s*:=\s*(\d+)', yuho_data)
    section_number = section_number.group(1) if section_number else None

    section_description = re.search(r'sectionDescription\s*:=\s*"(.*?)"', yuho_data)
    section_description = section_description.group(1) if section_description else None

    definition = re.search(r'definition\s*:=\s*"(.*?)"', yuho_data)
    definition = definition.group(1) if definition else None

    result = {}
    punishments = [
        "ofGeneric", "ofMotorVehicle", "ofDwellingHouse", "ofClerkOrServant",
        "afterPreparationCausingDeath", "ofMurderWithDeathSentence", "ofPersonation",
        "withThreatToCauseDeath", "withThreatToCauseGrievousHurt", "ofHouseTrespass"
    ]

    for punishment in punishments:
        imprisonment_duration_match = re.search(
            rf'{punishment}\s*:=\s*{{.*?imprisonmentDuration\s*:=\s*(\w+ \w+|life imprisonment|pass).*?}}',
            yuho_data, re.DOTALL
        )
        imprisonment_duration = imprisonment_duration_match.group(1) if imprisonment_duration_match else None

        fine_match = re.search(
            rf'{punishment}.*?fine\s*:=\s*(pass|money)',
            yuho_data, re.DOTALL
        )
        fine = fine_match.group(1) if fine_match else None

        supplementary_punishment_match = re.search(
            rf'{punishment}.*?supplementaryPunishment\s*:=\s*(pass|"(.*?)")',
            yuho_data, re.DOTALL
        )
        supplementary_punishment = (
            supplementary_punishment_match.group(1)
            if supplementary_punishment_match and supplementary_punishment_match.group(1) == "pass"
            else supplementary_punishment_match.group(2) if supplementary_punishment_match else None
        )

        result[punishment] = {
            "imprisonmentDuration": None if imprisonment_duration == "pass" else imprisonment_duration,
            "fine": None if fine == "pass" else fine,
            "supplementaryPunishment": None if supplementary_punishment == "pass" else supplementary_punishment
        }

    output_json = {
        "sectionNumber": int(section_number) if section_number else None,
        "sectionDescription": section_description,
        "definition": definition,
        "result": result
    }

    return output_json

# ----- EXECUTION CODE -----

def main():
    yuho_files = [
        ('dep/yh/cheating.yh', 'out/json/cheating.json'),
        ('dep/yh/murder.yh', 'out/json/murder.json'),
        ('dep/yh/theft.yh', 'out/json/theft.json'),
        ('dep/yh/extortion.yh', 'out/json/extortion.json'),
        ('dep/yh/trespass.yh', 'out/json/trespass.json')  # Added trespass file
    ]
    for yuho_file_path, write_file_path in yuho_files:
        yuho_data = read_yuho_file(yuho_file_path)
        json_output = parse_yuho_to_json(yuho_data)
        json_string = json.dumps(json_output, indent=4)
        with open(write_file_path, 'w') as json_file:
            json_file.write(json_string)
        print(f'Finished writing {write_file_path}')

if __name__ == "__main__":
    main()
