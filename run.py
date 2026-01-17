#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Cazador Supremo - Launcher Script

Convenience script to run the bot from root directory.
Handles path setup automatically.

Usage:
    python run.py

Author: @Juanka_Spain
Version: 14.3.0
Date: 2026-01-17
"""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Run main bot
if __name__ == "__main__":
    try:
        print("\n" + "="*80)
        print("🚀 Starting Cazador Supremo v14.3 Enterprise".center(80))
        print("="*80 + "\n")
        
        # Import and run bot
        from bot.cazador_supremo_enterprise import main
        import asyncio
        
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n✋ Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting bot: {e}")
        print("\n💡 Tip: Make sure you have:")
        print("  1. Configured config/config.json")
        print("  2. Installed requirements: pip install -r requirements.txt")
        print("  3. All systems available in src/systems/")
        sys.exit(1)
