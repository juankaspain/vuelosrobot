#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
┌────────────────────────────────────────────────────────────────┐
│  🎮 QUICK ACTIONS BAR - 1-Tap Access                    │
│  🚀 Cazador Supremo v13.0 Enterprise                          │
│  ⚡ Reduce Fricción 70%                                       │
└────────────────────────────────────────────────────────────────┘

Sistema de acciones rápidas con inline keyboard persistente:
- 1-tap access a funciones críticas
- Smart context adaptation
- Analytics tracking
- Customization support

Autor: @Juanka_Spain
Version: 13.0.0
Date: 2026-01-14
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  ACTION DEFINITIONS
# ═══════════════════════════════════════════════════════════════

@dataclass
class QuickAction:
    """Definición de una acción rápida"""
    id: str
    label: str
    emoji: str
    callback_data: str
    description: str
    min_tier: str = "bronze"  # bronze, silver, gold, diamond
    requires_onboarding: bool = False
    
    @property
    def button_text(self) -> str:
        return f"{self.emoji} {self.label}"


# Acciones disponibles
AVAILABLE_ACTIONS = {
    'scan': QuickAction(
        id='scan',
        label='Scan',
        emoji='🔍',
        callback_data='qa_scan',
        description='Escanear rutas configuradas',
        requires_onboarding=False
    ),
    'deals': QuickAction(
        id='deals',
        label='Deals',
        emoji='💰',
        callback_data='qa_deals',
        description='Ver chollos disponibles',
        requires_onboarding=False
    ),
    'watchlist': QuickAction(
        id='watchlist',
        label='Watchlist',
        emoji='⭐',
        callback_data='qa_watchlist',
        description='Gestionar watchlist',
        requires_onboarding=True
    ),
    'profile': QuickAction(
        id='profile',
        label='Profile',
        emoji='📊',
        callback_data='qa_profile',
        description='Ver perfil y stats',
        requires_onboarding=True
    ),
    'daily': QuickAction(
        id='daily',
        label='Daily',
        emoji='🔥',
        callback_data='qa_daily',
        description='Reclamar reward diario',
        requires_onboarding=True
    ),
    'shop': QuickAction(
        id='shop',
        label='Shop',
        emoji='🛍️',
        callback_data='qa_shop',
        description='Tienda de FlightCoins',
        min_tier='silver',
        requires_onboarding=True
    ),
    'trends': QuickAction(
        id='trends',
        label='Trends',
        emoji='📈',
        callback_data='qa_trends',
        description='Tendencias de precio',
        requires_onboarding=False
    ),
    'help': QuickAction(
        id='help',
        label='Help',
        emoji='❓',
        callback_data='qa_help',
        description='Ayuda y comandos',
        requires_onboarding=False
    ),
}

# Layouts predefinidos por tier
DEFAULT_LAYOUTS = {
    'bronze': ['scan', 'deals', 'daily', 'help'],
    'silver': ['scan', 'deals', 'watchlist', 'profile', 'daily', 'help'],
    'gold': ['scan', 'deals', 'watchlist', 'profile', 'daily', 'shop', 'trends', 'help'],
    'diamond': ['scan', 'deals', 'watchlist', 'profile', 'daily', 'shop', 'trends', 'help'],
}

# Layout para usuarios sin onboarding
NO_ONBOARDING_LAYOUT = ['scan', 'deals', 'help']


# ═══════════════════════════════════════════════════════════════
#  ANALYTICS
# ═══════════════════════════════════════════════════════════════

