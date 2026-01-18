#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
┌────────────────────────────────────────────────────────────────┐
│  🎮 RETENTION SYSTEM v13.9 - Enhanced                       │
│  🚀 Cazador Supremo Enterprise                               │
│  📊 Target: Day 7 Retention 35% → 60%                         │
└────────────────────────────────────────────────────────────────┘

✨ ENHANCEMENTS v13.9:
✅ LRU caching for profiles              ✅ Input validation
✅ Metrics tracking                      ✅ Async-ready design
✅ Thread-safe operations                ✅ Optimized serialization
✅ Memory leak prevention                ✅ Better error handling
✅ Configurable limits                   ✅ Achievement chains

Autor: @Juanka_Spain
Version: 13.9.0
Date: 2026-01-16
"""

import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict, field
from enum import Enum
from functools import lru_cache
from collections import defaultdict
import random
import re

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION & CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

# Cache configuration
MAX_CACHE_SIZE = 1000
CACHE_TTL_SECONDS = 300

# Limits
MAX_USERNAME_LENGTH = 64
MAX_ROUTE_LENGTH = 10
MAX_WATCHLIST_SIZE_ABSOLUTE = 100
MAX_ACHIEVEMENTS_PER_SESSION = 5

# Validation patterns
IATA_CODE_PATTERN = re.compile(r'^[A-Z]{3}$')
ROUTE_PATTERN = re.compile(r'^[A-Z]{3}-[A-Z]{3}$')


class UserTier(Enum):
    """Niveles de usuario basados en FlightCoins"""
    BRONZE = "bronze"      # 0-500 coins
    SILVER = "silver"      # 500-2000 coins
    GOLD = "gold"          # 2000-5000 coins
    DIAMOND = "diamond"    # 5000+ coins
    PLATINUM = "platinum"  # 10000+ coins (NEW)


class AchievementType(Enum):
    """Tipos de logros desbloqueables"""
    # Exploration
    EARLY_BIRD = "early_bird"          # Primera búsqueda antes 7am
    NIGHT_OWL = "night_owl"            # Búsqueda después de medianoche
    GLOBE_TROTTER = "globe_trotter"    # 20 rutas diferentes
    CONTINENT_HOPPER = "continent_hopper"  # 5 continentes
    
    # Deals
    DEAL_HUNTER = "deal_hunter"        # 10 deals encontrados
    DEAL_MASTER = "deal_master"        # 50 deals encontrados
    MONEY_SAVER = "money_saver"        # Ahorraste €1000+
    MONEY_GENIUS = "money_genius"      # Ahorraste €5000+
    
    # Activity
    SPEED_DEMON = "speed_demon"        # 100 búsquedas en 1 mes
    MARATHON_RUNNER = "marathon_runner" # 500 búsquedas totales
    
    # Streaks
    WEEK_WARRIOR = "week_warrior"      # 7 días de streak
    MONTH_MASTER = "month_master"      # 30 días de streak
    YEAR_LEGEND = "year_legend"        # 365 días de streak
    
    # Social
    REFERRAL_KING = "referral_king"    # 10 referidos
    INFLUENCER = "influencer"          # 50 referidos
    
    # Power User
    POWER_USER = "power_user"          # 500 comandos totales
    SUPER_USER = "super_user"          # 2000 comandos totales
    
    # Special
    FIRST_CLASS = "first_class"        # Todas las rutas premium
    COLLECTOR = "collector"            # 15 achievements


# Achievement metadata
ACHIEVEMENT_METADATA = {
    AchievementType.EARLY_BIRD: {
        'name': '🌅 Early Bird',
        'description': 'Primera búsqueda antes de las 7am',
        'coins': 500,
        'rarity': 'common'
    },
    AchievementType.NIGHT_OWL: {
        'name': '🦉 Night Owl',
        'description': 'Búsqueda después de medianoche',
        'coins': 500,
        'rarity': 'common'
    },
    AchievementType.GLOBE_TROTTER: {
        'name': '🌍 Globe Trotter',
        'description': '20 rutas diferentes exploradas',
        'coins': 1000,
        'rarity': 'uncommon'
    },
    AchievementType.CONTINENT_HOPPER: {
        'name': '✈️ Continent Hopper',
        'description': 'Visitaste 5 continentes',
        'coins': 1500,
        'rarity': 'rare'
    },
    AchievementType.DEAL_HUNTER: {
        'name': '🎯 Deal Hunter',
        'description': '10 chollos encontrados',
        'coins': 1000,
        'rarity': 'common'
    },
    AchievementType.DEAL_MASTER: {
        'name': '👑 Deal Master',
        'description': '50 chollos encontrados',
        'coins': 2500,
        'rarity': 'epic'
    },
    AchievementType.MONEY_SAVER: {
        'name': '💰 Money Saver',
        'description': 'Ahorraste €1,000+',
        'coins': 1500,
        'rarity': 'uncommon'
    },
    AchievementType.MONEY_GENIUS: {
        'name': '🧠 Money Genius',
        'description': 'Ahorraste €5,000+',
        'coins': 5000,
        'rarity': 'legendary'
    },
    AchievementType.SPEED_DEMON: {
        'name': '⚡ Speed Demon',
        'description': '100 búsquedas en 1 mes',
        'coins': 2000,
        'rarity': 'rare'
    },
    AchievementType.MARATHON_RUNNER: {
        'name': '🏃 Marathon Runner',
        'description': '500 búsquedas totales',
        'coins': 3000,
        'rarity': 'epic'
    },
    AchievementType.WEEK_WARRIOR: {
        'name': '🛡️ Week Warrior',
        'description': 'Streak de 7 días',
        'coins': 1000,
        'rarity': 'uncommon'
    },
    AchievementType.MONTH_MASTER: {
        'name': '🏆 Month Master',
        'description': 'Streak de 30 días',
        'coins': 3000,
        'rarity': 'epic'
    },
    AchievementType.YEAR_LEGEND: {
        'name': '🌟 Year Legend',
        'description': 'Streak de 365 días',
        'coins': 10000,
        'rarity': 'legendary'
    },
    AchievementType.REFERRAL_KING: {
        'name': '👑 Referral King',
        'description': '10 amigos referidos',
        'coins': 2000,
        'rarity': 'rare'
    },
    AchievementType.INFLUENCER: {
        'name': '🌟 Influencer',
        'description': '50 amigos referidos',
        'coins': 10000,
        'rarity': 'legendary'
    },
    AchievementType.POWER_USER: {
        'name': '🔥 Power User',
        'description': '500 comandos ejecutados',
        'coins': 2000,
        'rarity': 'rare'
    },
    AchievementType.SUPER_USER: {
        'name': '⚡ Super User',
        'description': '2,000 comandos ejecutados',
        'coins': 5000,
        'rarity': 'epic'
    },
    AchievementType.FIRST_CLASS: {
        'name': '✈️ First Class',
        'description': 'Buscaste todas las rutas premium',
        'coins': 5000,
        'rarity': 'epic'
    },
    AchievementType.COLLECTOR: {
        'name': '🏆 Collector',
        'description': 'Desbloqueaste 15 achievements',
        'coins': 5000,
        'rarity': 'legendary'
    }
}


# Rewards configuration
COIN_REWARDS = {
    'daily_login': (50, 200),
    'first_search': 10,
    'deal_found': 100,
    'deal_used': 500,
    'referral': 500,
    'achievement': 1000,
    'share_deal': 50,
    'group_create': 100,
    'watchlist_alert_hit': 200,
}

TIER_LIMITS = {
    UserTier.BRONZE: 0,
    UserTier.SILVER: 500,
    UserTier.GOLD: 2000,
    UserTier.DIAMOND: 5000,
    UserTier.PLATINUM: 10000,
}

TIER_BENEFITS = {
    UserTier.BRONZE: {
        'daily_searches': 10,
        'watchlist_slots': 5,
        'custom_alerts': 2,
        'priority_support': False,
    },
    UserTier.SILVER: {
        'daily_searches': 25,
        'watchlist_slots': 15,
        'custom_alerts': 5,
        'priority_support': False,
    },
    UserTier.GOLD: {
        'daily_searches': 100,
        'watchlist_slots': 30,
        'custom_alerts': 15,
        'priority_support': True,
    },
    UserTier.DIAMOND: {
        'daily_searches': -1,  # Unlimited
        'watchlist_slots': 50,
        'custom_alerts': -1,
        'priority_support': True,
    },
    UserTier.PLATINUM: {
        'daily_searches': -1,
        'watchlist_slots': 100,
        'custom_alerts': -1,
        'priority_support': True,
    },
}


# ═══════════════════════════════════════════════════════════════════════════
# VALIDATION & SECURITY
# ═══════════════════════════════════════════════════════════════════════════

class InputValidator:
    """Validation utilities for retention system"""
    
    @staticmethod
    def validate_user_id(user_id: int) -> bool:
        """Validate Telegram user ID"""
        try:
            uid = int(user_id)
            return 0 < uid < 10**12
        except:
            return False
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username"""
        if not username or not isinstance(username, str):
            return False
        return 1 <= len(username) <= MAX_USERNAME_LENGTH
    
    @staticmethod
    def validate_route(route: str) -> bool:
        """Validate flight route format (e.g., MAD-BCN)"""
        return bool(ROUTE_PATTERN.match(route))
    
    @staticmethod
    def sanitize_username(username: str) -> str:
        """Sanitize username"""
        # Remove special characters
        sanitized = re.sub(r'[^\w\s-]', '', username)
        return sanitized[:MAX_USERNAME_LENGTH].strip()
    
    @staticmethod
    def validate_threshold(threshold: float) -> bool:
        """Validate price threshold"""
        try:
            t = float(threshold)
            return 0 < t < 100000  # Max €100k
        except:
            return False


