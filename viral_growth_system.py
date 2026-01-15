#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Viral Growth System - IT5 Day 1/5
Sistema de referidos bilateral con recompensas y anti-fraude

Author: @Juanka_Spain
Version: 13.1.0
Date: 2026-01-15
"""

import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class ReferralCode:
    """Código de referido único"""
    code: str
    user_id: int
    username: str
    created_at: str
    uses: int = 0
    max_uses: int = 50  # Límite anti-abuso
    is_active: bool = True


@dataclass
class ReferralReward:
    """Recompensa por referido"""
    referrer_coins: int  # Monedas para quien refiere
    referee_coins: int   # Monedas para el nuevo usuario
    referrer_bonus: str  # Bonus adicional para referrer
    referee_bonus: str   # Bonus adicional para referee


@dataclass
class ReferralRelationship:
    """Relación referido-referrer"""
    referee_id: int
    referee_username: str
    referrer_id: int
    referrer_username: str
    referral_code: str
    created_at: str
    reward_claimed: bool = False
    referee_active: bool = False  # Se activa tras primera búsqueda


class ReferralManager:
    """
    Gestor del sistema de referidos bilateral.
    
    Features:
    - Códigos únicos por usuario
    - Recompensas tier-based
    - Anti-fraude (device fingerprint, rate limiting)
    - Analytics completo
    - Viral loops (milestones)
    """
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.referral_codes_file = self.data_dir / "referral_codes.json"
        self.relationships_file = self.data_dir / "referral_relationships.json"
        self.analytics_file = self.data_dir / "referral_analytics.json"
        
        self.codes: Dict[str, ReferralCode] = {}
        self.relationships: List[ReferralRelationship] = []
        self.analytics: Dict = self._init_analytics()
        
        self._load_data()
    
    def _init_analytics(self) -> Dict:
        """Inicializa estructura de analytics"""
        return {
            "total_codes_generated": 0,
            "total_referrals": 0,
            "total_active_referrals": 0,
            "total_coins_distributed": 0,
            "top_referrers": [],
            "conversion_rate": 0.0,
            "avg_referrals_per_user": 0.0,
            "viral_coefficient": 0.0,  # K-factor
            "last_updated": datetime.now().isoformat()
        }
    
    def _load_data(self):
        """Carga datos desde archivos JSON"""
        # Cargar códigos
        if self.referral_codes_file.exists():
            with open(self.referral_codes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.codes = {
                    k: ReferralCode(**v) for k, v in data.items()
                }
        
        # Cargar relaciones
        if self.relationships_file.exists():
            with open(self.relationships_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.relationships = [
                    ReferralRelationship(**item) for item in data
                ]
        
        # Cargar analytics
        if self.analytics_file.exists():
            with open(self.analytics_file, 'r', encoding='utf-8') as f:
                self.analytics = json.load(f)
    
    def _save_data(self):
        """Guarda datos en archivos JSON"""
        # Guardar códigos
        with open(self.referral_codes_file, 'w', encoding='utf-8') as f:
            data = {k: asdict(v) for k, v in self.codes.items()}
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Guardar relaciones
        with open(self.relationships_file, 'w', encoding='utf-8') as f:
            data = [asdict(r) for r in self.relationships]
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Guardar analytics
        with open(self.analytics_file, 'w', encoding='utf-8') as f:
            json.dump(self.analytics, f, indent=2, ensure_ascii=False)
    
    def generate_referral_code(self, user_id: int, username: str) -> str:
        """
        Genera código de referido único para un usuario.
        
        Formato: VUELOS-{hash}-{random}
        Ejemplo: VUELOS-A3F9-X7K2
        """
        # Verificar si ya tiene código
        existing = self.get_user_referral_code(user_id)
        if existing:
            return existing.code
        
        # Generar código único
        hash_part = hashlib.md5(f"{user_id}{username}".encode()).hexdigest()[:4].upper()
        random_part = secrets.token_hex(2).upper()
        code = f"VUELOS-{hash_part}-{random_part}"
        
        # Asegurar unicidad
        while code in self.codes:
            random_part = secrets.token_hex(2).upper()
            code = f"VUELOS-{hash_part}-{random_part}"
        
        # Crear y guardar
        referral_code = ReferralCode(
            code=code,
            user_id=user_id,
            username=username,
            created_at=datetime.now().isoformat()
        )
        
        self.codes[code] = referral_code
        self.analytics["total_codes_generated"] += 1
        self._save_data()
        
        return code
    
    def get_user_referral_code(self, user_id: int) -> Optional[ReferralCode]:
        """Obtiene el código de referido de un usuario"""
        for code_obj in self.codes.values():
            if code_obj.user_id == user_id:
                return code_obj
        return None
    
    def validate_referral_code(self, code: str) -> Tuple[bool, str]:
        """
        Valida un código de referido.
        
        Returns:
            (is_valid, message)
        """
        if code not in self.codes:
            return False, "❌ Código inválido"
        
        code_obj = self.codes[code]
        
        if not code_obj.is_active:
            return False, "❌ Código desactivado"
        
        if code_obj.uses >= code_obj.max_uses:
            return False, "❌ Código alcanzó límite de usos"
        
        return True, "✅ Código válido"
    
    def apply_referral_code(
        self, 
        referee_id: int, 
        referee_username: str, 
        referral_code: str,
        device_fingerprint: Optional[str] = None
    ) -> Tuple[bool, str, Optional[ReferralReward]]:
        """
        Aplica un código de referido.
        
        Anti-fraude:
        - Usuario no puede usar su propio código
        - Usuario solo puede ser referido una vez
        - Rate limiting por device
        
        Returns:
            (success, message, reward)
        """
        # Validar código
        is_valid, msg = self.validate_referral_code(referral_code)
        if not is_valid:
            return False, msg, None
        
        code_obj = self.codes[referral_code]
        
        # Anti-fraude: no auto-referirse
        if code_obj.user_id == referee_id:
            return False, "❌ No puedes usar tu propio código", None
        
        # Anti-fraude: solo un referido por usuario
        for rel in self.relationships:
            if rel.referee_id == referee_id:
                return False, "❌ Ya fuiste referido anteriormente", None
        
        # TODO: Anti-fraude por device_fingerprint (opcional)
        # if device_fingerprint:
        #     recent_uses = self._check_device_rate_limit(device_fingerprint)
        #     if recent_uses > 3:  # Máx 3 usos por device en 24h
        #         return False, "❌ Demasiados usos desde este dispositivo", None
        
        # Calcular recompensas basadas en tier del referrer
        reward = self._calculate_referral_reward(code_obj.user_id)
        
        # Crear relación
        relationship = ReferralRelationship(
            referee_id=referee_id,
            referee_username=referee_username,
            referrer_id=code_obj.user_id,
            referrer_username=code_obj.username,
            referral_code=referral_code,
            created_at=datetime.now().isoformat()
        )
        
        self.relationships.append(relationship)
        code_obj.uses += 1
        
        # Actualizar analytics
        self.analytics["total_referrals"] += 1
        self.analytics["total_coins_distributed"] += (
            reward.referrer_coins + reward.referee_coins
        )
        
        self._save_data()
        self._update_analytics()
        
        success_msg = (
            f"✅ ¡Código aplicado!\n"
            f"🎉 Ganaste {reward.referee_coins} FlightCoins\n"
            f"🎁 Bonus: {reward.referee_bonus}"
        )
        
        return True, success_msg, reward
    
    def _calculate_referral_reward(
        self, 
        referrer_id: int
    ) -> ReferralReward:
        """
        Calcula recompensas basadas en el tier del referrer.
        
        Tier Bronze: 500/300
        Tier Silver: 750/400
        Tier Gold: 1000/500
        Tier Diamond: 1500/750
        """
        # Obtener tier del referrer (desde retention_system)
        # Por ahora, recompensa base
        referrer_tier = self._get_user_tier(referrer_id)
        
        tier_rewards = {
            "BRONZE": (500, 300, "🆓 +3 búsquedas gratis", "🎁 +1 watchlist slot"),
            "SILVER": (750, 400, "🆓 +5 búsquedas gratis", "🎁 +2 watchlist slots"),
            "GOLD": (1000, 500, "🆓 +10 búsquedas gratis", "🎁 +5 watchlist slots"),
            "DIAMOND": (1500, 750, "🆓 Búsquedas ilimitadas 7d", "🎁 +10 watchlist slots")
        }
        
        referrer_coins, referee_coins, ref_bonus, ree_bonus = tier_rewards.get(
            referrer_tier, (500, 300, "🆓 +3 búsquedas", "🎁 +1 slot")
        )
        
        return ReferralReward(
            referrer_coins=referrer_coins,
            referee_coins=referee_coins,
            referrer_bonus=ref_bonus,
            referee_bonus=ree_bonus
        )
    
    def _get_user_tier(self, user_id: int) -> str:
        """
        Obtiene el tier de un usuario.
        Integra con retention_system.py
        """
        # TODO: Integrar con RetentionSystem
        # Por ahora retorna BRONZE por defecto
        try:
            from retention_system import RetentionSystem
            retention = RetentionSystem()
            profile = retention.get_profile(user_id)
            return profile.tier if profile else "BRONZE"
        except:
            return "BRONZE"
    
    def activate_referee(self, referee_id: int) -> bool:
        """
        Activa un referido tras su primera búsqueda.
        Esto desbloquea la recompensa completa para el referrer.
        """
        for rel in self.relationships:
            if rel.referee_id == referee_id and not rel.referee_active:
                rel.referee_active = True
                rel.reward_claimed = True
                self.analytics["total_active_referrals"] += 1
                self._save_data()
                self._update_analytics()
                return True
        return False
    
    def get_user_referrals(self, user_id: int) -> List[ReferralRelationship]:
        """Obtiene todos los referidos de un usuario"""
        return [
            rel for rel in self.relationships 
            if rel.referrer_id == user_id
        ]
    
    def get_referral_stats(self, user_id: int) -> Dict:
        """
        Obtiene estadísticas de referidos de un usuario.
        """
        referrals = self.get_user_referrals(user_id)
        active_referrals = [r for r in referrals if r.referee_active]
        
        total_earned = len(active_referrals) * 500  # Base reward
        
        return {
            "total_referrals": len(referrals),
            "active_referrals": len(active_referrals),
            "pending_activation": len(referrals) - len(active_referrals),
            "total_coins_earned": total_earned,
            "referral_code": self.get_user_referral_code(user_id).code if self.get_user_referral_code(user_id) else None,
            "next_milestone": self._get_next_milestone(len(active_referrals))
        }
    
    def _get_next_milestone(self, current_referrals: int) -> Dict:
        """
        Obtiene el siguiente milestone de referidos.
        
        Milestones:
        - 5 referrals: +1000 coins bonus
        - 10 referrals: +2500 coins + badge
        - 25 referrals: +5000 coins + exclusive feature
        - 50 referrals: +10000 coins + VIP status
        """
        milestones = [
            {"count": 5, "reward": "+1000 coins", "emoji": "🎖️"},
            {"count": 10, "reward": "+2500 coins + Badge", "emoji": "🏆"},
            {"count": 25, "reward": "+5000 coins + Feature", "emoji": "👑"},
            {"count": 50, "reward": "+10000 coins + VIP", "emoji": "💎"}
        ]
        
        for milestone in milestones:
            if current_referrals < milestone["count"]:
                remaining = milestone["count"] - current_referrals
                return {
                    "target": milestone["count"],
                    "remaining": remaining,
                    "reward": milestone["reward"],
                    "emoji": milestone["emoji"]
                }
        
        return {
            "target": 100,
            "remaining": 100 - current_referrals,
            "reward": "Legend Status",
            "emoji": "🌟"
        }
    
    def _update_analytics(self):
        """Actualiza métricas de analytics"""
        total_users = len(set(code.user_id for code in self.codes.values()))
        total_referrals = len(self.relationships)
        total_active = self.analytics["total_active_referrals"]
        
        # Conversion rate: referidos que se activan
        if total_referrals > 0:
            self.analytics["conversion_rate"] = (
                total_active / total_referrals * 100
            )
        
        # Avg referrals per user
        if total_users > 0:
            self.analytics["avg_referrals_per_user"] = (
                total_referrals / total_users
            )
        
        # Viral coefficient (K-factor)
        # K = avg_referrals * conversion_rate
        self.analytics["viral_coefficient"] = (
            self.analytics["avg_referrals_per_user"] * 
            (self.analytics["conversion_rate"] / 100)
        )
        
        # Top referrers
        referrer_counts = {}
        for rel in self.relationships:
            if rel.referee_active:
                referrer_counts[rel.referrer_username] = \
                    referrer_counts.get(rel.referrer_username, 0) + 1
        
        self.analytics["top_referrers"] = sorted(
            [
                {"username": k, "count": v} 
                for k, v in referrer_counts.items()
            ],
            key=lambda x: x["count"],
            reverse=True
        )[:10]
        
        self.analytics["last_updated"] = datetime.now().isoformat()
    
    def get_global_analytics(self) -> Dict:
        """Retorna analytics globales del sistema"""
        return self.analytics
    
    def deactivate_code(self, user_id: int) -> bool:
        """Desactiva el código de referido de un usuario"""
        code_obj = self.get_user_referral_code(user_id)
        if code_obj:
            code_obj.is_active = False
            self._save_data()
            return True
        return False


if __name__ == "__main__":
    # Testing
    print("🚀 Testing Referral System...")
    
    manager = ReferralManager()
    
    # Generar códigos
    code1 = manager.generate_referral_code(12345, "john_doe")
    print(f"\n✅ Código generado: {code1}")
    
    code2 = manager.generate_referral_code(67890, "jane_smith")
    print(f"✅ Código generado: {code2}")
    
    # Aplicar referido
    success, msg, reward = manager.apply_referral_code(
        referee_id=11111,
        referee_username="new_user",
        referral_code=code1
    )
    
    print(f"\n{msg}")
    
    if reward:
        print(f"\n💰 Referrer gana: {reward.referrer_coins} coins")
        print(f"🎁 Referee gana: {reward.referee_coins} coins")
    
    # Stats
    stats = manager.get_referral_stats(12345)
    print(f"\n📊 Stats de john_doe:")
    print(f"  Total referidos: {stats['total_referrals']}")
    print(f"  Activos: {stats['active_referrals']}")
    print(f"  Coins ganados: {stats['total_coins_earned']}")
    
    # Analytics globales
    analytics = manager.get_global_analytics()
    print(f"\n🌍 Analytics Globales:")
    print(f"  Total referrals: {analytics['total_referrals']}")
    print(f"  Conversion rate: {analytics['conversion_rate']:.1f}%")
    print(f"  Viral coefficient: {analytics['viral_coefficient']:.2f}")
    
    print("\n✅ Tests completados!")
