import os
import sys
import json
import time
import requests
import jwt

def get_jwt(app_id, private_key):
    payload = {
        'iat': int(time.time()),
        'exp': int(time.time()) + 600,
        'iss': app_id
    }
    return jwt.encode(payload, private_key, algorithm='RS256')

def main():
    app_id = os.environ.get('RENOVATE_APP_ID')
    private_key = os.environ.get('RENOVATE_PRIVATE_KEY')
    
    if not app_id or not private_key:
        print("Error: RENOVATE_APP_ID and RENOVATE_PRIVATE_KEY are required.")
        sys.exit(1)

    # Whitelist logic
    whitelist_str = os.environ.get('RENOVATE_INSTALLATION_WHITELIST', '')
    whitelist = [x.strip() for x in whitelist_str.split(',') if x.strip()]
    
    # Auth
    try:
        token = get_jwt(app_id, private_key)
    except Exception as e:
        print(f"Error creating JWT: {e}")
        sys.exit(1)

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Fetch installations
    installations = []
    page = 1
    while True:
        resp = requests.get(f"https://api.github.com/app/installations?per_page=100&page={page}", headers=headers)
        if resp.status_code != 200:
            print(f"Error fetching installations: {resp.status_code} {resp.text}")
            sys.exit(1)
            
        data = resp.json()
        if not data:
            break
            
        installations.extend(data)
        page += 1

    matrix = []
    
    # Forgejo (Static) - Prepend as requested
    codeberg_user = os.environ.get('CODEBERG_BOT_USERNAME', 'codeberg-bot')
    forgejo_entry = {
        "platform": "forgejo",
        "owner": None,
        "installation_id": None,
        "endpoint": "https://codeberg.org/api/v1",
        "renovate_username": codeberg_user,
        "git_author": f"{codeberg_user} <{codeberg_user}@noreply.codeberg.org>"
    }
    matrix.append(forgejo_entry)

    # GitHub
    renovate_user = os.environ.get('RENOVATE_USERNAME', 'renovate-bot')
    
    for inst in installations:
        inst_id = str(inst['id'])
        owner = inst['account']['login']
        
        # Filter
        if whitelist:
            if inst_id not in whitelist and owner not in whitelist:
                print(f"Skipping installation: {owner} (ID: {inst_id})")
                continue
        
        matrix.append({
            "platform": "github",
            "owner": owner,
            "installation_id": inst['id'],
            "endpoint": "", # Default
            "renovate_username": renovate_user,
            "git_author": f"{renovate_user}[bot] <{app_id}+{renovate_user}[bot]@users.noreply.github.com>"
        })

    # Output
    json_output = json.dumps(matrix)
    
    # Print to stdout for debugging/logs
    print(f"Generated matrix: {json_output}")

    # Write to GITHUB_OUTPUT
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"matrix={json_output}\n")

if __name__ == "__main__":
    main()