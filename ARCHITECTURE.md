# 🏗️ VuelosBot Architecture v16.0

## 📐 Enterprise 4-Tier Architecture

```
vuelosrobot/
├── 📁 src/                     # Source Code (4-tier)
│   ├── bot/                  # Tier 1: Bot Layer
│   │   ├── __init__.py
│   │   └── vuelos_bot_unified.py
│   ├── core/                 # Tier 2: Core Systems
│   │   ├── __init__.py
│   │   ├── search_engine.py
│   │   ├── deal_detector.py
│   │   ├── alert_manager.py
│   │   └── monitoring_system.py
│   ├── features/             # Tier 3: Features
│   │   ├── __init__.py
│   │   ├── retention_system.py
│   │   ├── viral_growth_system.py
│   │   ├── freemium_system.py
│   │   ├── premium_analytics.py
│   │   ├── ab_testing_system.py
│   │   ├── feedback_collection_system.py
│   │   └── smart_notifications.py
│   └── utils/                # Tier 4: Utilities
│       ├── __init__.py
│       ├── i18n.py
│       ├── config_manager.py
│       └── data_manager.py
├── 📂 data/                  # Data & Config
│   ├── bot_config.json
│   ├── translations.json
│   └── pricing_config.json
├── 📚 docs/                  # Documentation
│   ├── README.md
│   ├── API.md
│   └── USER_GUIDE.md
├── 🗄️ archive/               # Old Versions
│   ├── v9/
│   ├── v10/
│   ├── v11/
│   └── v15/
├── 🧪 tests/                 # Tests
├── 🔧 scripts/               # Utility Scripts
│   └── migrate.py
├── 📝 README.md              # Main README
├── 🚀 run.py                 # Launcher
└── 📋 requirements.txt       # Dependencies
```

## 🎯 Design Principles

### 1. **Separation of Concerns**
- Bot layer handles Telegram interaction
- Core layer implements business logic
- Features are modular and independent
- Utils provide shared functionality

### 2. **Modularity**
- Each feature is self-contained
- Easy to add/remove features
- Clear dependencies
- Testable components

### 3. **Maintainability**
- Clean imports
- Organized structure
- Clear naming conventions
- Proper documentation

### 4. **Scalability**
- Horizontal scaling ready
- Async/await support
- Efficient caching
- Load balancing compatible

## 📦 Layer Details

### Tier 1: Bot Layer (`src/bot/`)
**Responsibility:** Telegram bot interface

**Components:**
- `vuelos_bot_unified.py` - Main bot implementation
- Command handlers
- Callback query handlers
- Message handlers
- Menu system

**Dependencies:** → Core, Features, Utils

### Tier 2: Core Layer (`src/core/`)
**Responsibility:** Business logic and core systems

**Components:**
- `search_engine.py` - Flight search engines
- `deal_detector.py` - Deal detection logic
- `alert_manager.py` - Price alerts management
- `monitoring_system.py` - System monitoring

**Dependencies:** → Utils

### Tier 3: Features Layer (`src/features/`)
**Responsibility:** Modular functionalities

**Components:**
- `retention_system.py` - User retention
- `viral_growth_system.py` - Viral mechanics
- `freemium_system.py` - Freemium model
- `premium_analytics.py` - Analytics
- `ab_testing_system.py` - A/B testing
- `feedback_collection_system.py` - Feedback
- `smart_notifications.py` - Notifications

**Dependencies:** → Core, Utils

### Tier 4: Utils Layer (`src/utils/`)
**Responsibility:** Shared utilities

**Components:**
- `i18n.py` - Internationalization
- `config_manager.py` - Configuration
- `data_manager.py` - Data persistence
- `logger.py` - Logging utilities

**Dependencies:** None (base layer)

## 🔄 Data Flow

```
User (Telegram)
     ↓
  Bot Layer (src/bot/)
     ↓
  Core Layer (src/core/)
     ↓
  Features Layer (src/features/)
     ↓
  Utils Layer (src/utils/)
     ↓
  Data Storage (data/)
```

## 🚀 Import Patterns

```python
# Bot layer
from src.core import SearchEngine, DealDetector
from src.features import RetentionSystem, ViralGrowth
from src.utils import ConfigManager, i18n

# Core layer
from src.utils import ConfigManager, DataManager

# Features layer
from src.core import SearchEngine
from src.utils import i18n

# Utils layer
# No internal dependencies
```

## 📊 Metrics & Monitoring

- Response time tracking
- Error rate monitoring
- User activity metrics
- System health checks
- Performance profiling

## 🔒 Security

- API key encryption
- Rate limiting
- Input validation
- SQL injection prevention
- XSS protection

## 🧪 Testing Strategy

- Unit tests per module
- Integration tests per layer
- End-to-end tests
- Performance tests
- Load tests

## 📝 Documentation Standards

- Docstrings for all functions
- Type hints everywhere
- README per directory
- API documentation
- User guides

## 🔄 Version Control

- Semantic versioning (X.Y.Z)
- Clear commit messages
- Feature branches
- Pull request reviews
- Automated CI/CD

---

**Version:** 16.0.0  
**Author:** @Juanka_Spain  
**Date:** 2026-01-17
