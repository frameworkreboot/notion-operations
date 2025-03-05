#!/usr/bin/env python3
"""
Script to push changes to all remotes with safety checks.
This script ensures that sensitive information is not pushed to the frameworkreboot remote.
"""

import os
import sys
import subprocess
import re

# Sensitive patterns to check for
SENSITIVE_PATTERNS = [
    r'api_key\s*=\s*["\']([^"\']+)["\']',
    r'secret\s*=\s*["\']([^"\']+)["\']',
    r'password\s*=\s*["\']([^"\']+)["\']',
    r'token\s*=\s*["\']([^"\']+)["\']',
    # Add more patterns as needed
]

def check_for_sensitive_info(files):
    """Check if any of the files contain sensitive information."""
    for file_path in files:
        if not os.path.exists(file_path):
            continue
            
        # Skip binary files and certain directories
        if os.path.isdir(file_path) or file_path.startswith('venv/') or file_path.endswith('.bin'):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            for pattern in SENSITIVE_PATTERNS:
                matches = re.findall(pattern, content)
                if matches:
                    print(f"WARNING: Possible sensitive information found in {file_path}")
                    print(f"Pattern matched: {pattern}")
                    return True
        except UnicodeDecodeError:
            # Skip binary files that couldn't be decoded
            continue
    
    return False

def get_staged_files():
    """Get list of files staged for commit."""
    result = subprocess.run(['git', 'diff', '--name-only', '--cached'], 
                           capture_output=True, text=True)
    return result.stdout.strip().split('\n')

def get_changed_files():
    """Get list of files that have been changed but not staged."""
    result = subprocess.run(['git', 'diff', '--name-only'], 
                           capture_output=True, text=True)
    return result.stdout.strip().split('\n')

def push_to_frameworkreboot(current_branch, force=False):
    """Special handling for pushing to frameworkreboot remote."""
    print("\nPushing to frameworkreboot (clean remote)...")
    
    # Check for sensitive information in staged and changed files
    staged_files = get_staged_files()
    changed_files = get_changed_files()
    all_files = list(set(staged_files + changed_files))
    
    if check_for_sensitive_info(all_files):
        print("ERROR: Possible sensitive information detected.")
        print("Please review your changes before pushing to frameworkreboot.")
        user_input = input("Do you want to continue anyway? (y/N): ")
        if user_input.lower() != 'y':
            print("Skipping push to frameworkreboot.")
            return
    
    # Save current state
    print("Saving current state...")
    subprocess.run(['git', 'stash', 'push', '-m', 'Temporary stash for frameworkreboot push'])
    
    try:
        # Check if clean-main branch exists
        result = subprocess.run(['git', 'branch'], capture_output=True, text=True)
        branches = result.stdout.strip().split('\n')
        clean_branch_exists = any('clean-main' in branch for branch in branches)
        
        if not clean_branch_exists:
            print("Creating clean-main branch...")
            subprocess.run(['git', 'checkout', '--orphan', 'clean-main'])
            subprocess.run(['git', 'rm', '-rf', '.'])
        else:
            print("Checking out clean-main branch...")
            subprocess.run(['git', 'checkout', 'clean-main'])
        
        # Get list of files to copy from main branch
        print("Copying files from main branch...")
        subprocess.run(['git', 'checkout', current_branch, '--', '.'])
        
        # Remove sensitive files
        print("Removing sensitive files...")
        if os.path.exists('.env'):
            os.remove('.env')
        
        # Add all files
        print("Adding files to clean-main branch...")
        subprocess.run(['git', 'add', '.'])
        
        # Commit changes
        print("Committing changes to clean-main branch...")
        subprocess.run(['git', 'commit', '-m', f'Update clean-main with changes from {current_branch}'])
        
        # Push to frameworkreboot
        print("Pushing clean-main to frameworkreboot...")
        cmd = ['git', 'push', 'frameworkreboot', 'clean-main:main']
        if force:
            cmd.append('--force')
        subprocess.run(cmd)
        
        print("Push to frameworkreboot completed.")
    finally:
        # Return to original branch
        print(f"Returning to {current_branch} branch...")
        subprocess.run(['git', 'checkout', current_branch])
        
        # Apply stashed changes
        print("Applying stashed changes...")
        subprocess.run(['git', 'stash', 'pop'])

def push_to_all_remotes(branch_name, force=False):
    """Push to all remotes."""
    # Get all remotes
    result = subprocess.run(['git', 'remote'], capture_output=True, text=True)
    remotes = result.stdout.strip().split('\n')
    
    for remote in remotes:
        if not remote:
            continue
            
        # Special handling for frameworkreboot remote
        if remote == 'frameworkreboot':
            push_to_frameworkreboot(branch_name, force)
            continue
        
        # Push to other remotes
        print(f"\nPushing to {remote}...")
        cmd = ['git', 'push', remote, branch_name]
        if force:
            cmd.append('--force')
            
        subprocess.run(cmd)
        print(f"Push to {remote} completed.")

def main():
    # Get current branch
    result = subprocess.run(['git', 'branch', '--show-current'], 
                           capture_output=True, text=True)
    current_branch = result.stdout.strip()
    
    print(f"Current branch: {current_branch}")
    
    # Check if force push is requested
    force = '--force' in sys.argv
    
    # Push to all remotes
    push_to_all_remotes(current_branch, force)

if __name__ == "__main__":
    main() 