#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔════════════════════════════════════════════════════════════════╗
║  🧹 MASSIVE REPOSITORY CLEANUP AUTOMATION                    ║
║  📦 Moves 80+ files to proper structure                       ║
╚════════════════════════════════════════════════════════════════╝

Este script automatiza el movimiento masivo de archivos
del root a la estructura organizada de carpetas.

Usage:
    python scripts/massive_cleanup.py [--dry-run]
"""

# ═══════════════════════════════════════════════════════════════
#  FILE MOVEMENT MAP
# ═══════════════════════════════════════════════════════════════

MOVE_MAP = {
    # ══════════════ SYSTEMS → src/systems/ ══════════════
    'monitoring_system.py': 'src/systems/monitoring_system.py',
    'retention_system.py': 'src/systems/retention_system.py',
    'viral_growth_system.py': 'src/systems/viral_growth_system.py',
    'freemium_system.py': 'src/systems/freemium_system.py',
    'ab_testing_system.py': 'src/systems/ab_testing_system.py',
    'continuous_optimization_engine.py': 'src/systems/continuous_optimization_engine.py',
    
    # ══════════════ FEATURES → src/features/ ══════════════
    'onboarding_flow.py': 'src/features/onboarding_flow.py',
    'onboarding_and_quickactions.py': 'src/features/onboarding_and_quickactions.py',
    'quick_actions.py': 'src/features/quick_actions.py',
    'freemium_paywalls.py': 'src/features/freemium_paywalls.py',
    'smart_paywalls.py': 'src/features/smart_paywalls.py',
    'pricing_engine.py': 'src/features/pricing_engine.py',
    'premium_trial.py': 'src/features/premium_trial.py',
    'premium_analytics.py': 'src/features/premium_analytics.py',
    'deal_sharing_system.py': 'src/features/deal_sharing_system.py',
    'social_sharing.py': 'src/features/social_sharing.py',
    'group_hunting.py': 'src/features/group_hunting.py',
    'competitive_leaderboards.py': 'src/features/competitive_leaderboards.py',
    'value_metrics.py': 'src/features/value_metrics.py',
    'smart_notifications.py': 'src/features/smart_notifications.py',
    'feedback_collection_system.py': 'src/features/feedback_collection_system.py',
    'background_tasks.py': 'src/features/background_tasks.py',
    
    # ══════════════ COMMANDS → src/commands/ ══════════════
    'advanced_search_commands.py': 'src/commands/advanced_search_commands.py',
    'advanced_search_methods.py': 'src/commands/advanced_search_methods.py',
    'additional_search_methods.py': 'src/commands/additional_search_methods.py',
    'viral_growth_commands.py': 'src/commands/viral_growth_commands.py',
    'bot_commands_retention.py': 'src/commands/bot_commands_retention.py',
    'bot_commands_viral.py': 'src/commands/bot_commands_viral.py',
    
    # ══════════════ UTILS → src/utils/ ══════════════
    'search_cache.py': 'src/utils/search_cache.py',
    'search_analytics.py': 'src/utils/search_analytics.py',
    'i18n.py': 'src/utils/i18n.py',
    
    # ══════════════ CONFIG → config/ ══════════════
    'config.json': 'config/config.json',
    'config.example.json': 'config/config.example.json',
    'config.json.example': 'config/config.example2.json',
    'pricing_config.json': 'config/pricing_config.json',
    'translations.json': 'config/translations.json',
    'feature_usage.json': 'config/feature_usage.json',
    'paywall_events.json': 'config/paywall_events.json',
    
    # ══════════════ DOCS → docs/ ══════════════
    'CHANGELOG.md': 'docs/CHANGELOG.md',
    'CHANGELOG_V10.md': 'docs/legacy/CHANGELOG_V10.md',
    'LEEME.md': 'docs/LEEME.md',
    'QUICKSTART.md': 'docs/QUICKSTART.md',
    'STATUS.md': 'docs/STATUS.md',
    'PROJECT_STRUCTURE.md': 'docs/PROJECT_STRUCTURE.md',
    'CLEANUP_PLAN.md': 'docs/cleanup/CLEANUP_PLAN.md',
    'CLEANUP_SUMMARY.md': 'docs/cleanup/CLEANUP_SUMMARY.md',
    'CLEANUP_COMPLETE.md': 'docs/cleanup/CLEANUP_COMPLETE.md',
    'MIGRATION_GUIDE.md': 'docs/cleanup/MIGRATION_GUIDE.md',
    
    # Implementación docs
    'IMPLEMENTACION_COMPLETADA.md': 'docs/implementation/IMPLEMENTACION_COMPLETADA.md',
    'IMPLEMENTATION_PLAN_v14.0.md': 'docs/implementation/IMPLEMENTATION_PLAN_v14.0.md',
    'RESUMEN_FINAL.md': 'docs/implementation/RESUMEN_FINAL.md',
    
    # Audit reports
    'AUDIT_REPORT_v13.12.md': 'docs/audits/AUDIT_REPORT_v13.12.md',
    'AUDIT_REPORT_v14.1.md': 'docs/audits/AUDIT_REPORT_v14.1.md',
    'ONBOARDING_AUDIT_REPORT.md': 'docs/audits/ONBOARDING_AUDIT_REPORT.md',
    'BENCHMARKS_v13.12.md': 'docs/audits/BENCHMARKS_v13.12.md',
    'TESTING_REPORT_v13.12.md': 'docs/audits/TESTING_REPORT_v13.12.md',
    
    # Version docs
    'V14.0_COMPLETE.md': 'docs/versions/V14.0_COMPLETE.md',
    'V14.0_PHASE2_COMPLETE.md': 'docs/versions/V14.0_PHASE2_COMPLETE.md',
    'V14.0_STATUS.md': 'docs/versions/V14.0_STATUS.md',
    
    # Roadmaps
    'ROADMAP_v14.md': 'docs/roadmaps/ROADMAP_v14.md',
    'ROADMAP_v15_v16.md': 'docs/roadmaps/ROADMAP_v15_v16.md',
    
    # READMEs legacy
    'README_IT4.md': 'docs/legacy/README_IT4.md',
    'README_IT5.md': 'docs/legacy/README_IT5.md',
    'README_IT6.md': 'docs/legacy/README_IT6.md',
    'README_V10.md': 'docs/legacy/README_V10.md',
    'README_V11_ULTIMATE.md': 'docs/legacy/README_V11_ULTIMATE.md',
    
    # ══════════════ ARCHIVE → archive/ ══════════════
    # Versiones antiguas del bot
    'cazador_supremo_v9.py': 'archive/v9/cazador_supremo_v9.py',
    'cazador_supremo_v9_enterprise.py': 'archive/v9/cazador_supremo_v9_enterprise.py',
    
    'cazador_supremo_v10.py': 'archive/v10/cazador_supremo_v10.py',
    'cazador_supremo_v10_COMPLETO.py': 'archive/v10/cazador_supremo_v10_COMPLETO.py',
    'cazador_supremo_v10_ml_enhanced.py': 'archive/v10/cazador_supremo_v10_ml_enhanced.py',
    'cazador_supremo_v10_part2.py': 'archive/v10/cazador_supremo_v10_part2.py',
    'cazador_supremo_v10_part3.py': 'archive/v10/cazador_supremo_v10_part3.py',
    
    'cazador_supremo_v11.1.py': 'archive/v11/cazador_supremo_v11.1.py',
    'cazador_supremo_v11.1_ultimate.py': 'archive/v11/cazador_supremo_v11.1_ultimate.py',
    'cazador_supremo_v11.2.py': 'archive/v11/cazador_supremo_v11.2.py',
    'cazador_supremo_v11.2_ultimate.py': 'archive/v11/cazador_supremo_v11.2_ultimate.py',
    'cazador_supremo_v11_ultimate.py': 'archive/v11/cazador_supremo_v11_ultimate.py',
    
    'vuelos_bot_unified.py': 'archive/old/vuelos_bot_unified.py',
    
    # Patches y fixes obsoletos
    'APPLY_FIX_v13.2.1.sh': 'archive/patches/APPLY_FIX_v13.2.1.sh',
    'apply_fix_auto_v13.2.1.py': 'archive/patches/apply_fix_auto_v13.2.1.py',
    'onboarding_patch_v13.2.1.py': 'archive/patches/onboarding_patch_v13.2.1.py',
    'patch_v12_bugs.py': 'archive/patches/patch_v12_bugs.py',
    'quick_fix_callbacks.py': 'archive/patches/quick_fix_callbacks.py',
    'restore_and_fix.py': 'archive/patches/restore_and_fix.py',
    'UPDATE_INSTRUCTIONS_v13.2.1.md': 'archive/patches/UPDATE_INSTRUCTIONS_v13.2.1.md',
    
    # Scripts obsoletos
    'fix_csv.py': 'archive/scripts/fix_csv.py',
    'merge_v10.ps1': 'archive/scripts/merge_v10.ps1',
    'merge_v10.sh': 'archive/scripts/merge_v10.sh',
    
    # ══════════════ TESTS → tests/ ══════════════
    'test_all_systems.py': 'tests/test_all_systems.py',
    'test_it4_retention.py': 'tests/test_it4_retention.py',
}

# Archivos que NO se deben mover (quedan en root)
KEEP_IN_ROOT = [
    'README.md',
    'requirements.txt',
    'VERSION.txt',
    'run.py',
    '.gitignore',
    'cazador_supremo_enterprise.py',  # Bot principal actual
]

# ═══════════════════════════════════════════════════════════════
#  EXECUTION SUMMARY
# ═══════════════════════════════════════════════════════════════

def print_summary():
    """Imprime resumen del cleanup"""
    
    by_dest = {}
    for src, dest in MOVE_MAP.items():
        folder = dest.split('/')[0] if '/' in dest else 'root'
        by_dest.setdefault(folder, []).append(src)
    
    print("\n" + "="*70)
    print("📋 MASSIVE CLEANUP SUMMARY".center(70))
    print("="*70 + "\n")
    
    print(f"Total files to move: {len(MOVE_MAP)}")
    print(f"Files staying in root: {len(KEEP_IN_ROOT)}\n")
    
    print("Destination breakdown:")
    for folder, files in sorted(by_dest.items()):
        print(f"  📁 {folder}/: {len(files)} files")
    
    print("\n" + "="*70)
    print("\n⚠️  IMPORTANT:")
    print("  • This script requires GitHub API with write access")
    print("  • Files will be MOVED (created + deleted)")
    print("  • Backup recommended before execution")
    print("  • Use --dry-run to preview changes")
    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    import sys
    
    dry_run = '--dry-run' in sys.argv
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No files will be moved\n")
    
    print_summary()
    
    if not dry_run:
        response = input("\n🚀 Proceed with massive cleanup? [y/N]: ")
        if response.lower() != 'y':
            print("❌ Cancelled")
            sys.exit(0)
        
        print("\n⚠️  THIS REQUIRES MANUAL EXECUTION VIA GITHUB API")
        print("   Run this through the GitHub MCP connector!\n")
