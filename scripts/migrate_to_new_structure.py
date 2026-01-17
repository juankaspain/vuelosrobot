#!/usr/bin/env python3
"""
🔄 AUTOMATED MIGRATION SCRIPT
================================
This script moves all files from the root directory to the new professional structure.
It's safe to run multiple times (idempotent).

Usage:
    python scripts/migrate_to_new_structure.py
"""

import os
import shutil
from pathlib import Path

# Define the migration map
MIGRATION_MAP = {
    # Systems (v14.3)
    'monitoring_system.py': 'src/systems/',
    'retention_system.py': 'src/features/',
    'viral_growth_system.py': 'src/features/',
    'freemium_system.py': 'src/features/',
    'continuous_optimization_engine.py': 'src/systems/',
    'pricing_engine.py': 'src/features/',
    
    # Features
    'ab_testing_system.py': 'src/features/',
    'premium_analytics.py': 'src/features/',
    'premium_trial.py': 'src/features/',
    'feedback_collection_system.py': 'src/features/',
    'smart_notifications.py': 'src/features/',
    'competitive_leaderboards.py': 'src/features/',
    'deal_sharing_system.py': 'src/features/',
    'group_hunting.py': 'src/features/',
    'social_sharing.py': 'src/features/',
    
    # Commands
    'bot_commands_retention.py': 'src/commands/',
    'bot_commands_viral.py': 'src/commands/',
    'viral_growth_commands.py': 'src/commands/',
    'advanced_search_commands.py': 'src/commands/',
    
    # Search & Analytics
    'additional_search_methods.py': 'src/features/',
    'advanced_search_methods.py': 'src/features/',
    'search_analytics.py': 'src/features/',
    'search_cache.py': 'src/features/',
    
    # UI & Paywall
    'freemium_paywalls.py': 'src/features/',
    'smart_paywalls.py': 'src/features/',
    'value_metrics.py': 'src/features/',
    'onboarding_flow.py': 'src/features/',
    'onboarding_and_quickactions.py': 'src/features/',
    'quick_actions.py': 'src/features/',
    
    # Utilities
    'i18n.py': 'src/utils/',
    'background_tasks.py': 'src/utils/',
    
    # Old Versions (Archive)
    'cazador_supremo_v9.py': 'archive/v9/',
    'cazador_supremo_v9_enterprise.py': 'archive/v9/',
    'cazador_supremo_v10.py': 'archive/v10/',
    'cazador_supremo_v10_COMPLETO.py': 'archive/v10/',
    'cazador_supremo_v10_ml_enhanced.py': 'archive/v10/',
    'cazador_supremo_v10_part2.py': 'archive/v10/',
    'cazador_supremo_v10_part3.py': 'archive/v10/',
    'cazador_supremo_v11.1.py': 'archive/v11/',
    'cazador_supremo_v11.1_ultimate.py': 'archive/v11/',
    'cazador_supremo_v11.2.py': 'archive/v11/',
    'cazador_supremo_v11.2_ultimate.py': 'archive/v11/',
    'cazador_supremo_v11_ultimate.py': 'archive/v11/',
    'vuelos_bot_unified.py': 'archive/v12/',
    
    # Documentation (old versions)
    'README_IT4.md': 'archive/docs/',
    'README_IT5.md': 'archive/docs/',
    'README_IT6.md': 'archive/docs/',
    'README_V10.md': 'archive/docs/',
    'README_V11_ULTIMATE.md': 'archive/docs/',
    'CHANGELOG_V10.md': 'archive/docs/',
    'LEEME.md': 'archive/docs/',
    
    # Reports & Audits
    'AUDIT_REPORT_v13.12.md': 'docs/reports/',
    'AUDIT_REPORT_v14.1.md': 'docs/reports/',
    'BENCHMARKS_v13.12.md': 'docs/reports/',
    'TESTING_REPORT_v13.12.md': 'docs/reports/',
    'ONBOARDING_AUDIT_REPORT.md': 'docs/reports/',
    
    # Status & Planning
    'STATUS.md': 'docs/planning/',
    'ROADMAP_v14.md': 'docs/planning/',
    'ROADMAP_v15_v16.md': 'docs/planning/',
    'IMPLEMENTATION_PLAN_v14.0.md': 'docs/planning/',
    'V14.0_COMPLETE.md': 'docs/reports/',
    'V14.0_PHASE2_COMPLETE.md': 'docs/reports/',
    'V14.0_STATUS.md': 'docs/reports/',
    'IMPLEMENTACION_COMPLETADA.md': 'docs/reports/',
    'RESUMEN_FINAL.md': 'docs/reports/',
    
    # Quick Guides
    'QUICKSTART.md': 'docs/',
    'PROJECT_STRUCTURE.md': 'docs/',
    
    # Scripts & Fixes
    'merge_v10.sh': 'scripts/',
    'merge_v10.ps1': 'scripts/',
    'apply_fix_auto_v13.2.1.py': 'scripts/fixes/',
    'quick_fix_callbacks.py': 'scripts/fixes/',
    'fix_csv.py': 'scripts/fixes/',
    'patch_v12_bugs.py': 'scripts/fixes/',
    'restore_and_fix.py': 'scripts/fixes/',
    'onboarding_patch_v13.2.1.py': 'scripts/fixes/',
    'APPLY_FIX_v13.2.1.sh': 'scripts/fixes/',
    'UPDATE_INSTRUCTIONS_v13.2.1.md': 'scripts/fixes/',
    
    # Test files
    'test_all_systems.py': 'tests/',
    'test_it4_retention.py': 'tests/',
    
    # Config files (keep in root, just note them)
    # config.json, config.json.example, config.example.json
    
    # Data files (keep in root or move to data/)
    'feature_usage.json': 'data/',
    'paywall_events.json': 'data/',
    'pricing_config.json': 'data/',
    'translations.json': 'data/',
}


def migrate_files():
    """Execute the migration."""
    root = Path.cwd()
    moved_count = 0
    skipped_count = 0
    
    print("🚀 Starting migration to new structure...\n")
    
    # Create all necessary directories first
    dirs_to_create = set()
    for dest in MIGRATION_MAP.values():
        dirs_to_create.add(dest)
    
    for dir_path in sorted(dirs_to_create):
        full_path = root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {dir_path}")
    
    # Create data directory
    (root / 'data').mkdir(exist_ok=True)
    print(f"✅ Created directory: data/\n")
    
    print("📦 Moving files...\n")
    
    # Move each file
    for source_file, dest_dir in MIGRATION_MAP.items():
        source_path = root / source_file
        dest_path = root / dest_dir / source_file
        
        if source_path.exists():
            if dest_path.exists():
                print(f"⏭️  Skipped (exists): {source_file} → {dest_dir}")
                skipped_count += 1
            else:
                shutil.move(str(source_path), str(dest_path))
                print(f"✅ Moved: {source_file} → {dest_dir}")
                moved_count += 1
        else:
            print(f"⚠️  Not found: {source_file}")
    
    print(f"\n{'='*60}")
    print(f"📊 Migration Summary:")
    print(f"   ✅ Moved: {moved_count} files")
    print(f"   ⏭️  Skipped: {skipped_count} files")
    print(f"{'='*60}\n")
    
    print("🎉 Migration complete!")
    print("\n💡 Next steps:")
    print("   1. Review the changes")
    print("   2. Update imports in affected files")
    print("   3. Test the bot: python run.py")
    print("   4. Commit: git add . && git commit -m '🏗️ Complete structure migration'")


if __name__ == '__main__':
    try:
        migrate_files()
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        print("   Please review and fix manually.")
