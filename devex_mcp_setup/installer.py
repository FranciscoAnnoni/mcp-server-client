import os
import sys
import json
import re
import platform
import shutil
import subprocess
from pathlib import Path
from auth_installer import AuthManager

# Force UTF-8 encoding for standard I/O
sys.stdout.reconfigure(encoding='utf-8') # type: ignore
sys.stderr.reconfigure(encoding='utf-8') # type: ignore
if sys.stdin.encoding != 'utf-8':
    try: 
        sys.stdin.reconfigure(encoding='utf-8') # type: ignore
    except: 
        pass

# REPO_URL logic: Prefer environment variable from setup script, else fallback to default
if os.environ.get("DEVEX_CLIENT_REPO_URL"):
    REPO_URL = os.environ.get("DEVEX_CLIENT_REPO_URL")
else: # Default Fallback (SSH)
    REPO_URL = "git+ssh://git@github.com/rappi-inc/devex-mcp.git@master#subdirectory=devex_mcp_client"

SERVER_NAME = "devex-mcp"

def get_os_type():
    sys_name = platform.system().lower()
    if sys_name == "darwin": return "mac"
    elif sys_name == "windows": return "windows"
    return "linux"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    clear_screen()
    print("========================================")
    print(f"🚀 {SERVER_NAME} Installer")
    print(f"   Detected System: {platform.system()}")
    print("========================================")

