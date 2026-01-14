import os
import sys
import json
import time
import logging
import requests
import jwt
import hashlib

def get_jwt(app_id, private_key):
    payload = {
        'iat': int(time.time()),
        'exp': int(time.time()) + 600,
        'iss': app_id
    }
    return jwt.encode(payload, private_key, algorithm='RS256')

def main():
    # Configure logging
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

    # Check for required environment variables
    required_env_vars = ['GITHUB_APP_ID', 'GITHUB_PRIVATE_KEY', 'RENOVATE_BOT_USER_ID', 'RENOVATE_APP_SLUG', 'CODEBERG_BOT_USERNAME']
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    if missing_vars:
        logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)

    # Environment variables
    app_id = os.environ.get('GITHUB_APP_ID')
    private_key = os.environ.get('GITHUB_PRIVATE_KEY')
    bot_user_id = os.environ.get('RENOVATE_BOT_USER_ID')
    app_slug = os.environ.get('RENOVATE_APP_SLUG')
    codeberg_bot_username = os.environ.get('CODEBERG_BOT_USERNAME')
    hash_all_namespaces = os.environ.get('RENOVATE_HASH_ALL_NAMESPACES', 'false').lower() == 'true'

    whitelist_str = os.environ.get('GITHUB_INSTALLATION_WHITELIST', '')
    whitelist = [x.strip() for x in whitelist_str.split(',') if x.strip()]
    
    max_parallel = os.environ.get('MATRIX_MAX_PARALLEL', '5')

    # Auth
    try:
        token = get_jwt(app_id, private_key)
    except Exception as e:
        logging.error(f"Error creating JWT: {e}")
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
            logging.error(f"Error fetching installations: {resp.status_code} {resp.text}")
            sys.exit(1)
            
        data = resp.json()
        if not data:
            break
            
        installations.extend(data)
        page += 1

    matrix = []
    
    # Forgejo (Static) - Prepend as requested
    forgejo_entry = {
        "platform": "forgejo",
        "owner": "Codeberg",
        "installation_id": None,
        "endpoint": "https://codeberg.org/api/v1",
        "renovate_username": codeberg_bot_username,
        "git_author": f"{codeberg_bot_username} <{codeberg_bot_username}@noreply.codeberg.org>"
    }
    matrix.append(forgejo_entry)

    # GitHub
    
    for inst in installations:
        inst_id = str(inst['id'])
        owner = inst['account']['login']
        
        # Filter
        if whitelist:
            if inst_id not in whitelist and owner not in whitelist:
                logging.debug(f"Skipping installation: {owner} (ID: {inst_id})")
                continue
        
        display_owner = owner
        if hash_all_namespaces or inst['account'].get('user_view_type') != 'public': # assumes it's private if not public, i don't have any examples
            display_owner = hashlib.sha1(owner.encode()).hexdigest()

        matrix.append({
            "platform": "github",
            "owner": display_owner,
            "installation_id": inst['id'],
            "endpoint": "", # Default
            "renovate_username": app_slug,
            "git_author": f"{app_slug}[bot] <{bot_user_id}+{app_slug}[bot]@users.noreply.github.com>"
        })

    # Output
    json_output = json.dumps(matrix)
    
    # debugging matrix json format
    logging.debug(f"Generated matrix: {json_output}")

    # Write to GITHUB_OUTPUT
    github_output = os.environ.get('GITHUB_OUTPUT')
    if github_output:
        with open(github_output, 'a') as f:
            f.write(f"matrix={json_output}\n")
            f.write(f"max_parallel={max_parallel}\n")

if __name__ == "__main__":
    main()