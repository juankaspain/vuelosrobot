#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
┌────────────────────────────────────────────────────────────────┐
│  🎉 INTERACTIVE ONBOARDING FLOW                           │
│  🚀 Cazador Supremo v13.0 Enterprise                          │
│  ⏱️ Target TTFV: <90 segundos                                   │
└────────────────────────────────────────────────────────────────┘

Onboarding flow optimizado para nuevos usuarios:
- 3-step interactive wizard
- Personalización inmediata
- First value en <90 segundos
- Completion tracking

Autor: @Juanka_Spain
Version: 13.0.0
Date: 2026-01-14
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  ENUMS & CONSTANTS
# ═══════════════════════════════════════════════════════════════

class OnboardingState(Enum):
    """Estados del onboarding"""
    NOT_STARTED = "not_started"
    STARTED = "started"
    STEP1_REGION = "step1_region"
    STEP2_BUDGET = "step2_budget"
    STEP3_FIRST_VALUE = "step3_first_value"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class TravelRegion(Enum):
    """Regiones de viaje"""
    EUROPE = "europe"
    USA = "usa"
    ASIA = "asia"
    LATAM = "latam"


class BudgetRange(Enum):
    """Rangos de presupuesto"""
    LOW = "low"        # <€300
    MEDIUM = "medium"  # €300-600
    HIGH = "high"      # >€600


# Configuración por región
REGION_ROUTES = {
    TravelRegion.EUROPE: [
        ('MAD', 'BCN', 'Madrid-Barcelona'),
        ('MAD', 'LHR', 'Madrid-Londres'),
        ('MAD', 'CDG', 'Madrid-París'),
        ('MAD', 'FCO', 'Madrid-Roma'),
        ('BCN', 'AMS', 'Barcelona-Amsterdam'),
    ],
    TravelRegion.USA: [
        ('MAD', 'JFK', 'Madrid-Nueva York'),
        ('MAD', 'MIA', 'Madrid-Miami'),
        ('MAD', 'LAX', 'Madrid-Los Angeles'),
        ('BCN', 'JFK', 'Barcelona-Nueva York'),
    ],
    TravelRegion.ASIA: [
        ('MAD', 'NRT', 'Madrid-Tokio'),
        ('MAD', 'BKK', 'Madrid-Bangkok'),
        ('MAD', 'SIN', 'Madrid-Singapur'),
        ('BCN', 'DXB', 'Barcelona-Dubai'),
    ],
    TravelRegion.LATAM: [
        ('MAD', 'BOG', 'Madrid-Bogotá'),
        ('MAD', 'MEX', 'Madrid-México'),
        ('MAD', 'LIM', 'Madrid-Lima'),
        ('MAD', 'GUA', 'Madrid-Guatemala'),
        ('MAD', 'SCL', 'Madrid-Santiago'),
    ]
}

# Thresholds por presupuesto
BUDGET_THRESHOLDS = {
    BudgetRange.LOW: {
        'europe': 200,
        'usa': 400,
        'asia': 500,
        'latam': 450
    },
    BudgetRange.MEDIUM: {
        'europe': 350,
        'usa': 550,
        'asia': 700,
        'latam': 600
    },
    BudgetRange.HIGH: {
        'europe': 500,
        'usa': 800,
        'asia': 1000,
        'latam': 850
    }
}

# Bonus por completar onboarding
ONBOARDING_COMPLETION_BONUS = 200


