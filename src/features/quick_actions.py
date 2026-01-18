#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
┌────────────────────────────────────────────────────────────────┐
│  ⚡ QUICK ACTIONS BAR - 1-Tap Access                     │
│  🚀 Cazador Supremo v13.0 Enterprise                          │
│  🎯 Target: Reduce clicks 3→1                              │
└────────────────────────────────────────────────────────────────┘

Sistema de Quick Actions para acceso rápido a funciones críticas:
- Persistent inline keyboard
- 1-tap access
- Smart context adaptation
- Analytics tracking

Autor: @Juanka_Spain
Version: 13.0.0
Date: 2026-01-14
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  ENUMS & CONSTANTS
# ═══════════════════════════════════════════════════════════════

class QuickAction(Enum):
    """Acciones rápidas disponibles"""
    SCAN = "scan"
    DEALS = "deals"
    WATCHLIST = "watchlist"
    PROFILE = "profile"
    DAILY = "daily"
    SETTINGS = "settings"
    HELP = "help"


class KeyboardLayout(Enum):
    """Layouts de teclado"""
    COMPACT = "compact"      # 1 fila, 4 botones principales
    STANDARD = "standard"    # 2 filas, 6 botones
    EXTENDED = "extended"    # 3 filas, todos los botones


# Configuración de botones
BUTTON_CONFIG = {
    QuickAction.SCAN: {
        'emoji': '🔍',
        'text': 'Scan',
        'callback': 'qa_scan',
        'priority': 1
    },
    QuickAction.DEALS: {
        'emoji': '💰',
        'text': 'Deals',
        'callback': 'qa_deals',
        'priority': 2
    },
    QuickAction.WATCHLIST: {
        'emoji': '⭐',
        'text': 'Watchlist',
        'callback': 'qa_watchlist',
        'priority': 3
    },
    QuickAction.PROFILE: {
        'emoji': '📈',
        'text': 'Perfil',
        'callback': 'qa_profile',
        'priority': 4
    },
    QuickAction.DAILY: {
        'emoji': '🔥',
        'text': 'Daily',
        'callback': 'qa_daily',
        'priority': 5
    },
    QuickAction.SETTINGS: {
        'emoji': '⚙️',
        'text': 'Config',
        'callback': 'qa_settings',
        'priority': 6
    },
    QuickAction.HELP: {
        'emoji': '❓',
        'text': 'Ayuda',
        'callback': 'qa_help',
        'priority': 7
    }
}


# ═══════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class ButtonState:
    """Estado de un botón"""
    action: QuickAction
    enabled: bool = True
    badge: Optional[str] = None  # Ej: "3" para 3 items en watchlist
    highlight: bool = False       # Ej: daily reward disponible
    
    def get_text(self) -> str:
        """Genera texto del botón con badge."""
        config = BUTTON_CONFIG[self.action]
        text = f"{config['emoji']} {config['text']}"
        
        if self.badge:
            text += f" ({self.badge})"
        
        if self.highlight:
            text = f"🔥 {text}"
        
        return text