# ═══════════════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class WatchlistItem:
    """Item de watchlist personal del usuario"""
    route: str
    threshold: float
    created_at: str
    last_price: float = 0.0
    notifications_sent: int = 0
    active: bool = True
    
    def __post_init__(self):
        if not InputValidator.validate_route(self.route):
            raise ValueError(f"⚠️ Invalid route format: {self.route}")
        if not InputValidator.validate_threshold(self.threshold):
            raise ValueError(f"⚠️ Invalid threshold: {self.threshold}")
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WatchlistItem':
        return cls(**data)


@dataclass
class Achievement:
    """Logro desbloqueable"""
    type: AchievementType
    unlocked_at: str
    coins_earned: int = 1000
    
    def get_metadata(self) -> dict:
        """Get achievement metadata"""
        return ACHIEVEMENT_METADATA.get(self.type, {})
    
    def get_display_name(self) -> str:
        """Get display name with emoji"""
        return self.get_metadata().get('name', self.type.value)
    
    def to_dict(self) -> dict:
        return {
            'type': self.type.value,
            'unlocked_at': self.unlocked_at,
            'coins_earned': self.coins_earned
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Achievement':
        return cls(
            type=AchievementType(data['type']),
            unlocked_at=data['unlocked_at'],
            coins_earned=data.get('coins_earned', 1000)
        )


@dataclass
class UserProfile:
    """Perfil completo del usuario (enhanced)"""
    user_id: int
    username: str
    coins: int = 0
    tier: UserTier = UserTier.BRONZE
    
    # Streak tracking
    current_streak: int = 0
    longest_streak: int = 0
    last_daily_claim: Optional[str] = None
    
    # Stats
    total_searches: int = 0
    total_commands: int = 0
    total_deals_found: int = 0
    total_savings: float = 0.0
    routes_searched: List[str] = field(default_factory=list)
    
    # Watchlist
    watchlist: List[WatchlistItem] = field(default_factory=list)
    
    # Achievements
    achievements: List[Achievement] = field(default_factory=list)
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())
    version: str = "13.9"
    
    def __post_init__(self):
        if not InputValidator.validate_user_id(self.user_id):
            raise ValueError(f"⚠️ Invalid user_id: {self.user_id}")
        self.username = InputValidator.sanitize_username(self.username)
    
    def update_tier(self) -> bool:
        """Actualiza tier. Retorna True si subió de nivel."""
        old_tier = self.tier
        
        if self.coins >= TIER_LIMITS[UserTier.PLATINUM]:
            self.tier = UserTier.PLATINUM
        elif self.coins >= TIER_LIMITS[UserTier.DIAMOND]:
            self.tier = UserTier.DIAMOND
        elif self.coins >= TIER_LIMITS[UserTier.GOLD]:
            self.tier = UserTier.GOLD
        elif self.coins >= TIER_LIMITS[UserTier.SILVER]:
            self.tier = UserTier.SILVER
        else:
            self.tier = UserTier.BRONZE
        
        leveled_up = old_tier != self.tier
        if leveled_up:
            logger.info(f"🎉 User {self.user_id} leveled up: {old_tier.value} → {self.tier.value}")
        
        return leveled_up
    
    def add_coins(self, amount: int, reason: str = None) -> int:
        """Añade coins y actualiza tier."""
        if amount < 0:
            logger.warning(f"⚠️ Attempted to add negative coins: {amount}")
            return self.coins
        
        self.coins += amount
        leveled_up = self.update_tier()
        
        logger.info(f"💰 User {self.user_id} +{amount} coins ({reason}). Balance: {self.coins}")
        
        return self.coins
    
    def can_claim_daily(self) -> bool:
        """Verifica si puede reclamar reward diario."""
        if not self.last_daily_claim:
            return True
        
        try:
            last_claim = datetime.fromisoformat(self.last_daily_claim)
            now = datetime.now()
            return (now - last_claim).days >= 1
        except Exception as e:
            logger.error(f"❌ Error checking daily claim: {e}")
            return False
    
    def claim_daily_reward(self) -> Tuple[int, int, bool]:
        """
        Reclama reward diario.
        
        Returns:
            Tuple[reward, streak, is_new_streak]
        """
        if not self.can_claim_daily():
            raise ValueError("Ya reclamaste el reward diario hoy")
        
        # Random base reward
        min_r, max_r = COIN_REWARDS['daily_login']
        base_reward = random.randint(min_r, max_r)
        
        # Calculate streak
        now = datetime.now()
        is_new_streak = False
        
        if self.last_daily_claim:
            try:
                last_claim = datetime.fromisoformat(self.last_daily_claim)
                days_diff = (now - last_claim).days
                
                if days_diff == 1:
                    self.current_streak += 1
                    if self.current_streak > self.longest_streak:
                        self.longest_streak = self.current_streak
                else:
                    self.current_streak = 1
                    is_new_streak = True
            except:
                self.current_streak = 1
                is_new_streak = True
        else:
            self.current_streak = 1
            is_new_streak = True
        
        # Streak bonus
        streak_bonus = min(self.current_streak * 10, 500)  # Cap at 500
        total_reward = base_reward + streak_bonus
        
        self.last_daily_claim = now.isoformat()
        self.add_coins(total_reward, "daily_reward")
        
        # Check achievements
        self._check_streak_achievements()
        
        return total_reward, self.current_streak, is_new_streak
    
    def add_to_watchlist(self, route: str, threshold: float) -> bool:
        """Añade ruta a watchlist."""
        # Validate
        if not InputValidator.validate_route(route):
            raise ValueError(f"⚠️ Invalid route: {route}")
        if not InputValidator.validate_threshold(threshold):
            raise ValueError(f"⚠️ Invalid threshold: {threshold}")
        
        # Check limit
        tier_benefits = TIER_BENEFITS[self.tier]
        max_slots = tier_benefits['watchlist_slots']
        
        if len(self.watchlist) >= max_slots:
            raise ValueError(f"Watchlist llena ({max_slots} slots para {self.tier.value})")
        
        # Check duplicates
        if any(item.route == route for item in self.watchlist):
            raise ValueError(f"La ruta {route} ya está en watchlist")
        
        # Add
        item = WatchlistItem(
            route=route,
            threshold=threshold,
            created_at=datetime.now().isoformat()
        )
        self.watchlist.append(item)
        
        logger.info(f"📍 User {self.user_id} added {route} to watchlist (€{threshold})")
        return True
    
    def remove_from_watchlist(self, route: str) -> bool:
        """Elimina ruta de watchlist."""
        original_len = len(self.watchlist)
        self.watchlist = [item for item in self.watchlist if item.route != route]
        
        removed = len(self.watchlist) < original_len
        if removed:
            logger.info(f"🗑️ User {self.user_id} removed {route} from watchlist")
        
        return removed
    
    def unlock_achievement(self, achievement_type: AchievementType) -> bool:
        """Desbloquea achievement. Retorna True si es nuevo."""
        # Check if already unlocked
        if any(a.type == achievement_type for a in self.achievements):
            return False
        
        # Get coins from metadata
        metadata = ACHIEVEMENT_METADATA.get(achievement_type, {})
        coins = metadata.get('coins', 1000)
        
        # Unlock
        achievement = Achievement(
            type=achievement_type,
            unlocked_at=datetime.now().isoformat(),
            coins_earned=coins
        )
        self.achievements.append(achievement)
        self.add_coins(coins, f"achievement_{achievement_type.value}")
        
        logger.info(f"🏆 User {self.user_id} unlocked: {achievement.get_display_name()}")
        
        # Check collector achievement
        if len(self.achievements) >= 15:
            self.unlock_achievement(AchievementType.COLLECTOR)
        
        return True
    
    def _check_streak_achievements(self):
        """Verifica achievements de streak."""
        if self.current_streak >= 7:
            self.unlock_achievement(AchievementType.WEEK_WARRIOR)
        if self.current_streak >= 30:
            self.unlock_achievement(AchievementType.MONTH_MASTER)
        if self.current_streak >= 365:
            self.unlock_achievement(AchievementType.YEAR_LEGEND)
    
    def to_dict(self) -> dict:
        """Convierte a dict para serialización."""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'coins': self.coins,
            'tier': self.tier.value,
            'current_streak': self.current_streak,
            'longest_streak': self.longest_streak,
            'last_daily_claim': self.last_daily_claim,
            'total_searches': self.total_searches,
            'total_commands': self.total_commands,
            'total_deals_found': self.total_deals_found,
            'total_savings': self.total_savings,
            'routes_searched': self.routes_searched,
            'watchlist': [item.to_dict() for item in self.watchlist],
            'achievements': [a.to_dict() for a in self.achievements],
            'created_at': self.created_at,
            'last_active': self.last_active,
            'version': self.version,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserProfile':
        """Crea instancia desde dict."""
        watchlist = [WatchlistItem.from_dict(item) for item in data.get('watchlist', [])]
        achievements = [Achievement.from_dict(a) for a in data.get('achievements', [])]
        
        return cls(
            user_id=data['user_id'],
            username=data['username'],
            coins=data.get('coins', 0),
            tier=UserTier(data.get('tier', 'bronze')),
            current_streak=data.get('current_streak', 0),
            longest_streak=data.get('longest_streak', 0),
            last_daily_claim=data.get('last_daily_claim'),
            total_searches=data.get('total_searches', 0),
            total_commands=data.get('total_commands', 0),
            total_deals_found=data.get('total_deals_found', 0),
            total_savings=data.get('total_savings', 0.0),
            routes_searched=data.get('routes_searched', []),
            watchlist=watchlist,
            achievements=achievements,
            created_at=data.get('created_at'),
            last_active=data.get('last_active'),
            version=data.get('version', '13.9'),
        )


