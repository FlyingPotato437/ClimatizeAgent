import json
import re
from datetime import datetime

def extract_and_format_markdown(json_file_path):
    """Extract content from Perplexity JSON response and format as markdown"""
    
    # Read the JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract the content from the response
    content = data['choices'][0]['message']['content']
    
    # Remove the <think> section (internal reasoning)
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
    
    # Clean up any extra whitespace
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    content = content.strip()
    
    # Create markdown filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    markdown_filename = f"perplexity_response_{timestamp}.md"
    
    # Write the formatted content to markdown file
    with open(markdown_filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Markdown content saved to: {markdown_filename}")
    return markdown_filename

def main():
    # Extract from the most recent response file
    json_file = "perplexity_response_20250716_000359.json"
    
    try:
        markdown_file = extract_and_format_markdown(json_file)
        print(f"\nSuccessfully converted JSON response to markdown: {markdown_file}")
        
        # Also print the content to console
        with open(markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print("\n" + "="*50)
        print("FORMATTED MARKDOWN CONTENT:")
        print("="*50)
        print(content)
        
    except FileNotFoundError:
        print(f"Error: Could not find {json_file}")
    except Exception as e:
        print(f"Error processing file: {e}")

if __name__ == "__main__":
    main() 