@dataclass
class QuickActionsAnalytics:
    """Analytics de Quick Actions"""
    user_id: int
    action_clicks: Dict[str, int] = field(default_factory=dict)
    total_clicks: int = 0
    last_action: Optional[str] = None
    last_action_timestamp: Optional[str] = None
    
    def track_click(self, action: QuickAction):
        """Registra click en acción."""
        action_str = action.value
        
        if action_str not in self.action_clicks:
            self.action_clicks[action_str] = 0
        
        self.action_clicks[action_str] += 1
        self.total_clicks += 1
        self.last_action = action_str
        self.last_action_timestamp = datetime.now().isoformat()
    
    def get_top_actions(self, limit: int = 3) -> List[tuple]:
        """Obtiene top acciones más usadas."""
        sorted_actions = sorted(
            self.action_clicks.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_actions[:limit]
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'QuickActionsAnalytics':
        return cls(**data)


# ═══════════════════════════════════════════════════════════════
#  QUICK ACTIONS MANAGER
# ═══════════════════════════════════════════════════════════════

class QuickActionsManager:
    """
    Gestor de Quick Actions Bar.
    
    Responsabilidades:
    - Generar keyboards dinámicos
    - Tracking de analytics
    - State management
    - Context adaptation
    """
    
    def __init__(self, 
                 analytics_file: str = 'quick_actions_analytics.json',
                 default_layout: KeyboardLayout = KeyboardLayout.STANDARD):
        self.analytics_file = Path(analytics_file)
        self.default_layout = default_layout
        self.analytics: Dict[int, QuickActionsAnalytics] = {}
        
        self._load_analytics()
        
        logger.info("⚡ QuickActionsManager initialized")
    
    def _load_analytics(self):
        """Carga analytics desde archivo."""
        if not self.analytics_file.exists():
            return
        
        try:
            with open(self.analytics_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for user_id_str, analytics_data in data.items():
                user_id = int(user_id_str)
                self.analytics[user_id] = QuickActionsAnalytics.from_dict(analytics_data)
            
            logger.info(f"✅ Loaded analytics for {len(self.analytics)} users")
        except Exception as e:
            logger.error(f"❌ Error loading analytics: {e}")
    
    def _save_analytics(self):
        """Guarda analytics a archivo."""
        try:
            data = {
                str(user_id): analytics.to_dict()
                for user_id, analytics in self.analytics.items()
            }
            
            with open(self.analytics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("💾 Quick actions analytics saved")
        except Exception as e:
            logger.error(f"❌ Error saving analytics: {e}")
    
    def track_action(self, user_id: int, action: QuickAction):
        """Registra uso de acción."""
        if user_id not in self.analytics:
            self.analytics[user_id] = QuickActionsAnalytics(user_id=user_id)
        
        self.analytics[user_id].track_click(action)
        self._save_analytics()
        
        logger.info(f"⚡ User {user_id} clicked {action.value}")
    
    def get_button_states(self, 
                         user_id: int,
                         retention_mgr=None,
                         onboarding_mgr=None) -> Dict[QuickAction, ButtonState]:
        """
        Genera estados de botones basados en contexto del usuario.
        
        Args:
            user_id: ID del usuario
            retention_mgr: RetentionManager instance (opcional)
            onboarding_mgr: OnboardingManager instance (opcional)
        
        Returns:
            Dict con estados de cada botón
        """
        states = {}
        
        for action in QuickAction:
            state = ButtonState(action=action)
            
            # SCAN - siempre habilitado
            if action == QuickAction.SCAN:
                state.enabled = True
            
            # DEALS - siempre habilitado
            elif action == QuickAction.DEALS:
                state.enabled = True
            
            # WATCHLIST - badge con número de items
            elif action == QuickAction.WATCHLIST:
                if retention_mgr:
                    watchlist = retention_mgr.get_watchlist(user_id)
                    if watchlist:
                        state.badge = str(len(watchlist))
            
            # PROFILE - siempre habilitado
            elif action == QuickAction.PROFILE:
                state.enabled = True
            
            # DAILY - highlight si puede reclamar
            elif action == QuickAction.DAILY:
                if retention_mgr:
                    profile = retention_mgr.get_or_create_profile(user_id, str(user_id))
                    if profile.can_claim_daily():
                        state.highlight = True
            
            # SETTINGS - siempre habilitado
            elif action == QuickAction.SETTINGS:
                state.enabled = True
            
            # HELP - siempre habilitado
            elif action == QuickAction.HELP:
                state.enabled = True
            
            states[action] = state
        
        return states
    
    def generate_keyboard(self,
                         user_id: int,
                         layout: Optional[KeyboardLayout] = None,
                         retention_mgr=None,
                         onboarding_mgr=None) -> InlineKeyboardMarkup:
        """
        Genera inline keyboard con Quick Actions.
        
        Args:
            user_id: ID del usuario
            layout: Layout a usar (None = default)
            retention_mgr: RetentionManager instance
            onboarding_mgr: OnboardingManager instance
        
        Returns:
            InlineKeyboardMarkup listo para usar
        """
        layout = layout or self.default_layout
        states = self.get_button_states(user_id, retention_mgr, onboarding_mgr)
        
        # Ordenar por prioridad
        sorted_actions = sorted(
            QuickAction,
            key=lambda a: BUTTON_CONFIG[a]['priority']
        )
        
        # Generar botones
        buttons = []
        for action in sorted_actions:
            state = states[action]
            
            if not state.enabled:
                continue
            
            config = BUTTON_CONFIG[action]
            buttons.append(
                InlineKeyboardButton(
                    text=state.get_text(),
                    callback_data=config['callback']
                )
            )
        
        # Organizar en filas según layout
        keyboard = []
        
        if layout == KeyboardLayout.COMPACT:
            # 1 fila, 4 botones principales
            keyboard.append(buttons[:4])
        
        elif layout == KeyboardLayout.STANDARD:
            # 2 filas, 3 botones cada una
            keyboard.append(buttons[:3])
            keyboard.append(buttons[3:6])
        
        elif layout == KeyboardLayout.EXTENDED:
            # 3 filas, distribuidos
            keyboard.append(buttons[:3])
            keyboard.append(buttons[3:5])
            keyboard.append(buttons[5:])
        
        return InlineKeyboardMarkup(keyboard)
    
    def get_user_analytics(self, user_id: int) -> Optional[QuickActionsAnalytics]:
        """Obtiene analytics del usuario."""
        return self.analytics.get(user_id)
    
    def get_global_analytics(self) -> Dict:
        """Obtiene analytics globales."""
        total_users = len(self.analytics)
        total_clicks = sum(a.total_clicks for a in self.analytics.values())
        
        # Agregar clicks por acción
        action_totals = {}
        for analytics in self.analytics.values():
            for action, clicks in analytics.action_clicks.items():
                if action not in action_totals:
                    action_totals[action] = 0
                action_totals[action] += clicks
        
        # Top acciones
        top_actions = sorted(
            action_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return {
            'total_users': total_users,
            'total_clicks': total_clicks,
            'avg_clicks_per_user': total_clicks / total_users if total_users > 0 else 0,
            'action_totals': action_totals,
            'top_actions': top_actions[:3]
        }


if __name__ == '__main__':
    # 🧪 Tests rápidos
    print("🧪 Testing QuickActionsManager...\n")
    
    mgr = QuickActionsManager('test_qa_analytics.json')
    
    # Test 1: Generate keyboard
    print("1. Generating keyboard...")
    keyboard = mgr.generate_keyboard(12345)
    print(f"   Rows: {len(keyboard.inline_keyboard)}")
    print(f"   Buttons: {sum(len(row) for row in keyboard.inline_keyboard)}\n")
    
    # Test 2: Track actions
    print("2. Tracking actions...")
    mgr.track_action(12345, QuickAction.SCAN)
    mgr.track_action(12345, QuickAction.DEALS)
    mgr.track_action(12345, QuickAction.SCAN)
    
    user_analytics = mgr.get_user_analytics(12345)
    print(f"   Total clicks: {user_analytics.total_clicks}")
    print(f"   Top action: {user_analytics.get_top_actions(1)[0]}\n")
    
    # Test 3: Global analytics
    print("3. Global analytics...")
    global_analytics = mgr.get_global_analytics()
    print(f"   Total users: {global_analytics['total_users']}")
    print(f"   Avg clicks/user: {global_analytics['avg_clicks_per_user']:.1f}\n")
    
    # Test 4: Different layouts
    print("4. Testing layouts...")
    for layout in KeyboardLayout:
        keyboard = mgr.generate_keyboard(12345, layout=layout)
        print(f"   {layout.value}: {len(keyboard.inline_keyboard)} rows")
    
    print("\n✅ All tests completed!")
