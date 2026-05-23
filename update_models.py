import os

# Define the new fields to add
ew_fields = [
    "    wave: str",
    "    cutover_group: str",
    "    owner: str",
    "    application: str",
    "    priority: str",
    "    dependency_group: str"
]

# Read the existing content of models.py
with open('models.py', 'r') as file:
    lines = file.readlines()

# Find the line where the MigrationVm class starts
class_start_index = None
for i, line in enumerate(lines):
    if line.strip().startswith('@dataclass'):
        class_start_index = i
        break

if class_start_index is not None:
    # Insert the new fields after the existing fields
    for field in new_fields:
        lines.insert(class_start_index + 1, field + '\n')

    # Write the updated lines back to the file
    with open('models.py', 'w') as file:
        file.writelines(lines)
    print("Fields added to MigrationVm class in models.py")
else:
    print("MigrationVm class not found in models.py")