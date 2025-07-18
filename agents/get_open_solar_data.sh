#!/bin/bash

# Set variables
TOKEN="${OPENSOLAR_TOKEN}"
ORG_ID="183989"
PROJECT_ID="7481941"
BASE_URL="https://api.opensolar.com"

# Check if token is provided
if [ -z "$TOKEN" ]; then
    echo "Error: OPENSOLAR_TOKEN environment variable is required"
    echo "Please set it with: export OPENSOLAR_TOKEN='your_token_here'"
    exit 1
fi

# 1. Get project info first to extract the project name
echo "1. Getting project info..."
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/api/orgs/$ORG_ID/projects/$PROJECT_ID/" \
  -o "./project.json"

# Extract project name from the response using Python
PROJECT_NAME=$(python3 -c "import json; data=json.load(open('./project.json')); print(data.get('title', 'Unknown_Project').replace(' ', '_'))")
# Also extract the pretty project name (with spaces)
PRETTY_PROJECT_NAME=$(python3 -c "import json; data=json.load(open('./project.json')); print(data.get('title', 'Unknown Project'))")
echo "Project name: $PROJECT_NAME"

# Create directory for this project in current directory
mkdir -p "./$PROJECT_NAME"

# 2. Get systems for the project, save to file
echo "2. Getting systems..."
curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/api/orgs/$ORG_ID/systems/?fieldset=list&project=$PROJECT_ID" \
  -o "./$PROJECT_NAME/systems.json"

# 3. Extract the first system UUID from the systems response using Python
SYSTEM_UUID=$(python3 -c "import json; data=json.load(open('$PROJECT_NAME/systems.json')); print(data[0].get('uuid', '') if data else '')")
echo "System UUID: $SYSTEM_UUID"

# 4. Get system image
echo "4. Downloading system image..."
curl -L "$BASE_URL/api/orgs/$ORG_ID/projects/$PROJECT_ID/systems/$SYSTEM_UUID/image/?width=1200&height=800" \
  -H "Authorization: Bearer $TOKEN" \
  -o "./$PROJECT_NAME/system_image.png"

# Copy the project info to the project directory
mv ./project.json "./$PROJECT_NAME/"

# 5. Extract Single Line Diagram (SLD) URL from project.json (title must be exactly 'Single Line Diagram')
# Find the line number of the first "title": "Single Line Diagram"
SLD_LINE=$(grep -n '"title" *: *"Single Line Diagram"' "./$PROJECT_NAME/project.json" | head -n1 | cut -d: -f1)

if [ -n "$SLD_LINE" ]; then
  # From that line onward, find the first "file_contents" and extract the URL
  SLD_URL=$(python3 -c '
import json
import sys
with open("'"./$PROJECT_NAME/project.json"'") as f:
    data = json.load(f)
def find_sld_url(obj):
    if isinstance(obj, dict):
        if obj.get("title") == "Single Line Diagram" and "file_contents" in obj:
            return obj["file_contents"]
        for v in obj.values():
            result = find_sld_url(v)
            if result:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = find_sld_url(item)
            if result:
                return result
    return None
url = find_sld_url(data)
if url:
    print(url)
' )
  if [ -n "$SLD_URL" ]; then
    echo "Single Line Diagram URL: $SLD_URL"
    curl -L "$SLD_URL" -o "./$PROJECT_NAME/single_line_diagram.svg"
    echo "  - ./$PROJECT_NAME/single_line_diagram.svg"
  else
    echo "No file_contents found after Single Line Diagram title."
  fi
else
  echo "No Single Line Diagram found in project.json."
fi

# 6. Extract IronRidge Bill of Materials (BOM) PDF URL from project.json (title contains 'Ironridge_BOM' and ends with .pdf)
IR_BOM_URL=$(python3 -c '
import json
with open("'"./$PROJECT_NAME/project.json"'") as f:
    data = json.load(f)
def find_ir_bom_url(obj):
    if isinstance(obj, dict):
        title = obj.get("title", "")
        if "Ironridge_BOM" in title and title.endswith(".pdf") and "file_contents" in obj:
            return obj["file_contents"]
        for v in obj.values():
            result = find_ir_bom_url(v)
            if result:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = find_ir_bom_url(item)
            if result:
                return result
    return None
url = find_ir_bom_url(data)
if url:
    print(url)
')
if [ -n "$IR_BOM_URL" ]; then
  echo "Ironridge Bill of Materials URL: $IR_BOM_URL"
  curl -L "$IR_BOM_URL" -o "./$PROJECT_NAME/bill_of_materials.pdf"
  echo "  - ./$PROJECT_NAME/bill_of_materials.pdf"
else
  echo "No Ironridge Bill of Materials found in project.json."
fi

# 7. Extract Bill of Materials (BOM) CSV URL from project.json
BOM_TITLE="${PRETTY_PROJECT_NAME}_BOM.csv"
echo "Looking for BOM file with title: $BOM_TITLE"
BOM_URL=$(python3 -c '
import json
with open("'"./$PROJECT_NAME/project.json"'") as f:
    data = json.load(f)
def find_bom_url(obj):
    if isinstance(obj, dict):
        if obj.get("title") == "'"$BOM_TITLE"'" and "file_contents" in obj:
            return obj["file_contents"]
        for v in obj.values():
            result = find_bom_url(v)
            if result:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = find_bom_url(item)
            if result:
                return result
    return None
url = find_bom_url(data)
if url:
    print(url)
')
if [ -n "$BOM_URL" ]; then
  echo "Bill of Materials CSV URL: $BOM_URL"
  curl -L "$BOM_URL" -o "./$PROJECT_NAME/bill_of_materials.csv"
  echo "  - ./$PROJECT_NAME/bill_of_materials.csv"
else
  echo "No Bill of Materials CSV found in project.json."
fi

echo "✅ All data saved to directory: $PROJECT_NAME"
echo "Files created:"
echo "  - ./$PROJECT_NAME/project.json"
echo "  - ./$PROJECT_NAME/systems.json" 
echo "  - ./$PROJECT_NAME/system_image.png" 
echo "  - ./$PROJECT_NAME/single_line_diagram.svg" 
echo "  - ./$PROJECT_NAME/bill_of_materials.pdf"
echo "  - ./$PROJECT_NAME/bill_of_materials.csv" 