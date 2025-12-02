import os
import re
from pathlib import Path

def remove_comments_from_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    cleaned_lines = []
    in_multiline_string = False
    multiline_delimiter = None
    
    for line in lines:
        stripped = line.lstrip()
        
        if '"""' in line or "'''" in line:
            if '"""' in line:
                delimiter = '"""'
            else:
                delimiter = "'''"
            
            count = line.count(delimiter)
            if count == 1:
                in_multiline_string = not in_multiline_string
                multiline_delimiter = delimiter if in_multiline_string else None
            elif count == 2:
                pass
            
            cleaned_lines.append(line)
            continue
        
        if in_multiline_string:
            cleaned_lines.append(line)
            continue
        
        if stripped.startswith('#'):
            continue
        
        if '#' in line:
            in_string = False
            quote_char = None
            cleaned = []
            i = 0
            while i < len(line):
                char = line[i]
                
                if char in ('"', "'") and (i == 0 or line[i-1] != '\\'):
                    if not in_string:
                        in_string = True
                        quote_char = char
                    elif char == quote_char:
                        in_string = False
                        quote_char = None
                    cleaned.append(char)
                elif char == '#' and not in_string:
                    cleaned.append('\n')
                    break
                else:
                    cleaned.append(char)
                i += 1
            
            line = ''.join(cleaned).rstrip() + '\n'
        
        if line.strip():
            cleaned_lines.append(line)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)

project_root = Path(r"C:\Users\91800\.gemini\antigravity\scratch\andon_system")

python_files = [
    "dashboard/Home.py",
    "dashboard/auth.py",
    "dashboard/pages/1_📊_Executive_Summary.py",
    "dashboard/pages/2_🏭_Shop_Floor.py",
    "dashboard/pages/3_👨‍🏭_Shift_Analysis.py",
    "dashboard/pages/4_🎯_Quality_Dashboard.py",
    "dashboard/pages/5_⚡_Energy_Monitoring.py",
    "dashboard/pages/6_🧵_Invisible_Airbag_Facility.py",
    "dashboard/utils/alerts.py",
    "dashboard/utils/data_export.py",
    "dashboard/utils/quality_metrics.py",
    "dashboard/utils/tooltips.py",
    "edge/gateway.py",
    "ingress-api/app/auth.py",
    "ingress-api/app/database.py",
    "ingress-api/app/main.py",
    "ingress-api/app/models.py",
    "ingress-api/app/schemas.py",
    "ingress-api/create_admin.py",
]

count = 0
errors = 0

for file_path in python_files:
    full_path = project_root / file_path
    if full_path.exists():
        try:
            remove_comments_from_file(str(full_path))
            count += 1
        except Exception as e:
            errors += 1
    else:
        errors += 1

print(f"Processed: {count} files")
print(f"Errors: {errors} files")
print("Done")
