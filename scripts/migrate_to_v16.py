#!/usr/bin/env python3
"""Migration script from v15 to v16 structure."""

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent

FILES_TO_MOVE = {
    # Core layer
    'monitoring_system.py': 'src/core/',
    'continuous_optimization_engine.py': 'src/core/',
    
    # Features layer
    'retention_system.py': 'src/features/',
    'viral_growth_system.py': 'src/features/',
    'freemium_system.py': 'src/features/',
    'premium_analytics.py': 'src/features/',
    'ab_testing_system.py': 'src/features/',
    'feedback_collection_system.py': 'src/features/',
    'smart_notifications.py': 'src/features/',
    'group_hunting.py': 'src/features/',
    'deal_sharing_system.py': 'src/features/',
    'competitive_leaderboards.py': 'src/features/',
    'social_sharing.py': 'src/features/',
    'background_tasks.py': 'src/features/',
    'onboarding_flow.py': 'src/features/',
    'quick_actions.py': 'src/features/',
    'search_cache.py': 'src/features/',
    'search_analytics.py': 'src/features/',
    'premium_trial.py': 'src/features/',
    'smart_paywalls.py': 'src/features/',
    'value_metrics.py': 'src/features/',
    'pricing_engine.py': 'src/features/',
    'freemium_paywalls.py': 'src/features/',
    'onboarding_and_quickactions.py': 'src/features/',
    'bot_commands_retention.py': 'src/features/',
    'bot_commands_viral.py': 'src/features/',
    'viral_growth_commands.py': 'src/features/',
    'advanced_search_methods.py': 'src/features/',
    'advanced_search_commands.py': 'src/features/',
    'additional_search_methods.py': 'src/features/',
    
    # Utils layer
    'i18n.py': 'src/utils/',
}

FILES_TO_ARCHIVE = [
    # Old bot versions
    'cazador_supremo_v9.py',
    'cazador_supremo_v9_enterprise.py',
    'cazador_supremo_v10.py',
    'cazador_supremo_v10_COMPLETO.py',
    'cazador_supremo_v10_ml_enhanced.py',
    'cazador_supremo_v10_part2.py',
    'cazador_supremo_v10_part3.py',
    'cazador_supremo_v11.1.py',
    'cazador_supremo_v11.1_ultimate.py',
    'cazador_supremo_v11.2.py',
    'cazador_supremo_v11.2_ultimate.py',
    'cazador_supremo_v11_ultimate.py',
    'cazador_supremo_enterprise.py',
    
    # Test files
    'test_all_systems.py',
    'test_it4_retention.py',
    
    # Patches and fixes
    'apply_fix_auto_v13.2.1.py',
    'onboarding_patch_v13.2.1.py',
    'patch_v12_bugs.py',
    'quick_fix_callbacks.py',
    'restore_and_fix.py',
    'fix_csv.py',
    
    # Merge scripts
    'merge_v10.ps1',
    'merge_v10.sh',
]

def migrate():
    print("🚀 VuelosBot v15 → v16 Migration Script\n")
    
    # Move active files
    print("📦 Moving active modules to src/...")
    for src_file, dest_dir in FILES_TO_MOVE.items():
        src_path = ROOT / src_file
        dest_path = ROOT / dest_dir / src_file
        
        if src_path.exists():
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_path), str(dest_path))
            print(f"  ✅ {src_file} → {dest_dir}")
        else:
            print(f"  ⚠️  {src_file} not found (skipping)")
    
    # Archive old files
    print("\n🗄️  Archiving legacy files...")
    archive_dir = ROOT / 'archive' / 'v15'
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    for filename in FILES_TO_ARCHIVE:
        src_path = ROOT / filename
        dest_path = archive_dir / filename
        
        if src_path.exists():
            shutil.move(str(src_path), str(dest_path))
            print(f"  ✅ {filename} → archive/v15/")
        else:
            print(f"  ⚠️  {filename} not found (skipping)")
    
    print("\n✅ Migration complete!")
    print("\n📚 Next steps:")
    print("  1. Update imports in your code")
    print("  2. Run: python -m pytest tests/")
    print("  3. Start bot: python vuelos_bot_unified.py")
    print("\n📖 See: MIGRATION_GUIDE.md for details\n")

if __name__ == '__main__':
    migrate()