# ═══════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class OnboardingProgress:
    """Progreso del onboarding por usuario"""
    user_id: int
    state: OnboardingState
    started_at: str
    completed_at: Optional[str] = None
    
    # Preferencias capturadas
    travel_region: Optional[TravelRegion] = None
    budget_range: Optional[BudgetRange] = None
    
    # Tracking
    step1_timestamp: Optional[str] = None
    step2_timestamp: Optional[str] = None
    step3_timestamp: Optional[str] = None
    
    # Analytics
    total_time_seconds: Optional[int] = None
    
    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'state': self.state.value,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'travel_region': self.travel_region.value if self.travel_region else None,
            'budget_range': self.budget_range.value if self.budget_range else None,
            'step1_timestamp': self.step1_timestamp,
            'step2_timestamp': self.step2_timestamp,
            'step3_timestamp': self.step3_timestamp,
            'total_time_seconds': self.total_time_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'OnboardingProgress':
        return cls(
            user_id=data['user_id'],
            state=OnboardingState(data['state']),
            started_at=data['started_at'],
            completed_at=data.get('completed_at'),
            travel_region=TravelRegion(data['travel_region']) if data.get('travel_region') else None,
            budget_range=BudgetRange(data['budget_range']) if data.get('budget_range') else None,
            step1_timestamp=data.get('step1_timestamp'),
            step2_timestamp=data.get('step2_timestamp'),
            step3_timestamp=data.get('step3_timestamp'),
            total_time_seconds=data.get('total_time_seconds')
        )


# ═══════════════════════════════════════════════════════════════
#  ONBOARDING MANAGER
# ═══════════════════════════════════════════════════════════════

