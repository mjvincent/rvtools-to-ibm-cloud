import os

# Define the new fields to add to the UI
new_fields = [
    "    wave = st.text_input(\"Wave\")",
    "    cutover_group = st.text_input(\"Cutover Group\")",
    "    owner = st.text_input(\"Owner\")",
    "    application = st.text_input(\"Application\")",
    "    priority = st.selectbox(\"Priority\", [\"High\", \"Medium\", \"Low\"])",
    "    dependency_group = st.text_input(\"Dependency Group\")"
]

# Read the existing content of ui.py
with open('ui.py', 'r') as file:
    lines = file.readlines()

# Find the line where the form or table starts
form_start_index = None
for i, line in enumerate(lines):
    if line.strip().startswith('st.markdown') or line.strip().startswith('st.write'):
        form_start_index = i
        break

if form_start_index is not None:
    # Insert the new fields after the existing form or table
    for field in new_fields:
        lines.insert(form_start_index + 1, field + '\n')

    # Write the updated lines back to the file
    with open('ui.py', 'w') as file:
        file.writelines(lines)
    print("New fields added to the UI form in ui.py")
else:
    print("Form or table not found in ui.py")