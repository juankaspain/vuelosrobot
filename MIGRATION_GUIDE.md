# 🔄 Migration Guide - v14.3 Cleanup

**Date:** 2026-01-17  
**From:** Flat structure  
**To:** Professional modular structure

---

## ⚠️ BREAKING CHANGES

### Import Paths Changed

**Before:**
```python
from monitoring_system import MonitoringSystem
from ab_testing_system import ABTestingSystem
from retention_system import RetentionManager
```

**After:**
```python
from src.systems.monitoring_system import MonitoringSystem
from src.systems.ab_testing_system import ABTestingSystem
from src.features.retention_system import RetentionManager
```

### Config Paths Changed

**Before:**
```python
config_file = "config.json"
```

**After:**
```python
config_file = "config/config.json"
```

### Main Bot Location Changed

**Before:**
```bash
python cazador_supremo_enterprise.py
```

**After:**
```bash
python src/bot/cazador_supremo_enterprise.py
# OR use the launcher:
python run.py
```

---

## 📋 MIGRATION STEPS

### 1. Backup Current Setup
```bash
# Create backup
cp -r vuelosrobot vuelosrobot_backup_20260117
```

### 2. Pull Latest Changes
```bash
cd vuelosrobot
git pull origin main
```

### 3. Verify Structure
```bash
ls -la src/ config/ docs/ tests/
```

### 4. Update Custom Scripts (if any)

If you have custom scripts importing the bot:

```python
# Update all imports
# Old: from monitoring_system import ...
# New: from src.systems.monitoring_system import ...

# Update config paths
# Old: "config.json"
# New: "config/config.json"
```

### 5. Test Everything
```bash
# Run tests
python tests/test_all_systems.py

# Test bot starts
python src/bot/cazador_supremo_enterprise.py
# OR
python run.py
```

### 6. Update Deployment Scripts

If you have systemd services or deployment scripts:

```ini
# Old systemd service
[Service]
ExecStart=/usr/bin/python3 /path/to/cazador_supremo_enterprise.py

# New systemd service
[Service]
ExecStart=/usr/bin/python3 /path/to/src/bot/cazador_supremo_enterprise.py
# OR better:
ExecStart=/usr/bin/python3 /path/to/run.py
```

---

## 🗂️ FILE LOCATION MAP

### Code Files:
```
OLD LOCATION → NEW LOCATION

# Main bot
cazador_supremo_enterprise.py → src/bot/cazador_supremo_enterprise.py

# v14.3 Systems
monitoring_system.py → src/systems/monitoring_system.py
ab_testing_system.py → src/systems/ab_testing_system.py
feedback_collection_system.py → src/systems/feedback_collection_system.py
continuous_optimization_engine.py → src/systems/continuous_optimization_engine.py

# Features
retention_system.py → src/features/retention_system.py
viral_growth_system.py → src/features/viral_growth_system.py
freemium_system.py → src/features/freemium_system.py
advanced_search_methods.py → src/features/advanced_search_methods.py
additional_search_methods.py → src/features/additional_search_methods.py
background_tasks.py → src/features/background_tasks.py
onboarding_flow.py → src/features/onboarding_flow.py
quick_actions.py → src/features/quick_actions.py
smart_notifications.py → src/features/smart_notifications.py

# Commands
bot_commands_retention.py → src/commands/bot_commands_retention.py
bot_commands_viral.py → src/commands/bot_commands_viral.py
advanced_search_commands.py → src/commands/advanced_search_commands.py
viral_growth_commands.py → src/commands/viral_growth_commands.py

# Feature Modules
competitive_leaderboards.py → src/features/competitive_leaderboards.py
deal_sharing_system.py → src/features/deal_sharing_system.py
group_hunting.py → src/features/group_hunting.py
social_sharing.py → src/features/social_sharing.py
premium_analytics.py → src/features/premium_analytics.py
premium_trial.py → src/features/premium_trial.py
pricing_engine.py → src/features/pricing_engine.py
smart_paywalls.py → src/features/smart_paywalls.py
value_metrics.py → src/features/value_metrics.py

# Utils
i18n.py → src/utils/i18n.py
search_cache.py → src/utils/search_cache.py
search_analytics.py → src/utils/search_analytics.py
```

