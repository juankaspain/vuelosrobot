#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
┌────────────────────────────────────────────────────────────────┐
│  🦠 VIRAL GROWTH SYSTEM - Two-Sided Referrals              │
│  🚀 Cazador Supremo v13.0 Enterprise                          │
│  🎯 Target: Viral Coefficient >1.0                           │
└────────────────────────────────────────────────────────────────┘

Sistema de crecimiento viral con referidos:
- Two-sided referral rewards
- Unique referral codes
- Multi-tier bonus system
- Fraud prevention
- Analytics tracking

Autor: @Juanka_Spain
Version: 13.0.0
Date: 2026-01-14
"""

import json
import logging
import random
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  CONSTANTS & ENUMS
# ═══════════════════════════════════════════════════════════════

class ReferralStatus(Enum):
    """Estados del referido"""
    PENDING = "pending"          # Registrado pero no completó onboarding
    COMPLETED = "completed"      # Completó onboarding
    ACTIVE = "active"            # Usó el bot 3+ veces
    CHURNED = "churned"          # No vuelve en 7+ días


class RewardTier(Enum):
    """Tiers de rewards por referidos"""
    TIER_1 = "tier_1"   # 1 ref
    TIER_2 = "tier_2"   # 5 refs
    TIER_3 = "tier_3"   # 10 refs
    TIER_4 = "tier_4"   # 25 refs
    TIER_5 = "tier_5"   # 50 refs


# Rewards por tier
REFERRAL_REWARDS = {
    'base_referrer': 500,      # Referrer gana por cada referido
    'base_referee': 200,       # Referee gana al registrarse
    RewardTier.TIER_1: 500,    # 1 ref
    RewardTier.TIER_2: 1000,   # 5 refs bonus
    RewardTier.TIER_3: 3000,   # 10 refs bonus + badge
    RewardTier.TIER_4: 10000,  # 25 refs bonus + premium
    RewardTier.TIER_5: 25000   # 50 refs bonus + legend
}

# Prefijos para códigos
CODE_PREFIXES = ['FLIGHT', 'DEALS', 'SAVE', 'FLY', 'TRAVEL']

# Fraud prevention
MIN_TIME_BETWEEN_REFS = 60  # segundos
MAX_REFS_PER_DAY = 10
MAX_REFS_SAME_IP = 3


# ═══════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class Referral:
    """Referido individual"""
    referee_id: int                      # Usuario referido
    referee_username: str
    referrer_id: int                     # Usuario que refirió
    referrer_username: str
    referral_code: str                   # Código usado
    status: ReferralStatus
    
    # Timestamps
    created_at: str
    completed_at: Optional[str] = None
    last_active_at: Optional[str] = None
    
    # Metadata
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    
    # Rewards
    referrer_reward_given: bool = False
    referee_reward_given: bool = False
    referrer_coins_earned: int = 0
    referee_coins_earned: int = 0
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'status': self.status.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Referral':
        data['status'] = ReferralStatus(data['status'])
        return cls(**data)


@dataclass
class ReferralCode:
    """Código de referido"""
    code: str
    owner_id: int
    owner_username: str
    created_at: str
    
    # Stats
    uses: int = 0
    successful_conversions: int = 0
    total_coins_earned: int = 0
    
    # Metadata
    is_active: bool = True
    expires_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ReferralCode':
        return cls(**data)


@dataclass
class ReferralStats:
    """Estadísticas de referidos por usuario"""
    user_id: int
    
    # Contadores
    total_referrals: int = 0
    pending_referrals: int = 0
    completed_referrals: int = 0
    active_referrals: int = 0
    
    # Rewards
    total_coins_earned: int = 0
    current_tier: Optional[RewardTier] = None
    next_tier_refs_needed: int = 5
    
    # Achievements
    referral_king_unlocked: bool = False
    premium_unlocked: bool = False
    legend_unlocked: bool = False
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        if self.current_tier:
            data['current_tier'] = self.current_tier.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ReferralStats':
        if data.get('current_tier'):
            data['current_tier'] = RewardTier(data['current_tier'])
        return cls(**data)


# ═══════════════════════════════════════════════════════════════
#  REFERRAL MANAGER
# ═══════════════════════════════════════════════════════════════

class ReferralManager:
    """
    Gestor del sistema de referidos.
    
    Responsabilidades:
    - Generar códigos únicos
    - Tracking de referidos
    - Distribución de rewards
    - Fraud prevention
    - Analytics
    """
    
    def __init__(self,
                 codes_file: str = 'referral_codes.json',
                 referrals_file: str = 'referrals.json',
                 stats_file: str = 'referral_stats.json'):
        self.codes_file = Path(codes_file)
        self.referrals_file = Path(referrals_file)
        self.stats_file = Path(stats_file)
        
        # Data structures
        self.codes: Dict[str, ReferralCode] = {}          # code -> ReferralCode
        self.user_codes: Dict[int, str] = {}              # user_id -> code
        self.referrals: Dict[int, List[Referral]] = {}    # referrer_id -> [Referral]
        self.stats: Dict[int, ReferralStats] = {}         # user_id -> ReferralStats
        
        # Fraud prevention tracking
        self.recent_refs: Dict[int, List[datetime]] = {}  # user_id -> [timestamps]
        self.ip_refs: Dict[str, List[int]] = {}           # ip -> [user_ids]
        
        self._load_data()
        
        logger.info("🦠 ReferralManager initialized")
    
    def _load_data(self):
        """Carga datos desde archivos."""
        # Load codes
        if self.codes_file.exists():
            try:
                with open(self.codes_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for code_str, code_data in data.items():
                    code = ReferralCode.from_dict(code_data)
                    self.codes[code_str] = code
                    self.user_codes[code.owner_id] = code_str
                
                logger.info(f"✅ Loaded {len(self.codes)} referral codes")
            except Exception as e:
                logger.error(f"❌ Error loading codes: {e}")
        
        # Load referrals
        if self.referrals_file.exists():
            try:
                with open(self.referrals_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for user_id_str, refs_data in data.items():
                    user_id = int(user_id_str)
                    self.referrals[user_id] = [
                        Referral.from_dict(ref_data) for ref_data in refs_data
                    ]
                
                logger.info(f"✅ Loaded referrals for {len(self.referrals)} users")
            except Exception as e:
                logger.error(f"❌ Error loading referrals: {e}")
        
        # Load stats
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
            # Save codes
            with open(self.codes_file, 'w', encoding='utf-8') as f:
                data = {code: obj.to_dict() for code, obj in self.codes.items()}
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Save referrals
            with open(self.referrals_file, 'w', encoding='utf-8') as f:
                data = {
                    str(user_id): [ref.to_dict() for ref in refs]
                    for user_id, refs in self.referrals.items()
                }
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Save stats
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                data = {
                    str(user_id): stats.to_dict()
                    for user_id, stats in self.stats.items()
                }
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("💾 Referral data saved")
        except Exception as e:
            logger.error(f"❌ Error saving data: {e}")
    
    def _generate_unique_code(self) -> str:
        """Genera código de referido único."""
        while True:
            prefix = random.choice(CODE_PREFIXES)
            suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
            code = f"{prefix}-{suffix}"
            
            if code not in self.codes:
                return code
    
    def get_or_create_referral_code(self, user_id: int, username: str) -> str:
        """Obtiene o crea código de referido para usuario."""
        # Si ya tiene código
        if user_id in self.user_codes:
            return self.user_codes[user_id]
        
        # Generar nuevo código
        code = self._generate_unique_code()
        
        referral_code = ReferralCode(
            code=code,
            owner_id=user_id,
            owner_username=username,
            created_at=datetime.now().isoformat()
        )
        
        self.codes[code] = referral_code
        self.user_codes[user_id] = code
        self._save_data()
        
        logger.info(f"🎫 Generated referral code {code} for user {user_id}")
        return code
    
    def validate_referral_code(self, code: str) -> Tuple[bool, Optional[str]]:
        """Valida código de referido."""
        if code not in self.codes:
            return False, "Código inválido"
        
        ref_code = self.codes[code]
        
        if not ref_code.is_active:
            return False, "Código desactivado"
        
        if ref_code.expires_at:
            expiry = datetime.fromisoformat(ref_code.expires_at)
            if datetime.now() > expiry:
                return False, "Código expirado"
        
        return True, None
    
    def check_fraud_flags(self,
                         referrer_id: int,
                         referee_id: int,
                         ip_address: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Verifica señales de fraude."""
        # No auto-referirse
        if referrer_id == referee_id:
            return False, "No puedes referirte a ti mismo"
        
        # Rate limiting temporal
        if referrer_id in self.recent_refs:
            recent = self.recent_refs[referrer_id]
            # Limpiar referencias antiguas
            cutoff = datetime.now() - timedelta(seconds=MIN_TIME_BETWEEN_REFS)
            recent = [ts for ts in recent if ts > cutoff]
            self.recent_refs[referrer_id] = recent
            
            if recent:
                return False, f"Espera {MIN_TIME_BETWEEN_REFS}s entre referidos"
        
        # Max refs por día
        if referrer_id in self.referrals:
            today = datetime.now().date()
            refs_today = sum(
                1 for ref in self.referrals[referrer_id]
                if datetime.fromisoformat(ref.created_at).date() == today
            )
            
            if refs_today >= MAX_REFS_PER_DAY:
                return False, "Límite diario de referidos alcanzado"
        
        # IP tracking
        if ip_address:
            if ip_address in self.ip_refs:
                if len(self.ip_refs[ip_address]) >= MAX_REFS_SAME_IP:
                    return False, "Demasiados referidos desde esta IP"
        
        return True, None
    
    def register_referral(self,
                         referral_code: str,
                         referee_id: int,
                         referee_username: str,
                         device_info: Optional[str] = None,
                         ip_address: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Registra nuevo referido.
        
        Returns:
            (success, error_message)
        """
        # Validar código
        valid, error = self.validate_referral_code(referral_code)
        if not valid:
            return False, error
        
        ref_code = self.codes[referral_code]
        referrer_id = ref_code.owner_id
        
        # Check fraud
        valid, error = self.check_fraud_flags(referrer_id, referee_id, ip_address)
        if not valid:
            return False, error
        
        # Crear referral
        referral = Referral(
            referee_id=referee_id,
            referee_username=referee_username,
            referrer_id=referrer_id,
            referrer_username=ref_code.owner_username,
            referral_code=referral_code,
            status=ReferralStatus.PENDING,
            created_at=datetime.now().isoformat(),
            device_info=device_info,
            ip_address=ip_address
        )
        
        # Guardar referral
        if referrer_id not in self.referrals:
            self.referrals[referrer_id] = []
        self.referrals[referrer_id].append(referral)
        
        # Update code stats
        ref_code.uses += 1
        
        # Update stats
        if referrer_id not in self.stats:
            self.stats[referrer_id] = ReferralStats(user_id=referrer_id)
        self.stats[referrer_id].total_referrals += 1
        self.stats[referrer_id].pending_referrals += 1
        
        # Track for fraud prevention
        if referrer_id not in self.recent_refs:
            self.recent_refs[referrer_id] = []
        self.recent_refs[referrer_id].append(datetime.now())
        
        if ip_address:
            if ip_address not in self.ip_refs:
                self.ip_refs[ip_address] = []
            self.ip_refs[ip_address].append(referee_id)
        
        self._save_data()
        
        logger.info(
            f"✅ Registered referral: {referee_username} referred by "
            f"{ref_code.owner_username} (code: {referral_code})"
        )
        
        return True, None
    
    def complete_referral(self,
                         referee_id: int,
                         retention_manager) -> Tuple[int, int]:
        """
        Completa referido cuando referee termina onboarding.
        
        Args:
            referee_id: Usuario referido
            retention_manager: RetentionManager para dar rewards
        
        Returns:
            (referrer_coins, referee_coins)
        """
        # Buscar referral
        referral = None
        referrer_id = None
        
        for r_id, refs in self.referrals.items():
            for ref in refs:
                if ref.referee_id == referee_id and ref.status == ReferralStatus.PENDING:
                    referral = ref
                    referrer_id = r_id
                    break
            if referral:
                break
        
        if not referral:
            return 0, 0
        
        # Update referral status
        referral.status = ReferralStatus.COMPLETED
        referral.completed_at = datetime.now().isoformat()
        
        # Award coins
        referrer_coins = REFERRAL_REWARDS['base_referrer']
        referee_coins = REFERRAL_REWARDS['base_referee']
        
        # Give rewards
        retention_manager.add_coins(
            referrer_id,
            referrer_coins,
            reason=f"Referido: @{referral.referee_username}"
        )
        
        retention_manager.add_coins(
            referee_id,
            referee_coins,
            reason="Bonus de bienvenida por referido"
        )
        
        # Update referral
        referral.referrer_reward_given = True
        referral.referee_reward_given = True
        referral.referrer_coins_earned = referrer_coins
        referral.referee_coins_earned = referee_coins
        
        # Update code stats
        code = self.codes[referral.referral_code]
        code.successful_conversions += 1
        code.total_coins_earned += referrer_coins
        
        # Update stats
        stats = self.stats[referrer_id]
        stats.completed_referrals += 1
        stats.pending_referrals -= 1
        stats.total_coins_earned += referrer_coins
        
        # Check tier upgrades
        self._check_tier_upgrades(referrer_id, retention_manager)
        
        self._save_data()
        
        logger.info(
            f"💰 Referral completed: {referrer_id} earned {referrer_coins} coins, "
            f"{referee_id} earned {referee_coins} coins"
        )
        
        return referrer_coins, referee_coins
    
    def _check_tier_upgrades(self, user_id: int, retention_manager):
        """Verifica y otorga bonos de tier."""
        stats = self.stats[user_id]
        total = stats.completed_referrals
        
        # Tier 2: 5 refs
        if total >= 5 and (not stats.current_tier or stats.current_tier.value < RewardTier.TIER_2.value):
            bonus = REFERRAL_REWARDS[RewardTier.TIER_2]
            retention_manager.add_coins(user_id, bonus, reason="Bonus 5 referidos")
            stats.current_tier = RewardTier.TIER_2
            stats.next_tier_refs_needed = 10 - total
            logger.info(f"🎁 User {user_id} reached TIER 2: +{bonus} coins")
        
        # Tier 3: 10 refs + badge
        if total >= 10 and (not stats.current_tier or stats.current_tier.value < RewardTier.TIER_3.value):
            bonus = REFERRAL_REWARDS[RewardTier.TIER_3]
            retention_manager.add_coins(user_id, bonus, reason="Bonus 10 referidos")
            stats.current_tier = RewardTier.TIER_3
            stats.next_tier_refs_needed = 25 - total
            stats.referral_king_unlocked = True
            
            # Unlock Referral King achievement
            from retention_system import AchievementType
            retention_manager.unlock_achievement(user_id, AchievementType.REFERRAL_KING)
            
            logger.info(f"👑 User {user_id} reached TIER 3: +{bonus} coins + Referral King badge")
        
        # Tier 4: 25 refs + premium
        if total >= 25 and (not stats.current_tier or stats.current_tier.value < RewardTier.TIER_4.value):
            bonus = REFERRAL_REWARDS[RewardTier.TIER_4]
            retention_manager.add_coins(user_id, bonus, reason="Bonus 25 referidos")
            stats.current_tier = RewardTier.TIER_4
            stats.next_tier_refs_needed = 50 - total
            stats.premium_unlocked = True
            logger.info(f"💎 User {user_id} reached TIER 4: +{bonus} coins + Premium")
        
        # Tier 5: 50 refs + legend
        if total >= 50 and (not stats.current_tier or stats.current_tier.value < RewardTier.TIER_5.value):
            bonus = REFERRAL_REWARDS[RewardTier.TIER_5]
            retention_manager.add_coins(user_id, bonus, reason="Bonus 50 referidos")
            stats.current_tier = RewardTier.TIER_5
            stats.legend_unlocked = True
            logger.info(f"⚡ User {user_id} reached TIER 5: +{bonus} coins + LEGEND")
    
    def get_user_stats(self, user_id: int) -> Optional[ReferralStats]:
        """Obtiene stats de referidos del usuario."""
        return self.stats.get(user_id)
    
    def get_leaderboard(self, limit: int = 10) -> List[Tuple[int, int]]:
        """Obtiene top referrers."""
        sorted_users = sorted(
            self.stats.items(),
            key=lambda x: x[1].completed_referrals,
            reverse=True
        )
        return [(user_id, stats.completed_referrals) for user_id, stats in sorted_users[:limit]]
    
    def get_viral_coefficient(self) -> float:
        """
        Calcula K-factor (viral coefficient).
        
        K = (# invites sent per user) × (conversion rate)
        K > 1 = exponential growth
        """
        if not self.stats:
            return 0.0
        
        total_users = len(self.stats)
        total_invites = sum(s.total_referrals for s in self.stats.values())
        total_conversions = sum(s.completed_referrals for s in self.stats.values())
        
        if total_invites == 0:
            return 0.0
        
        avg_invites = total_invites / total_users
        conversion_rate = total_conversions / total_invites
        
        k_factor = avg_invites * conversion_rate
        
        return k_factor


if __name__ == '__main__':
    # 🧪 Tests rápidos
    print("🧪 Testing ReferralManager...\n")
    
    mgr = ReferralManager('test_codes.json', 'test_refs.json', 'test_stats.json')
    
    # Test 1: Generate code
    print("1. Generating referral code...")
    code = mgr.get_or_create_referral_code(12345, "juan")
    print(f"   Code: {code}\n")
    
    # Test 2: Validate code
    print("2. Validating code...")
    valid, error = mgr.validate_referral_code(code)
    print(f"   Valid: {valid}\n")
    
    # Test 3: Register referral
    print("3. Registering referral...")
    success, error = mgr.register_referral(code, 67890, "maria")
    print(f"   Success: {success}\n")
    
    # Test 4: Stats
    print("4. Getting stats...")
    stats = mgr.get_user_stats(12345)
    if stats:
        print(f"   Total referrals: {stats.total_referrals}")
        print(f"   Pending: {stats.pending_referrals}\n")
    
    # Test 5: Viral coefficient
    print("5. Calculating K-factor...")
    k = mgr.get_viral_coefficient()
    print(f"   K-factor: {k:.2f}\n")
    
    print("✅ All tests completed!")
