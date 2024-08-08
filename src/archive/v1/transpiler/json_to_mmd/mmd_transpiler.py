import json

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