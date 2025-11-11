"""
Multi-Server Migration Helper Script

This script helps identify all places that need to be updated for multi-server support.
Run this to see what needs to be changed.
"""

import re
import os

def analyze_file(filepath):
    """Analyze a Python file for patterns that need updating"""
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return
    
    with open(filepath, 'r') as f:
        content = f.read()
        lines = content.split('\n')
    
    print(f"\n{'='*80}")
    print(f"📄 Analyzing: {filepath}")
    print(f"{'='*80}\n")
    
    issues = []
    
    # Pattern 1: Commands without guild_id
    command_pattern = r'async def (\w+)\(self, interaction: discord\.Interaction\):'
    commands = re.finditer(command_pattern, content)
    for match in commands:
        command_name = match.group(1)
        # Check if guild_id is used in the function
        func_start = match.start()
        # Find next function or end of file
        next_func = content.find('\n    async def ', func_start + 1)
        if next_func == -1:
            next_func = content.find('\n    @app_commands', func_start + 1)
        if next_func == -1:
            next_func = len(content)
        
        func_body = content[func_start:next_func]
        
        if 'guild_id' not in func_body and 'interaction.guild' not in func_body:
            line_no = content[:func_start].count('\n') + 1
            issues.append({
                'type': 'MISSING_GUILD_ID',
                'line': line_no,
                'command': command_name,
                'severity': 'HIGH'
            })
    
    # Pattern 2: Direct data.get() calls (should be server_data.get())
    data_get_pattern = r'data\.get\('
    data_gets = re.finditer(data_get_pattern, content)
    for match in data_gets:
        line_no = content[:match.start()].count('\n') + 1
        line_content = lines[line_no - 1].strip()
        # Ignore if it's getting config (global)
        if '"config"' not in line_content:
            issues.append({
                'type': 'DIRECT_DATA_ACCESS',
                'line': line_no,
                'content': line_content,
                'severity': 'HIGH'
            })
    
    # Pattern 3: data.setdefault() calls
    data_setdefault_pattern = r'data\.setdefault\('
    data_setdefaults = re.finditer(data_setdefault_pattern, content)
    for match in data_setdefaults:
        line_no = content[:match.start()].count('\n') + 1
        line_content = lines[line_no - 1].strip()
        if '"config"' not in line_content:
            issues.append({
                'type': 'DIRECT_DATA_SETDEFAULT',
                'line': line_no,
                'content': line_content,
                'severity': 'HIGH'
            })
    
    # Pattern 4: Missing get_server_data import
    if 'from .database import get_server_data, save_server_data' not in content:
        if 'data = await load_data()' in content:
            issues.append({
                'type': 'MISSING_IMPORT',
                'line': 1,
                'content': 'Missing: from .database import get_server_data, save_server_data',
                'severity': 'MEDIUM'
            })
    
    # Group and display issues
    if not issues:
        print("✅ No issues found!")
        return
    
    print(f"Found {len(issues)} potential issues:\n")
    
    # Group by type
    by_type = {}
    for issue in issues:
        issue_type = issue['type']
        if issue_type not in by_type:
            by_type[issue_type] = []
        by_type[issue_type].append(issue)
    
    for issue_type, type_issues in by_type.items():
        print(f"\n🔍 {issue_type} ({len(type_issues)} occurrences):")
        print("-" * 80)
        
        for issue in type_issues[:10]:  # Show first 10
            severity_icon = "🔴" if issue['severity'] == 'HIGH' else "🟡"
            print(f"{severity_icon} Line {issue['line']}: {issue.get('content', issue.get('command', 'N/A'))}")
        
        if len(type_issues) > 10:
            print(f"... and {len(type_issues) - 10} more")
    
    print(f"\n{'='*80}\n")
    return issues

def main():
    """Analyze all bot module files"""
    print("\n🔍 Multi-Server Migration Analyzer")
    print("=" * 80)
    
    modules = [
        'bot_modules/economy.py',
        'bot_modules/casino.py',
        'bot_modules/shop.py',
        'bot_modules/guild.py',
        'bot_modules/market.py',
        'bot_modules/leaderboard.py',
        'bot_modules/admin.py',
        'bot_modules/heist.py',
    ]
    
    all_issues = {}
    total_issues = 0
    
    for module in modules:
        issues = analyze_file(module)
        if issues:
            all_issues[module] = issues
            total_issues += len(issues)
    
    print(f"\n{'='*80}")
    print(f"📊 SUMMARY")
    print(f"{'='*80}")
    print(f"Total files analyzed: {len(modules)}")
    print(f"Files with issues: {len(all_issues)}")
    print(f"Total issues found: {total_issues}")
    print(f"\n🎯 Priority: Start with economy.py, then casino.py, then shop.py")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