def run_command(command_list):
    try:
        subprocess.run(command_list, check=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error executing: {' '.join(command_list)}")
        print(f"   Details: {e}")
        return False
    except FileNotFoundError:
        print(f"\n❌ Required command not found (uv/git).")
        return False

def get_ide_config_path(ide_choice):
    os_type = get_os_type()
    home = Path.home()

    if ide_choice == "claude":
        if os_type == "windows": return home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
        elif os_type == "mac": return home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        else: return home / ".config" / "Claude" / "claude_desktop_config.json"

    elif ide_choice == "vscode":
        if os_type == "windows": return home / "AppData" / "Roaming" / "Code" / "User" / "mcp.json"
        elif os_type == "mac": return home / "Library" / "Application Support" / "Code" / "User" / "mcp.json"
        else: return home / ".config" / "Code" / "User" / "mcp.json"

    elif ide_choice == "antigravity":
        if os_type == "windows": return home / ".gemini" / "antigravity" / "mcp_config.json"
        elif os_type == "mac": return home / ".gemini" / "antigravity" / "mcp_config.json"
        else: return home / ".gemini" / "antigravity" / "mcp_config.json"

    elif ide_choice == "jetbrains":
        if os_type == "windows": return home / "AppData" / "Local" / "github-copilot" / "intellij" / "mcp.json"
        elif os_type == "mac": return home / ".config" / "github-copilot" / "intellij" / "mcp.json"
        else: return home / ".config" / "github-copilot" / "intellij" / "mcp.json"

    if ide_choice == "custom":
        print(f"\nℹ️  Please enter the full path to the JSON file or its directory.")
        path_str = input("📂 Path > ").strip().replace('"', '').replace("'", "")
        if not path_str: return None
        
        path_obj = Path(path_str)
        
        # Auto-append filename if directory
        if path_obj.is_dir():
            path_obj = path_obj / "mcp.json"
            print(f"   -> Detected directory. Target set to: {path_obj}")
            
        return path_obj
        
    return None

def remove_comments_safe(json_str):
    pattern = r'("[^"\\]*(?:\\.[^"\\]*)*")|(/\*[^*]*\*+(?:[^/*][^*]*\*+)*|//.*)'
    def replace(match):
        if match.group(1):
            return match.group(1)
        return ""
    # REMOVED flags=re.DOTALL to prevent single-line comments from consuming the rest of the file
    return re.sub(pattern, replace, json_str)

def load_json_robust(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        if not content:
            return {}

        content = remove_comments_safe(content)
        # Handle trailing commas (multiple ones and before closing brackets)
        content = re.sub(r',+(\s*[}\]])', r'\1', content)
        
        return json.loads(content)
    except Exception as e:
        print(f"\n❌ CRITICAL JSON ERROR:")
        print(f"   Could not parse file at: {path}")
        print(f"   Technical error: {e}")
        return None

def step_configure_credentials():
    print("\n🔐 [1/2] Setting up Credentials")
    print("-----------------------------------")
    
    auth = AuthManager()
    return auth.setup_credentials()

def step_display_manual_config():
    print("\n📋 [Manual Mode] Copy the configuration below")
    print("---------------------------------------------")
    print("Add this entry to your 'mcpServers' or 'servers' block in your IDE config:\n")
    
    config_block = {
        SERVER_NAME: {
            "command": "uvx",
            "args": [
                "--refresh",
                "--from",
                REPO_URL,
                "devex-mcp"
            ]
        }
    }
    
    json_str = json.dumps(config_block, indent=4)
    print(f"{json_str}")
    print("\n---------------------------------------------")
    print("✅ Configuration generated.")
    return True

def restore_backup(target_path, backup_path):
    if backup_path and backup_path.exists():
        try:
            print(f"   ↺ Restoring backup from {backup_path.name}...")
            shutil.copy2(backup_path, target_path)
            print("   ✅ Restore successful.")
        except Exception as e:
            print(f"   ❌ CRITICAL: Failed to restore backup: {e}")

def step_update_json():
    print("\n⚙️  [2/2] Configuring MCP Client")
    print("---------------------------------------")
    
    print("Select your IDE:")
    print("   1. 🟠 Claude Desktop")
    print("   2. 🔵 VS Code")
    print("   3. 🟣 Antigravity") 
    print("   4. 🟢 JetBrains (IntelliJ, PyCharm, WebStorm, GoLand)")
    print("   5. ⚪ Other / Custom Path")
    print("   6. 📋 Copy Config (Manual)")
    
    selection = input("\n👉 Select option (1-6): ").strip()
    
    ide_key = None
    if selection == "1": ide_key = "claude"
    elif selection == "2": ide_key = "vscode"
    elif selection == "3": ide_key = "antigravity"
    elif selection == "4": 
        # Unified JetBrains
        ide_key = "jetbrains"
    elif selection == "5": ide_key = "custom"
    elif selection == "6": return step_display_manual_config()
    else:
        print("❌ Invalid selection.")
        return False
    
    config_path = get_ide_config_path(ide_key)
    if not config_path: return False

    print(f"\n📂 Target: {config_path}")

    if not config_path.parent.exists():
        try:
            print(f"   -> Directory not found. Creating: {config_path.parent}")
            config_path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            print("❌ Could not create directory.")
            return False

    data = {}
    backup_path = None

    if config_path.exists():
        print("   -> Analyzing existing file...")
        try:
            backup_path = config_path.with_suffix('.json.bak')
            shutil.copy2(config_path, backup_path)
            print(f"   📦 Backup created at: {backup_path.name}")
        except Exception as e:
            print(f"   ⚠️ Backup failed: {e}")
            print("   ⛔ Aborting for safety.")
            return False

        loaded_data = load_json_robust(config_path)
        
        if loaded_data is None:
            print("\n❌ The existing configuration file is CORRUPTED or invalid.")
            print("   We cannot parse it safely.")
            
            confirm = input("👉 Do you want to BACKUP and RESET this file? (y/n): ").strip().lower()
            if confirm == 'y':
                print("   -> Proceeding to overwrite with fresh config...")
                data = {} # Start fresh
            else:
                print("⛔ ABORTING. Please fix the file manually and try again.")
                return False
        else:
            data = loaded_data
    else:
        print("   -> Creating new file.")

    new_mcp_config = {
        "command": "uvx",
        "args": [
            "--refresh",
            "--from",
            REPO_URL,
            "devex-mcp"
        ]
    }

    target_key = "mcpServers"
    
    if "servers" in data: target_key = "servers"
    elif "mcpServers" in data: target_key = "mcpServers"
    elif ide_key == "vscode": target_key = "servers"
    
    if target_key not in data:
        data[target_key] = {}

    current_keys = list(data[target_key].keys())
    if current_keys:
        print(f"   ✅ Preserving {len(current_keys)} existing servers.")
    
    data[target_key][SERVER_NAME] = new_mcp_config

    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            f.write('\n')
        print(f"\n✅ {SERVER_NAME} installed successfully!")
        return True
    except Exception as e:
        print(f"❌ Error writing file: {e}")
        if backup_path:
            restore_backup(config_path, backup_path)
        return False

def main():
    while True:
        print_header()
        print("1. ✨ Full Installation (Creds + IDE)")
        print("2. 🔐 Credentials Only")
        print("3. ⚙️  IDE Config Only")
        print("0. Exit")
        
        opt = input("\n👉 Option: ").strip()

        if opt == "1":
            if step_configure_credentials(): step_update_json()
            input("\n[Enter] to continue...")
        elif opt == "2":
            step_configure_credentials()
            input("\n[Enter] to continue...")
        elif opt == "3":
            step_update_json()
            input("\n[Enter] to continue...")
        elif opt == "0":
            print("\n👋 Bye!")
            sys.exit(0)

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: sys.exit(0)