@dataclass
class ActionAnalytics:
    """Analytics de uso de quick actions"""
    action_id: str
    total_clicks: int = 0
    unique_users: set = field(default_factory=set)
    click_timestamps: List[str] = field(default_factory=list)
    
    def record_click(self, user_id: int):
        """Registra un click."""
        self.total_clicks += 1
        self.unique_users.add(user_id)
        self.click_timestamps.append(datetime.now().isoformat())
        
        # Mantener solo últimos 1000 timestamps
        if len(self.click_timestamps) > 1000:
            self.click_timestamps = self.click_timestamps[-1000:]
    
    def get_ctr(self, total_displays: int) -> float:
        """Calcula CTR (Click-Through Rate)."""
        return (self.total_clicks / total_displays * 100) if total_displays > 0 else 0
    
    def to_dict(self) -> Dict:
        return {
            'action_id': self.action_id,
            'total_clicks': self.total_clicks,
            'unique_users': list(self.unique_users),
            'click_timestamps': self.click_timestamps[-100:]  # Solo últimos 100
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ActionAnalytics':
        return cls(
            action_id=data['action_id'],
            total_clicks=data.get('total_clicks', 0),
            unique_users=set(data.get('unique_users', [])),
            click_timestamps=data.get('click_timestamps', [])
        )


# ═══════════════════════════════════════════════════════════════
#  QUICK ACTIONS MANAGER
# ═══════════════════════════════════════════════════════════════

class QuickActionsManager:
    """
    Gestor de Quick Actions Bar.
    
    Responsabilidades:
    - Generar keyboards personalizados
    - Smart context adaptation
    - Analytics tracking
    - Custom layouts
    """
    
    def __init__(self, 
                 analytics_file: str = 'quick_actions_analytics.json',
                 layouts_file: str = 'quick_actions_layouts.json'):
        self.analytics_file = Path(analytics_file)
        self.layouts_file = Path(layouts_file)
        
        # Analytics por acción
        self.analytics: Dict[str, ActionAnalytics] = {}
        
        # Layouts personalizados por usuario
        self.custom_layouts: Dict[int, List[str]] = {}
        
        # Display counter
        self.total_displays = 0
        
        self._load_data()
        
        logger.info("🎮 QuickActionsManager initialized")
    
    def _load_data(self):
        """Carga datos desde archivos."""
        # Load analytics
        if self.analytics_file.exists():
            try:
                with open(self.analytics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for action_id, analytics_data in data.get('analytics', {}).items():
                    self.analytics[action_id] = ActionAnalytics.from_dict(analytics_data)
                
                self.total_displays = data.get('total_displays', 0)
                
                logger.info(f"✅ Loaded analytics for {len(self.analytics)} actions")
            except Exception as e:
                logger.error(f"❌ Error loading analytics: {e}")
        
        # Load custom layouts
        if self.layouts_file.exists():
            try:
                with open(self.layouts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.custom_layouts = {
                    int(user_id): layout
                    for user_id, layout in data.items()
                }
                
                logger.info(f"✅ Loaded {len(self.custom_layouts)} custom layouts")
            except Exception as e:
                logger.error(f"❌ Error loading layouts: {e}")
    
    def _save_data(self):
        """Guarda datos a archivos."""
        try:
            # Save analytics
            analytics_data = {
                'analytics': {
                    action_id: analytics.to_dict()
                    for action_id, analytics in self.analytics.items()
                },
                'total_displays': self.total_displays
            }
            
            with open(self.analytics_file, 'w', encoding='utf-8') as f:
                json.dump(analytics_data, f, indent=2, ensure_ascii=False)
            
            # Save custom layouts
            with open(self.layouts_file, 'w', encoding='utf-8') as f:
                json.dump({
                    str(user_id): layout
                    for user_id, layout in self.custom_layouts.items()
                }, f, indent=2, ensure_ascii=False)
            
            logger.debug("💾 Quick actions data saved")
        except Exception as e:
            logger.error(f"❌ Error saving data: {e}")
    
    def get_keyboard(self, 
                     user_id: int,
                     user_tier: str = 'bronze',
                     onboarding_completed: bool = False,
                     can_claim_daily: bool = False) -> InlineKeyboardMarkup:
        """
        Genera keyboard personalizado para usuario.
        
        Args:
            user_id: ID del usuario
            user_tier: Tier del usuario (bronze/silver/gold/diamond)
            onboarding_completed: Si completó onboarding
            can_claim_daily: Si puede reclamar daily reward
        
        Returns:
            InlineKeyboardMarkup con botones personalizados
        """
        # Get layout
        if user_id in self.custom_layouts:
            layout = self.custom_layouts[user_id]
        elif not onboarding_completed:
            layout = NO_ONBOARDING_LAYOUT
        else:
            layout = DEFAULT_LAYOUTS.get(user_tier, DEFAULT_LAYOUTS['bronze'])
        
        # Filter actions based on context
        available_actions = []
        for action_id in layout:
            if action_id not in AVAILABLE_ACTIONS:
                continue
            
            action = AVAILABLE_ACTIONS[action_id]
            
            # Check tier requirement
            tier_levels = ['bronze', 'silver', 'gold', 'diamond']
            if tier_levels.index(user_tier) < tier_levels.index(action.min_tier):
                continue
            
            # Check onboarding requirement
            if action.requires_onboarding and not onboarding_completed:
                continue
            
            # Smart context: highlight daily if can claim
            if action_id == 'daily' and can_claim_daily:
                # Add visual indicator
                action = QuickAction(
                    id=action.id,
                    label=action.label,
                    emoji='🔥❗',  # Extra emphasis
                    callback_data=action.callback_data,
                    description=action.description
                )
            
            available_actions.append(action)
        
        # Create keyboard (2 columns)
        keyboard = []
        for i in range(0, len(available_actions), 2):
            row = [
                InlineKeyboardButton(
                    available_actions[i].button_text,
                    callback_data=available_actions[i].callback_data
                )
            ]
            
            if i + 1 < len(available_actions):
                row.append(
                    InlineKeyboardButton(
                        available_actions[i+1].button_text,
                        callback_data=available_actions[i+1].callback_data
                    )
                )
            
            keyboard.append(row)
        
        # Track display
        self.total_displays += 1
        self._save_data()
        
        return InlineKeyboardMarkup(keyboard)
    
    def track_click(self, user_id: int, action_id: str):
        """Registra click en acción."""
        if action_id not in self.analytics:
            self.analytics[action_id] = ActionAnalytics(action_id=action_id)
        
        self.analytics[action_id].record_click(user_id)
        self._save_data()
        
        logger.info(f"💆 User {user_id} clicked action: {action_id}")
    
    def set_custom_layout(self, user_id: int, action_ids: List[str]):
        """Configura layout personalizado para usuario."""
        # Validate action IDs
        valid_ids = [aid for aid in action_ids if aid in AVAILABLE_ACTIONS]
        
        self.custom_layouts[user_id] = valid_ids
        self._save_data()
        
        logger.info(f"⚙️ User {user_id} set custom layout: {valid_ids}")
    
    def get_analytics_report(self) -> Dict:
        """Genera reporte de analytics."""
        report = {
            'total_displays': self.total_displays,
            'actions': {}
        }
        
        for action_id, analytics in self.analytics.items():
            action = AVAILABLE_ACTIONS.get(action_id)
            if not action:
                continue
            
            report['actions'][action_id] = {
                'label': action.label,
                'emoji': action.emoji,
                'total_clicks': analytics.total_clicks,
                'unique_users': len(analytics.unique_users),
                'ctr': analytics.get_ctr(self.total_displays)
            }
        
        # Sort by clicks
        report['actions'] = dict(
            sorted(report['actions'].items(), 
                   key=lambda x: x[1]['total_clicks'], 
                   reverse=True)
        )
        
        return report
    
    def get_heatmap(self) -> Dict[str, int]:
        """Genera heatmap de uso."""
        return {
            action_id: analytics.total_clicks
            for action_id, analytics in self.analytics.items()
        }


if __name__ == '__main__':
    # 🧪 Tests rápidos
    print("🧪 Testing QuickActionsManager...\n")
    
    mgr = QuickActionsManager('test_qa_analytics.json', 'test_qa_layouts.json')
    
    # Test 1: Get keyboard for bronze user
    print("1. Generating keyboard for bronze user...")
    keyboard = mgr.get_keyboard(
        user_id=12345,
        user_tier='bronze',
        onboarding_completed=True,
        can_claim_daily=True
    )
    print(f"   Buttons: {len(keyboard.inline_keyboard)} rows\n")
    
    # Test 2: Track clicks
    print("2. Tracking clicks...")
    mgr.track_click(12345, 'scan')
    mgr.track_click(12345, 'deals')
    mgr.track_click(67890, 'scan')
    print("   Clicks tracked\n")
    
    # Test 3: Analytics report
    print("3. Generating analytics report...")
    report = mgr.get_analytics_report()
    print(f"   Total displays: {report['total_displays']}")
    for action_id, stats in list(report['actions'].items())[:3]:
        print(f"   {stats['emoji']} {stats['label']}: {stats['total_clicks']} clicks ({stats['ctr']:.1f}% CTR)")
    print()
    
    # Test 4: Custom layout
    print("4. Setting custom layout...")
    mgr.set_custom_layout(12345, ['daily', 'profile', 'scan', 'deals'])
    custom_kb = mgr.get_keyboard(12345, onboarding_completed=True)
    print(f"   Custom keyboard: {len(custom_kb.inline_keyboard)} rows\n")
    
    print("✅ All tests completed!")
