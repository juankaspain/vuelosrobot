# VuelosBot v15.0 - Legacy Files Archive

This directory contains all legacy files from v15.0.x and earlier versions.

## Archive Date
2026-01-18 00:26 CET

## Reason for Archiving
Migration to v16.0.0 Enterprise Architecture (4-tier structure)

## Contents
- cazador_supremo_v*.py - All old bot versions (v9, v10, v11)
- test_*.py - Legacy test files
- apply_fix_*.py - Temporary hotfix scripts
- patch_*.py - Temporary patch scripts
- restore_*.py - Restore scripts
- quick_fix_*.py - Quick fix scripts
- fix_*.py - Fix utility scripts
- merge_*.py - Merge utility scripts

## How to Access
If you need any of these files:
```bash
cd archive/v15/
ls -la
```

## Migration to v16
All active modules have been moved to:
- src/bot/ - Bot layer
- src/core/ - Core systems
- src/features/ - Features
- src/utils/ - Utilities

## Documentation
See:
- ../../ARCHITECTURE.md
- ../../PROJECT_STRUCTURE.md
- ../../MIGRATION_GUIDE.md
