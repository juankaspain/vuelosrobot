#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
┌────────────────────────────────────────────────────────────────┐
│  🦠 VIRAL GROWTH SYSTEM - Two-Sided Referrals              │
│  🚀 Cazador Supremo v13.0 Enterprise                          │
│  🎯 Target: K > 1.0 (Self-sustaining growth)                 │
└────────────────────────────────────────────────────────────────┘

Sistema viral de crecimiento con referidos bidireccionales:
- Incentivos para ambas partes
- Lifetime commission 10%
- Referral tiers progresivos
- Social sharing optimizado
- Anti-fraud protection

Autor: @Juanka_Spain
Version: 13.0.0
Date: 2026-01-14
"""

import json
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  CONSTANTS & ENUMS
# ═══════════════════════════════════════════════════════════════

class ReferralTier(Enum):
    """Tiers de referidos"""
    STARTER = "starter"        # 1-5 refs
    BUILDER = "builder"        # 6-15 refs
    EXPERT = "expert"          # 16-50 refs
    AMBASSADOR = "ambassador"  # 50+ refs


class SharePlatform(Enum):
    """Plataformas de compartir"""
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    LINK = "link"  # Copy link


# Recompensas por tier
REFERRAL_REWARDS = {
    ReferralTier.STARTER: {
        'coins_per_ref': 500,
        'bonus': 0,
        'badge': None
    },
    ReferralTier.BUILDER: {
        'coins_per_ref': 750,
        'bonus': 2000,  # Bonus al alcanzar tier
        'badge': '🌟 Builder'
    },
    ReferralTier.EXPERT: {
        'coins_per_ref': 1000,
        'bonus': 5000,
        'badge': '💎 Expert Recruiter'
    },
    ReferralTier.AMBASSADOR: {
        'coins_per_ref': 1500,
        'bonus': 10000,
        'badge': '👑 Brand Ambassador'
    }
}

# Recompensas base
REFERRER_BASE_COINS = 500
REFEREE_WELCOME_COINS = 300
LIFETIME_COMMISSION_PCT = 0.10  # 10%

# Anti-fraud
MIN_ACTIVITY_FOR_REWARD = 3  # Mínimo 3 acciones
MIN_TIME_ACTIVE_HOURS = 24   # Mínimo 24h activo

# Share messages
SHARE_MESSAGES = {
    SharePlatform.TELEGRAM: (
        "🚀 ¡Únete a Cazador Supremo y ahorra hasta 30% en vuelos!\n\n"
        "✈️ Encuentra los mejores precios\n"
        "💰 Gana FlightCoins\n"
        "🔔 Alertas de chollos\n\n"
        "👉 Usa mi código y consigue +300 coins de bienvenida:\n"
        "{link}"
    ),
    SharePlatform.WHATSAPP: (
        "🚀 *Cazador Supremo* - ¡Ahorra en vuelos!\n\n"
        "Pruébalo gratis y consigue +300 coins con mi código:\n"
        "{link}"
    ),
    SharePlatform.TWITTER: (
        "✈️ Ahorra hasta 30% en vuelos con @CazadorSupremo\n\n"
        "Consigue +300 coins de bienvenida con mi código:\n"
        "{link}\n\n"
        "#VuelosBaratos #Viajes #Ahorro"
    )
}


# ═══════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class ReferralCode:
    """Código de referido único"""
    code: str
    user_id: int
    created_at: str
    uses: int = 0
    conversions: int = 0  # Referidos que completaron actividad mínima
    total_earned: float = 0.0
    is_active: bool = True
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ReferralCode':
        return cls(**data)


@dataclass
class Referral:
    """Registro de un referido"""
    referee_id: int
    referrer_id: int
    referral_code: str
    created_at: str
    platform: str  # Desde dónde vino (telegram, whatsapp, etc)
    
    # Tracking de actividad
    is_active: bool = False  # Completó actividad mínima
    activation_date: Optional[str] = None
    total_actions: int = 0
    
    # Comisiones
    coins_earned_by_referee: float = 0.0  # Coins ganados por el referido
    commission_paid: float = 0.0  # Comisión pagada al referrer
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Referral':
        return cls(**data)


@dataclass
class ReferralStats:
    """Estadísticas de referidos por usuario"""
    user_id: int
    total_referrals: int = 0
    active_referrals: int = 0  # Referidos activos
    pending_referrals: int = 0  # Esperando activación
    
    # Earnings
    total_coins_earned: float = 0.0
    lifetime_commissions: float = 0.0
    
    # Tier
    current_tier: ReferralTier = ReferralTier.STARTER
    
    # Network
    network_size: int = 0  # Total incluyendo sub-referidos
    network_depth: int = 0  # Niveles de profundidad
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['current_tier'] = self.current_tier.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ReferralStats':
        data['current_tier'] = ReferralTier(data['current_tier'])
        return cls(**data)


# ═══════════════════════════════════════════════════════════════
#  VIRAL GROWTH MANAGER
# ═══════════════════════════════════════════════════════════════

class ViralGrowthManager:
    """
    Gestor del sistema viral de crecimiento.
    
    Responsabilidades:
    - Generación de códigos de referido
    - Tracking de referidos
    - Cálculo de recompensas
    - Comisiones lifetime
    - Analytics
    """
    
    def __init__(self,
                 codes_file: str = 'referral_codes.json',
                 referrals_file: str = 'referrals.json',
                 stats_file: str = 'referral_stats.json'):
        self.codes_file = Path(codes_file)
        self.referrals_file = Path(referrals_file)
        self.stats_file = Path(stats_file)
        
        self.codes: Dict[str, ReferralCode] = {}  # code -> ReferralCode
        self.user_codes: Dict[int, str] = {}  # user_id -> code
        self.referrals: Dict[int, List[Referral]] = {}  # referrer_id -> [Referral]
        self.stats: Dict[int, ReferralStats] = {}  # user_id -> ReferralStats
        
        self._load_data()
        
        logger.info("🦠 ViralGrowthManager initialized")
    
    def _load_data(self):
        """Carga datos desde archivos."""
        # Cargar códigos
        if self.codes_file.exists():
            try:
                with open(self.codes_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for code_str, code_data in data.items():
                    self.codes[code_str] = ReferralCode.from_dict(code_data)
                    self.user_codes[code_data['user_id']] = code_str
                
                logger.info(f"✅ Loaded {len(self.codes)} referral codes")
            except Exception as e:
                logger.error(f"❌ Error loading codes: {e}")
        
        # Cargar referrals
        if self.referrals_file.exists():
            try:
                with open(self.referrals_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for referrer_id_str, referrals_data in data.items():
                    referrer_id = int(referrer_id_str)
                    self.referrals[referrer_id] = [
                        Referral.from_dict(r) for r in referrals_data
                    ]
                
                logger.info(f"✅ Loaded referrals for {len(self.referrals)} users")
            except Exception as e:
                logger.error(f"❌ Error loading referrals: {e}")
        
        # Cargar stats
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for user_id_str, stats_data in data.items():
                    user_id = int(user_id_str)
                    self.stats[user_id] = ReferralStats.from_dict(stats_data)
                
                logger.info(f"✅ Loaded stats for {len(self.stats)} users")
            except Exception as e:
                logger.error(f"❌ Error loading stats: {e}")
    
    def _save_data(self):
        """Guarda datos a archivos."""
        try:
            # Guardar códigos
            codes_data = {
                code: ref_code.to_dict()
                for code, ref_code in self.codes.items()
            }
            with open(self.codes_file, 'w', encoding='utf-8') as f:
                json.dump(codes_data, f, indent=2, ensure_ascii=False)
            
            # Guardar referrals
            referrals_data = {
                str(user_id): [r.to_dict() for r in referrals]
                for user_id, referrals in self.referrals.items()
            }
            with open(self.referrals_file, 'w', encoding='utf-8') as f:
                json.dump(referrals_data, f, indent=2, ensure_ascii=False)
            
            # Guardar stats
            stats_data = {
                str(user_id): stats.to_dict()
                for user_id, stats in self.stats.items()
            }
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats_data, f, indent=2, ensure_ascii=False)
            
            logger.debug("💾 Viral growth data saved")
        except Exception as e:
            logger.error(f"❌ Error saving data: {e}")
    
    def generate_referral_code(self, user_id: int) -> str:
        """
        Genera código de referido único para usuario.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Código de referido (ej: 'FLY8X2K')
        """
        # Si ya tiene código, retornarlo
        if user_id in self.user_codes:
            return self.user_codes[user_id]
        
        # Generar código único
        while True:
            # Código de 7 caracteres alfanuméricos
            code = secrets.token_urlsafe(6)[:7].upper().replace('-', 'X').replace('_', 'Y')
            
            if code not in self.codes:
                break
        
        # Crear registro
        ref_code = ReferralCode(
            code=code,
            user_id=user_id,
            created_at=datetime.now().isoformat()
        )
        
        self.codes[code] = ref_code
        self.user_codes[user_id] = code
        
        # Inicializar stats
        if user_id not in self.stats:
            self.stats[user_id] = ReferralStats(user_id=user_id)
        
        self._save_data()
        
        logger.info(f"🎫 Generated referral code for user {user_id}: {code}")
        return code
    
    def process_referral(self,
                        referee_id: int,
                        referral_code: str,
                        platform: str = 'telegram') -> Tuple[bool, str]:
        """
        Procesa un nuevo referido.
        
        Args:
            referee_id: ID del usuario referido
            referral_code: Código usado
            platform: Plataforma origen
        
        Returns:
            (success: bool, message: str)
        """
        # Validar código
        if referral_code not in self.codes:
            return False, "Código de referido inválido"
        
        ref_code = self.codes[referral_code]
        referrer_id = ref_code.user_id
        
        # No puede referirse a sí mismo
        if referee_id == referrer_id:
            return False, "No puedes usar tu propio código"
        
        # Verificar si ya fue referido
        for referrals in self.referrals.values():
            if any(r.referee_id == referee_id for r in referrals):
                return False, "Ya fuiste referido anteriormente"
        
        # Crear referral
        referral = Referral(
            referee_id=referee_id,
            referrer_id=referrer_id,
            referral_code=referral_code,
            created_at=datetime.now().isoformat(),
            platform=platform
        )
        
        # Guardar
        if referrer_id not in self.referrals:
            self.referrals[referrer_id] = []
        self.referrals[referrer_id].append(referral)
        
        # Update código
        ref_code.uses += 1
        
        # Update stats
        if referrer_id not in self.stats:
            self.stats[referrer_id] = ReferralStats(user_id=referrer_id)
        
        stats = self.stats[referrer_id]
        stats.total_referrals += 1
        stats.pending_referrals += 1
        
        self._save_data()
        
        logger.info(
            f"🎉 New referral: User {referee_id} referred by {referrer_id} "
            f"via {platform}"
        )
        
        return True, f"¡Bienvenido! +{REFEREE_WELCOME_COINS} FlightCoins de regalo"
    
    def activate_referral(self, referee_id: int) -> Optional[float]:
        """
        Activa un referido cuando completa actividad mínima.
        Paga recompensas a ambas partes.
        
        Args:
            referee_id: ID del referido
        
        Returns:
            Coins ganados por el referrer (None si no aplica)
        """
        # Buscar referral
        referral = None
        referrer_id = None
        
        for rid, referrals in self.referrals.items():
            for r in referrals:
                if r.referee_id == referee_id and not r.is_active:
                    referral = r
                    referrer_id = rid
                    break
            if referral:
                break
        
        if not referral:
            return None
        
        # Activar
        referral.is_active = True
        referral.activation_date = datetime.now().isoformat()
        
        # Update código
        ref_code = self.codes[referral.referral_code]
        ref_code.conversions += 1
        
        # Update stats
        stats = self.stats[referrer_id]
        stats.pending_referrals -= 1
        stats.active_referrals += 1
        
        # Calcular tier
        tier = self._get_tier(stats.active_referrals)
        old_tier = stats.current_tier
        stats.current_tier = tier
        
        # Calcular recompensa
        tier_config = REFERRAL_REWARDS[tier]
        coins = tier_config['coins_per_ref']
        
        # Bonus por nuevo tier
        bonus = 0
        if tier != old_tier:
            bonus = tier_config['bonus']
            logger.info(f"🎊 User {referrer_id} reached tier {tier.value}!")
        
        total_coins = coins + bonus
        
        stats.total_coins_earned += total_coins
        ref_code.total_earned += total_coins
        
        self._save_data()
        
        logger.info(
            f"✅ Referral activated: {referee_id} -> {referrer_id} "
            f"(+{total_coins} coins)"
        )
        
        return total_coins
    
    def _get_tier(self, active_refs: int) -> ReferralTier:
        """Calcula tier basado en referidos activos."""
        if active_refs >= 50:
            return ReferralTier.AMBASSADOR
        elif active_refs >= 16:
            return ReferralTier.EXPERT
        elif active_refs >= 6:
            return ReferralTier.BUILDER
        else:
            return ReferralTier.STARTER
    
    def get_referral_link(self, user_id: int, bot_username: str) -> str:
        """
        Genera link de referido para usuario.
        
        Args:
            user_id: ID del usuario
            bot_username: Username del bot
        
        Returns:
            Deep link (ej: https://t.me/bot?start=ref_FLY8X2K)
        """
        code = self.generate_referral_code(user_id)
        return f"https://t.me/{bot_username}?start=ref_{code}"
    
    def get_share_message(self,
                         user_id: int,
                         platform: SharePlatform,
                         bot_username: str) -> str:
        """
        Genera mensaje para compartir en plataforma.
        
        Args:
            user_id: ID del usuario
            platform: Plataforma destino
            bot_username: Username del bot
        
        Returns:
            Mensaje formateado con link
        """
        link = self.get_referral_link(user_id, bot_username)
        template = SHARE_MESSAGES.get(platform, SHARE_MESSAGES[SharePlatform.TELEGRAM])
        return template.format(link=link)
    
    def get_user_stats(self, user_id: int) -> Optional[ReferralStats]:
        """Obtiene stats de referidos del usuario."""
        return self.stats.get(user_id)
    
    def get_leaderboard(self, limit: int = 10) -> List[Tuple[int, ReferralStats]]:
        """
        Obtiene leaderboard de top referrers.
        
        Args:
            limit: Número de resultados
        
        Returns:
            Lista de (user_id, ReferralStats) ordenada
        """
        sorted_stats = sorted(
            self.stats.items(),
            key=lambda x: x[1].active_referrals,
            reverse=True
        )
        return sorted_stats[:limit]


if __name__ == '__main__':
    # 🧪 Tests rápidos
    print("🧪 Testing ViralGrowthManager...\n")
    
    mgr = ViralGrowthManager(
        'test_ref_codes.json',
        'test_referrals.json',
        'test_ref_stats.json'
    )
    
    # Test 1: Generate code
    print("1. Generating referral code...")
    code = mgr.generate_referral_code(12345)
    print(f"   Code: {code}\n")
    
    # Test 2: Process referral
    print("2. Processing referral...")
    success, msg = mgr.process_referral(67890, code, 'telegram')
    print(f"   Success: {success}")
    print(f"   Message: {msg}\n")
    
    # Test 3: Activate referral
    print("3. Activating referral...")
    coins = mgr.activate_referral(67890)
    print(f"   Coins earned: {coins}\n")
    
    # Test 4: Get stats
    print("4. Getting user stats...")
    stats = mgr.get_user_stats(12345)
    print(f"   Total referrals: {stats.total_referrals}")
    print(f"   Active: {stats.active_referrals}")
    print(f"   Tier: {stats.current_tier.value}\n")
    
    # Test 5: Generate link
    print("5. Generating referral link...")
    link = mgr.get_referral_link(12345, 'CazadorSupremoBot')
    print(f"   Link: {link}\n")
    
    print("✅ All tests completed!")
