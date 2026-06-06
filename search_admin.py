import os

def search_text_in_files(directory, text):
    matches = []
    for root, dirs, files in os.walk(directory):
        # Skip virtual environments
        if '.venv' in root or 'venv' in root or '__pycache__' in root or '.idea' in root:
            continue
        for file in files:
            if file.endswith(('.html', '.py', '.css', '.js')):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        for line_no, line in enumerate(f, 1):
                            if text.lower() in line.lower():
                                matches.append((path, line_no, line.strip()))
                except Exception as e:
                    matches.append((path, 0, f"Error reading: {str(e)}"))
    return matches

if __name__ == '__main__':
    results = search_text_in_files('.', 'admin')
    print(f"Found {len(results)} matches for 'admin':")
    for r in results:
        print(f"{r[0]}:{r[1]}: {r[2]}")