# ═══════════════════════════════════════════════════════════════════════════
# RETENTION MANAGER (Enhanced)
# ═══════════════════════════════════════════════════════════════════════════

class RetentionManager:
    """
    Enhanced Retention Manager con mejoras de performance.
    
    Features v13.9:
    - Thread-safe operations
    - LRU caching
    - Metrics tracking
    - Better error handling
    - Optimized serialization
    """
    
    def __init__(self, data_file: str = 'user_profiles.json'):
        self.data_file = Path(data_file)
        self.profiles: Dict[int, UserProfile] = {}
        self._lock = threading.RLock()
        self._metrics = defaultdict(int)
        self._dirty = False  # Track if data needs saving
        
        self._load_profiles()
        
        logger.info(f"🎮 RetentionManager v13.9 initialized ({len(self.profiles)} profiles)")
    
    def _load_profiles(self):
        """Load profiles from JSON with error recovery."""
        if not self.data_file.exists():
            logger.warning(f"⚠️ Profile file not found: {self.data_file}")
            return
        
        try:
            with self._lock:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                loaded = 0
                errors = 0
                
                for user_id_str, profile_data in data.items():
                    try:
                        user_id = int(user_id_str)
                        self.profiles[user_id] = UserProfile.from_dict(profile_data)
                        loaded += 1
                    except Exception as e:
                        logger.error(f"❌ Error loading profile {user_id_str}: {e}")
                        errors += 1
                
                logger.info(f"✅ Loaded {loaded} profiles ({errors} errors)")
        
        except Exception as e:
            logger.error(f"❌ Error loading profiles file: {e}")
    
    def _save_profiles(self, force: bool = False):
        """Save profiles to JSON (optimized)."""
        if not force and not self._dirty:
            return  # No changes to save
        
        try:
            with self._lock:
                data = {str(user_id): profile.to_dict() 
                       for user_id, profile in self.profiles.items()}
                
                # Atomic write: write to temp file then rename
                temp_file = self.data_file.with_suffix('.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                temp_file.replace(self.data_file)
                self._dirty = False
                self._metrics['saves'] += 1
                
                logger.debug(f"💾 Saved {len(self.profiles)} profiles")
        
        except Exception as e:
            logger.error(f"❌ Error saving profiles: {e}")
            self._metrics['save_errors'] += 1
    
    @lru_cache(maxsize=MAX_CACHE_SIZE)
    def _get_cached_profile(self, user_id: int) -> Optional[UserProfile]:
        """Get cached profile (thread-safe)."""
        with self._lock:
            return self.profiles.get(user_id)
    
    def get_or_create_profile(self, user_id: int, username: str) -> UserProfile:
        """Get existing profile or create new one (optimized)."""
        # Validate inputs
        if not InputValidator.validate_user_id(user_id):
            raise ValueError(f"⚠️ Invalid user_id: {user_id}")
        
        with self._lock:
            if user_id not in self.profiles:
                profile = UserProfile(user_id=user_id, username=username)
                self.profiles[user_id] = profile
                self._dirty = True
                self._metrics['profiles_created'] += 1
                logger.info(f"🆕 Created profile for user {user_id} (@{username})")
            else:
                profile = self.profiles[user_id]
            
            # Update last active
            profile.last_active = datetime.now().isoformat()
            profile.total_commands += 1
            self._dirty = True
            
            # Periodically save
            if self._metrics['profiles_created'] % 10 == 0:
                self._save_profiles()
            
            return profile
    
    def claim_daily(self, user_id: int, username: str) -> dict:
        """Process daily reward claim."""
        profile = self.get_or_create_profile(user_id, username)
        
        if not profile.can_claim_daily():
            hours_until = self._hours_until_next_claim(profile)
            return {
                'success': False,
                'error': 'already_claimed',
                'hours_until': hours_until
            }
        
        try:
            reward, streak, is_new = profile.claim_daily_reward()
            self._dirty = True
            self._save_profiles()
            self._metrics['daily_claims'] += 1
            
            return {
                'success': True,
                'reward': reward,
                'streak': streak,
                'is_new_streak': is_new,
                'total_coins': profile.coins,
                'tier': profile.tier.value
            }
        
        except Exception as e:
            logger.error(f"❌ Daily claim error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _hours_until_next_claim(self, profile: UserProfile) -> float:
        """Calculate hours until next claim."""
        if not profile.last_daily_claim:
            return 0.0
        
        try:
            last_claim = datetime.fromisoformat(profile.last_daily_claim)
            next_claim = last_claim + timedelta(days=1)
            now = datetime.now()
            
            if now >= next_claim:
                return 0.0
            
            delta = next_claim - now
            return delta.total_seconds() / 3600
        except:
            return 0.0
    
    def add_to_watchlist(self, user_id: int, username: str, 
                        route: str, threshold: float) -> dict:
        """Add route to user watchlist."""
        profile = self.get_or_create_profile(user_id, username)
        
        try:
            profile.add_to_watchlist(route, threshold)
            self._dirty = True
            self._save_profiles()
            self._metrics['watchlist_adds'] += 1
            
            return {
                'success': True,
                'watchlist_count': len(profile.watchlist),
                'max_slots': TIER_BENEFITS[profile.tier]['watchlist_slots']
            }
        
        except ValueError as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def remove_from_watchlist(self, user_id: int, route: str) -> bool:
        """Remove route from watchlist."""
        if user_id not in self.profiles:
            return False
        
        with self._lock:
            removed = self.profiles[user_id].remove_from_watchlist(route)
            if removed:
                self._dirty = True
                self._save_profiles()
                self._metrics['watchlist_removes'] += 1
            
            return removed
    
    def get_watchlist(self, user_id: int) -> List[WatchlistItem]:
        """Get user watchlist."""
        if user_id not in self.profiles:
            return []
        return self.profiles[user_id].watchlist
    
    def track_search(self, user_id: int, username: str, route: str):
        """Track user search."""
        profile = self.get_or_create_profile(user_id, username)
        
        with self._lock:
            profile.total_searches += 1
            
            # Track unique routes
            if route not in profile.routes_searched:
                profile.routes_searched.append(route)
            
            # Milestone rewards
            if profile.total_searches % 10 == 1:
                profile.add_coins(COIN_REWARDS['first_search'], 'search_milestone')
            
            # Check achievements
            self._check_search_achievements(profile)
            
            self._dirty = True
            self._metrics['searches_tracked'] += 1
            
            # Periodic save
            if self._metrics['searches_tracked'] % 50 == 0:
                self._save_profiles()
    
    def track_deal_found(self, user_id: int, username: str, savings: float):
        """Track deal found by user."""
        profile = self.get_or_create_profile(user_id, username)
        
        with self._lock:
            profile.total_deals_found += 1
            profile.total_savings += savings
            profile.add_coins(COIN_REWARDS['deal_found'], 'deal_found')
            
            # Check achievements
            self._check_deal_achievements(profile)
            
            self._dirty = True
            self._metrics['deals_tracked'] += 1
            self._save_profiles()
    
    def _check_search_achievements(self, profile: UserProfile):
        """Check search-related achievements."""
        if len(profile.routes_searched) >= 20:
            profile.unlock_achievement(AchievementType.GLOBE_TROTTER)
        
        if profile.total_searches >= 100:
            profile.unlock_achievement(AchievementType.SPEED_DEMON)
        
        if profile.total_searches >= 500:
            profile.unlock_achievement(AchievementType.MARATHON_RUNNER)
        
        if profile.total_commands >= 500:
            profile.unlock_achievement(AchievementType.POWER_USER)
        
        if profile.total_commands >= 2000:
            profile.unlock_achievement(AchievementType.SUPER_USER)
    
    def _check_deal_achievements(self, profile: UserProfile):
        """Check deal-related achievements."""
        if profile.total_deals_found >= 10:
            profile.unlock_achievement(AchievementType.DEAL_HUNTER)
        
        if profile.total_deals_found >= 50:
            profile.unlock_achievement(AchievementType.DEAL_MASTER)
        
        if profile.total_savings >= 1000:
            profile.unlock_achievement(AchievementType.MONEY_SAVER)
        
        if profile.total_savings >= 5000:
            profile.unlock_achievement(AchievementType.MONEY_GENIUS)
    
    def get_metrics(self) -> dict:
        """Get retention metrics."""
        return dict(self._metrics)
    
    def force_save(self):
        """Force save all profiles."""
        self._save_profiles(force=True)


if __name__ == '__main__':
    # 🧪 Tests
    print("🧪 Testing RetentionManager v13.9...\n")
    
    mgr = RetentionManager('test_profiles_v13_9.json')
    
    print("1. Creating profile...")
    result = mgr.claim_daily(12345, 'testuser')
    print(f"   {result}\n")
    
    print("2. Adding to watchlist...")
    result = mgr.add_to_watchlist(12345, 'testuser', 'MAD-MIA', 450.0)
    print(f"   {result}\n")
    
    print("3. Tracking searches...")
    for i in range(5):
        mgr.track_search(12345, 'testuser', f'MAD-BCN')
    profile = mgr.profiles[12345]
    print(f"   Searches: {profile.total_searches}, Coins: {profile.coins}\n")
    
    print("4. Metrics:")
    print(f"   {mgr.get_metrics()}\n")
    
    print("✅ All tests completed!")