class OnboardingManager:
    """
    Gestor del flujo de onboarding.
    
    Responsabilidades:
    - Tracking de progreso
    - State machine
    - Persistencia
    - Analytics
    """
    
    def __init__(self, data_file: str = 'onboarding_progress.json'):
        self.data_file = Path(data_file)
        self.progress: Dict[int, OnboardingProgress] = {}
        self._load_data()
        
        logger.info("🎉 OnboardingManager initialized")
    
    def _load_data(self):
        """Carga datos desde archivo."""
        if not self.data_file.exists():
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for user_id_str, progress_data in data.items():
                user_id = int(user_id_str)
                self.progress[user_id] = OnboardingProgress.from_dict(progress_data)
            
            logger.info(f"✅ Loaded {len(self.progress)} onboarding records")
        except Exception as e:
            logger.error(f"❌ Error loading onboarding data: {e}")
    
    def _save_data(self):
        """Guarda datos a archivo."""
        try:
            data = {
                str(user_id): progress.to_dict()
                for user_id, progress in self.progress.items()
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("💾 Onboarding data saved")
        except Exception as e:
            logger.error(f"❌ Error saving onboarding data: {e}")
    
    def needs_onboarding(self, user_id: int) -> bool:
        """Verifica si el usuario necesita onboarding."""
        if user_id not in self.progress:
            return True
        
        state = self.progress[user_id].state
        return state not in [OnboardingState.COMPLETED, OnboardingState.SKIPPED]
    
    def start_onboarding(self, user_id: int) -> OnboardingProgress:
        """Inicia el onboarding para un usuario."""
        progress = OnboardingProgress(
            user_id=user_id,
            state=OnboardingState.STARTED,
            started_at=datetime.now().isoformat()
        )
        
        self.progress[user_id] = progress
        self._save_data()
        
        logger.info(f"🎉 Started onboarding for user {user_id}")
        return progress
    
    def advance_to_step1(self, user_id: int) -> OnboardingProgress:
        """Avanza al Step 1 (region selection)."""
        if user_id not in self.progress:
            self.start_onboarding(user_id)
        
        progress = self.progress[user_id]
        progress.state = OnboardingState.STEP1_REGION
        progress.step1_timestamp = datetime.now().isoformat()
        
        self._save_data()
        return progress
    
    def set_travel_region(self, user_id: int, region: TravelRegion) -> OnboardingProgress:
        """Guarda región de viaje y avanza a Step 2."""
        progress = self.progress[user_id]
        progress.travel_region = region
        progress.state = OnboardingState.STEP2_BUDGET
        progress.step2_timestamp = datetime.now().isoformat()
        
        self._save_data()
        
        logger.info(f"🌍 User {user_id} selected region: {region.value}")
        return progress
    
    def set_budget_range(self, user_id: int, budget: BudgetRange) -> OnboardingProgress:
        """Guarda presupuesto y avanza a Step 3."""
        progress = self.progress[user_id]
        progress.budget_range = budget
        progress.state = OnboardingState.STEP3_FIRST_VALUE
        progress.step3_timestamp = datetime.now().isoformat()
        
        self._save_data()
        
        logger.info(f"💰 User {user_id} selected budget: {budget.value}")
        return progress
    
    def complete_onboarding(self, user_id: int) -> OnboardingProgress:
        """Marca onboarding como completado."""
        progress = self.progress[user_id]
        progress.state = OnboardingState.COMPLETED
        progress.completed_at = datetime.now().isoformat()
        
        # Calcular tiempo total
        started = datetime.fromisoformat(progress.started_at)
        completed = datetime.fromisoformat(progress.completed_at)
        progress.total_time_seconds = int((completed - started).total_seconds())
        
        self._save_data()
        
        logger.info(
            f"✅ User {user_id} completed onboarding in {progress.total_time_seconds}s"
        )
        return progress
    
    def skip_onboarding(self, user_id: int):
        """Marca onboarding como skipped."""
        if user_id not in self.progress:
            self.start_onboarding(user_id)
        
        progress = self.progress[user_id]
        progress.state = OnboardingState.SKIPPED
        progress.completed_at = datetime.now().isoformat()
        
        self._save_data()
        
        logger.info(f"⏭️ User {user_id} skipped onboarding")
    
    def get_progress(self, user_id: int) -> Optional[OnboardingProgress]:
        """Obtiene progreso del usuario."""
        return self.progress.get(user_id)
    
    def get_recommended_routes(self, user_id: int) -> List[tuple]:
        """Obtiene rutas recomendadas basadas en preferencias."""
        progress = self.progress.get(user_id)
        
        if not progress or not progress.travel_region:
            # Default: rutas europeas
            return REGION_ROUTES[TravelRegion.EUROPE][:3]
        
        return REGION_ROUTES[progress.travel_region][:3]
    
    def get_watchlist_threshold(self, user_id: int, route_region: str) -> float:
        """Calcula threshold para watchlist basado en presupuesto."""
        progress = self.progress.get(user_id)
        
        if not progress or not progress.budget_range:
            # Default: medium
            return BUDGET_THRESHOLDS[BudgetRange.MEDIUM].get(route_region, 500)
        
        return BUDGET_THRESHOLDS[progress.budget_range].get(route_region, 500)
    
    def get_analytics(self) -> Dict:
        """Obtiene analytics del onboarding."""
        total_users = len(self.progress)
        completed = sum(1 for p in self.progress.values() 
                       if p.state == OnboardingState.COMPLETED)
        skipped = sum(1 for p in self.progress.values() 
                     if p.state == OnboardingState.SKIPPED)
        in_progress = total_users - completed - skipped
        
        # Avg completion time
        completion_times = [p.total_time_seconds for p in self.progress.values() 
                           if p.total_time_seconds]
        avg_time = sum(completion_times) / len(completion_times) if completion_times else 0
        
        return {
            'total_users': total_users,
            'completed': completed,
            'skipped': skipped,
            'in_progress': in_progress,
            'completion_rate': completed / total_users if total_users > 0 else 0,
            'avg_completion_time_seconds': int(avg_time),
            'under_90s': sum(1 for t in completion_times if t < 90)
        }


# ═══════════════════════════════════════════════════════════════
#  MESSAGE TEMPLATES
# ═══════════════════════════════════════════════════════════════

class OnboardingMessages:
    """Templates para mensajes de onboarding."""
    
    @staticmethod
    def welcome(username: str) -> str:
        """Mensaje de bienvenida inicial."""
        return (
            f"🎉 *¡Bienvenido a Cazador Supremo, @{username}!* 🎉\n\n"
            f"✈️ Soy tu asistente personal para encontrar los *mejores precios de vuelos*\n\n"
            f"💰 Te ayudaré a ahorrar hasta un *30% en cada vuelo*\n"
            f"🔔 Recibirás alertas instantáneas cuando los precios bajen\n"
            f"🎮 Gana FlightCoins y desbloquea funciones premium\n\n"
            f"🚀 *¡Empecemos!* Solo 3 preguntas rápidas...\n\n"
            f"_Configuración: <60 segundos_"
        )
    
    @staticmethod
    def step1_region() -> str:
        """Step 1: Selección de región."""
        return (
            f"🌍 *Paso 1/3: ¿Dónde viajas normalmente?*\n\n"
            f"Selecciona tu región favorita para personalizar tus búsquedas:\n\n"
            f"🇪🇺 *Europa* - Vuelos dentro de Europa\n"
            f"🇺🇸 *USA* - Vuelos a Estados Unidos\n"
            f"🌏 *Asia* - Vuelos a Asia y Oceanía\n"
            f"🌎 *Latam* - Vuelos a Latinoamérica\n\n"
            f"_⏱️ 30 segundos restantes_"
        )
    
    @staticmethod
    def step2_budget() -> str:
        """Step 2: Selección de presupuesto."""
        return (
            f"💰 *Paso 2/3: ¿Cuál es tu presupuesto típico?*\n\n"
            f"Esto me ayudará a encontrar deals perfectos para ti:\n\n"
            f"🟢 *Económico* - Hasta €300\n"
            f"🟡 *Moderado* - €300-600\n"
            f"🔵 *Premium* - Más de €600\n\n"
            f"_⏱️ 20 segundos restantes_"
        )
    
    @staticmethod
    def step3_first_value(deals_count: int) -> str:
        """Step 3: Primer valor - mostrando deals."""
        return (
            f"🎉 *¡Perfecto! Buscando tus primeros deals...*\n\n"
            f"🔍 Encontré {deals_count} vuelos para ti\n"
            f"📍 Los he añadido a tu watchlist automáticamente\n"
            f"🔔 Recibirás alertas cuando bajen de precio\n\n"
            f"_Cargando resultados..._"
        )
    
    @staticmethod
    def completion(coins_earned: int, ttfv_seconds: int) -> str:
        """Mensaje de completación."""
        return (
            f"✅ *¡Configuración completada!*\n\n"
            f"🎁 *+{coins_earned} FlightCoins* de bienvenida\n"
            f"⏱️ Completado en {ttfv_seconds} segundos\n\n"
            f"🚀 *Próximos pasos:*\n"
            f"• `/daily` - Reclama tu reward diario\n"
            f"• `/watchlist` - Gestiona tus alertas\n"
            f"• `/profile` - Ver tu perfil\n"
            f"• `/deals` - Buscar más chollos\n\n"
            f"_¡Disfruta ahorrando en tus vuelos!_ ✈️"
        )


if __name__ == '__main__':
    # 🧪 Tests rápidos
    print("🧪 Testing OnboardingManager...\n")
    
    mgr = OnboardingManager('test_onboarding.json')
    
    # Test 1: Start onboarding
    print("1. Starting onboarding...")
    progress = mgr.start_onboarding(12345)
    print(f"   State: {progress.state.value}\n")
    
    # Test 2: Advance to step 1
    print("2. Advancing to step 1...")
    mgr.advance_to_step1(12345)
    print(f"   State: {mgr.get_progress(12345).state.value}\n")
    
    # Test 3: Set region
    print("3. Setting travel region...")
    mgr.set_travel_region(12345, TravelRegion.EUROPE)
    print(f"   Region: {mgr.get_progress(12345).travel_region.value}\n")
    
    # Test 4: Set budget
    print("4. Setting budget...")
    mgr.set_budget_range(12345, BudgetRange.MEDIUM)
    print(f"   Budget: {mgr.get_progress(12345).budget_range.value}\n")
    
    # Test 5: Complete
    print("5. Completing onboarding...")
    mgr.complete_onboarding(12345)
    final = mgr.get_progress(12345)
    print(f"   State: {final.state.value}")
    print(f"   Time: {final.total_time_seconds}s\n")
    
    # Test 6: Analytics
    print("6. Getting analytics...")
    analytics = mgr.get_analytics()
    print(f"   Completion rate: {analytics['completion_rate']:.1%}")
    print(f"   Avg time: {analytics['avg_completion_time_seconds']}s\n")
    
    print("✅ All tests completed!")
