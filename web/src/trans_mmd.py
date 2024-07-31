# HELL YEAH THIS WORKS TOO

import json

COLOR_GREEN = '\033[92m'
COLOR_RESET = '\033[0m'

def parse_json_to_mmd(json_data):
    section_number = json_data.get("sectionNumber", "")
    section_description = json_data.get("sectionDescription", "")
    definition = json_data.get("definition", "")
    result = json_data.get("result", {})

    mmd_lines = [
        f"graph TD\n",
        f"    A[Section {section_number}] --> B[Statute: {section_description}] --> C[Definition: {definition}]\n"
    ]

    result_index = 0
    for result_name, details in result.items():
        node_letter = chr(ord('D') + result_index)  # 'D', 'E', 'F', etc.
        imprisonment_duration = details.get("imprisonmentDuration", "None")
        fine = details.get("fine", "None")
        supplementary_punishment = details.get("supplementaryPunishment", "None")
        mmd_lines.append(f"    C --> {node_letter}[Result: {result_name}]")
        mmd_lines.append(f"    {node_letter} --> {node_letter}1[Imprisonment Duration: {imprisonment_duration}]")
        mmd_lines.append(f"    {node_letter} --> {node_letter}2[Fine: {fine}]")
        mmd_lines.append(f"    {node_letter} --> {node_letter}3[Supplementary Punishment: {supplementary_punishment}]\n")
        result_index += 1

    return "\n".join(mmd_lines)

def read_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def write_mmd_file(file_path, mmd_data):
    with open(file_path, 'w') as file:
        file.write(mmd_data)

# ----- MAIN EXECUTION CODE -----

def main():
    json_files = [
        ('../out/json/theft.json', '../out/mmd/theft.mmd'),
        ('../out/json/cheating.json', '../out/mmd/cheating.mmd'),
        ('../out/json/murder.json', '../out/mmd/murder.mmd'),
        ('../out/json/extortion.json', '../out/mmd/extortion.mmd'),
        ('../out/json/trespass.json', '../out/mmd/trespass.mmd')
    ]

    for json_file_path, mmd_file_path in json_files:
        json_data = read_json_file(json_file_path)
        mmd_output = parse_json_to_mmd(json_data)
        write_mmd_file(mmd_file_path, mmd_output)
        print(f"{COLOR_GREEN}Finished writing {mmd_file_path}{COLOR_RESET}")

if __name__ == "__main__":
    main()