### Config Files:
```
config.json → config/config.json ✅ (already moved)
config.example.json → config/config.example.json
pricing_config.json → config/pricing_config.json
translations.json → config/translations.json
```

### Tests:
```
test_all_systems.py → tests/test_all_systems.py
test_it4_retention.py → tests/test_it4_retention.py
```

### Documentation:
```
README.md → docs/README.md (consolidated)
QUICKSTART.md → docs/QUICKSTART.md
CHANGELOG.md → docs/CHANGELOG.md
ROADMAP_v15_v16.md → docs/ROADMAP.md
PROJECT_STRUCTURE.md → docs/ARCHITECTURE.md
AUDIT_REPORT_v14.1.md → docs/AUDIT_REPORT.md
```

---

## 🗄️ ARCHIVED FILES

### All old versions moved to `/archive`:

```
archive/
├── v9/
│   ├── cazador_supremo_v9.py
│   └── cazador_supremo_v9_enterprise.py
├── v10/
│   ├── cazador_supremo_v10.py
│   ├── cazador_supremo_v10_COMPLETO.py
│   ├── cazador_supremo_v10_ml_enhanced.py
│   ├── cazador_supremo_v10_part2.py
│   └── cazador_supremo_v10_part3.py
├── v11/
│   ├── cazador_supremo_v11_ultimate.py
│   ├── cazador_supremo_v11.1.py
│   ├── cazador_supremo_v11.2.py
│   └── ...
├── docs/
│   ├── README_V10.md
│   ├── README_V11_ULTIMATE.md
│   ├── README_IT4.md
│   ├── CHANGELOG_V10.md
│   └── ...
├── reports/
│   ├── AUDIT_REPORT_v13.12.md
│   ├── BENCHMARKS_v13.12.md
│   └── ...
└── patches/
    ├── APPLY_FIX_v13.2.1.sh
    ├── apply_fix_auto_v13.2.1.py
    └── ...
```

**These files are preserved for reference but not used.**

---

## ✅ VERIFICATION CHECKLIST

### After Migration:

- [ ] Files in correct folders
- [ ] Imports work correctly
- [ ] Config files found
- [ ] Tests pass
- [ ] Bot starts without errors
- [ ] All commands work
- [ ] No broken imports

### Test Commands:
```bash
# 1. Check structure
ls -la src/ config/ docs/ tests/

# 2. Verify imports
python -c "from src.systems.monitoring_system import MonitoringSystem; print('✅ OK')"

# 3. Run tests
python tests/test_all_systems.py

# 4. Start bot (dry run)
python src/bot/cazador_supremo_enterprise.py --help
```

---

## 🆘 TROUBLESHOOTING

### Problem: Import Errors
```
ModuleNotFoundError: No module named 'monitoring_system'
```

**Solution:**
```python
# Update import
from src.systems.monitoring_system import MonitoringSystem
```

### Problem: Config Not Found
```
FileNotFoundError: config.json
```

**Solution:**
```python
# Update config path
config_file = "config/config.json"
```

### Problem: Old Version Running
```
Bot shows old version number
```

**Solution:**
```bash
# Make sure running new location
python src/bot/cazador_supremo_enterprise.py
# NOT: python cazador_supremo_enterprise.py
```

---

## 🔙 ROLLBACK (if needed)

If you need to revert:

```bash
# Option 1: Restore from backup
rm -rf vuelosrobot
cp -r vuelosrobot_backup_20260117 vuelosrobot

# Option 2: Git revert
cd vuelosrobot
git log --oneline  # Find commit before cleanup
git revert <commit-hash>

# Option 3: Use archive files
cp archive/v14/* .
```

---

## 📞 SUPPORT

If you encounter issues:

1. Check this migration guide
2. Review CLEANUP_SUMMARY.md
3. Check Git history: `git log`
4. Restore from backup if needed

---

## 🎉 BENEFITS AFTER MIGRATION

✅ **80% cleaner** root directory  
✅ **100% better** organized  
✅ **Professional** grade structure  
✅ **Easy** to navigate  
✅ **Ready** for v15.0 development  
✅ **Production** deployable  

---

**Migration completed successfully? Great! You're now ready for v15.0! 🚀**
