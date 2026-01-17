# 🚀 Deployment Guide

## Quick Start

After the v15.0 cleanup, the bot can be launched using:

```bash
# Option 1: Use the launcher
python run.py

# Option 2: Direct execution
python src/bot/cazador_supremo_enterprise.py

# Option 3: With optimizations
python src/bot/cazador_supremo_enterprise.py --auto-optimize
```

## Structure

The new structure is:

```
vuelosrobot/
├── src/
│   ├── bot/                    # Main bot
│   ├── systems/                # Core systems
│   ├── features/               # Features
│   ├── commands/               # Commands
│   └── utils/                  # Utilities
├── config/                     # Configuration
├── docs/                       # Documentation
├── tests/                      # Tests
├── run.py                      # Launcher
└── requirements.txt
```

## Requirements

```bash
pip install -r requirements.txt
```

## Configuration

1. Copy config example:
```bash
cp config/config.example.json config/config.json
```

2. Edit `config/config.json` with your credentials

3. Run the bot:
```bash
python run.py
```

## Production Deployment

For production use:

1. Set up systemd service (Linux)
2. Configure monitoring
3. Enable auto-optimization
4. Set up log rotation

See docs/ for detailed guides.
