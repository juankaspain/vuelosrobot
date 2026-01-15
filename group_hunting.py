#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Group Deal Hunting System - IT5 Day 3/5
Sistema de caza colaborativa de chollos en grupo

Author: @Juanka_Spain
Version: 13.1.0
Date: 2026-01-15
"""

import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
from enum import Enum


class GroupType(Enum):
    """Tipos de grupos de caza"""
    PUBLIC = "public"  # Cualquiera puede unirse
    PRIVATE = "private"  # Solo por invitación
    ROUTE_SPECIFIC = "route_specific"  # Enfocado en una ruta
    DESTINATION = "destination"  # Enfocado en un destino


class MemberRole(Enum):
    """Roles de miembros en el grupo"""
    OWNER = "owner"
    ADMIN = "admin"
    HUNTER = "hunter"  # Miembro activo
    OBSERVER = "observer"  # Solo observa


@dataclass
class GroupMember:
    """Miembro de un grupo de caza"""
    user_id: int
    username: str
    role: str
    joined_at: str
    deals_contributed: int = 0
    points: int = 0
    last_active: Optional[str] = None


@dataclass
class HuntingGroup:
    """Grupo de caza de chollos"""
    group_id: str
    name: str
    description: str
    group_type: str
    owner_id: int
    created_at: str
    members: List[GroupMember] = field(default_factory=list)
    target_routes: List[str] = field(default_factory=list)
    max_price: Optional[float] = None
    min_savings_pct: float = 20.0
    is_active: bool = True
    total_deals_found: int = 0
    total_savings: float = 0.0
    invite_code: Optional[str] = None


@dataclass
class GroupDeal:
    """Deal encontrado por un grupo"""
    deal_id: str
    group_id: str
    found_by_user_id: int
    found_by_username: str
    route: str
    price: float
    currency: str
    savings_pct: float
    url: str
    found_at: str
    notified_members: Set[int] = field(default_factory=set)
    claimed_by: Set[int] = field(default_factory=set)


@dataclass
class GroupContribution:
    """Contribución de un miembro al grupo"""
    contribution_id: str
    group_id: str
    user_id: int
    username: str
    contribution_type: str  # deal_found, deal_claimed, member_invited
    points_earned: int
    timestamp: str
    details: Dict = field(default_factory=dict)


class GroupHuntingManager:
    """
    Gestor del sistema de caza grupal.
    
    Features:
    - Grupos públicos y privados
    - Sistema de puntos por contribución
    - Notificaciones grupales instantáneas
    - Pools para rutas específicas
    - Leaderboard interno por grupo
    """
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.groups_file = self.data_dir / "hunting_groups.json"
        self.deals_file = self.data_dir / "group_deals.json"
        self.contributions_file = self.data_dir / "group_contributions.json"
        self.analytics_file = self.data_dir / "group_analytics.json"
        
        self.groups: Dict[str, HuntingGroup] = {}
        self.deals: List[GroupDeal] = []
        self.contributions: List[GroupContribution] = []
        self.analytics: Dict = self._init_analytics()
        
        self._load_data()
    
    def _init_analytics(self) -> Dict:
        """Inicializa analytics"""
        return {
            "total_groups": 0,
            "total_members": 0,
            "total_deals_found": 0,
            "total_savings": 0.0,
            "avg_members_per_group": 0.0,
            "top_groups": [],
            "top_hunters": [],
            "most_popular_routes": [],
            "last_updated": datetime.now().isoformat()
        }
    
    def _load_data(self):
        """Carga datos"""
        if self.groups_file.exists():
            with open(self.groups_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.groups = {
                    k: HuntingGroup(**{**v, 'members': [GroupMember(**m) for m in v.get('members', [])]})
                    for k, v in data.items()
                }
        
        if self.deals_file.exists():
            with open(self.deals_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.deals = [
                    GroupDeal(**{**item, 'notified_members': set(item.get('notified_members', [])), 'claimed_by': set(item.get('claimed_by', []))})
                    for item in data
                ]
        
        if self.contributions_file.exists():
            with open(self.contributions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.contributions = [GroupContribution(**item) for item in data]
        
        if self.analytics_file.exists():
            with open(self.analytics_file, 'r', encoding='utf-8') as f:
                self.analytics = json.load(f)
    
    def _save_data(self):
        """Guarda datos"""
        with open(self.groups_file, 'w', encoding='utf-8') as f:
            data = {
                k: {**asdict(v), 'members': [asdict(m) for m in v.members]}
                for k, v in self.groups.items()
            }
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        with open(self.deals_file, 'w', encoding='utf-8') as f:
            data = [
                {**asdict(d), 'notified_members': list(d.notified_members), 'claimed_by': list(d.claimed_by)}
                for d in self.deals
            ]
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        with open(self.contributions_file, 'w', encoding='utf-8') as f:
            data = [asdict(c) for c in self.contributions]
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        with open(self.analytics_file, 'w', encoding='utf-8') as f:
            json.dump(self.analytics, f, indent=2, ensure_ascii=False)
    
    def create_group(
        self,
        name: str,
        description: str,
        owner_id: int,
        owner_username: str,
        group_type: GroupType = GroupType.PUBLIC,
        target_routes: List[str] = None,
        max_price: Optional[float] = None,
        min_savings_pct: float = 20.0
    ) -> HuntingGroup:
        """
        Crea un nuevo grupo de caza.
        """
        group_id = hashlib.md5(
            f"{name}{owner_id}{datetime.now()}".encode()
        ).hexdigest()[:12]
        
        # Generar invite code para grupos privados
        invite_code = None
        if group_type == GroupType.PRIVATE:
            invite_code = f"HUNT-{secrets.token_hex(4).upper()}"
        
        # Crear owner como primer miembro
        owner = GroupMember(
            user_id=owner_id,
            username=owner_username,
            role=MemberRole.OWNER.value,
            joined_at=datetime.now().isoformat()
        )
        
        group = HuntingGroup(
            group_id=group_id,
            name=name,
            description=description,
            group_type=group_type.value,
            owner_id=owner_id,
            created_at=datetime.now().isoformat(),
            members=[owner],
            target_routes=target_routes or [],
            max_price=max_price,
            min_savings_pct=min_savings_pct,
            invite_code=invite_code
        )
        
        self.groups[group_id] = group
        self.analytics["total_groups"] += 1
        self.analytics["total_members"] += 1
        
        self._save_data()
        
        return group
    
    def join_group(
        self,
        group_id: str,
        user_id: int,
        username: str,
        invite_code: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Un usuario se une a un grupo.
        
        Returns:
            (success, message)
        """
        if group_id not in self.groups:
            return False, "❌ Grupo no encontrado"
        
        group = self.groups[group_id]
        
        # Verificar si ya es miembro
        if any(m.user_id == user_id for m in group.members):
            return False, "❌ Ya eres miembro de este grupo"
        
        # Verificar invite code para grupos privados
        if group.group_type == GroupType.PRIVATE.value:
            if not invite_code or invite_code != group.invite_code:
                return False, "❌ Código de invitación inválido"
        
        # Añadir miembro
        member = GroupMember(
            user_id=user_id,
            username=username,
            role=MemberRole.HUNTER.value,
            joined_at=datetime.now().isoformat()
        )
        
        group.members.append(member)
        self.analytics["total_members"] += 1
        
        self._save_data()
        
        return True, f"✅ Te uniste al grupo '{group.name}'"
    
    def contribute_deal(
        self,
        group_id: str,
        user_id: int,
        username: str,
        route: str,
        price: float,
        currency: str,
        savings_pct: float,
        url: str
    ) -> Tuple[bool, str, Optional[GroupDeal]]:
        """
        Un miembro contribuye un deal al grupo.
        
        Returns:
            (success, message, deal)
        """
        if group_id not in self.groups:
            return False, "❌ Grupo no encontrado", None
        
        group = self.groups[group_id]
        
        # Verificar membresía
        member = next((m for m in group.members if m.user_id == user_id), None)
        if not member:
            return False, "❌ No eres miembro de este grupo", None
        
        # Crear deal
        deal_id = hashlib.md5(
            f"{group_id}{route}{price}{datetime.now()}".encode()
        ).hexdigest()[:12]
        
        deal = GroupDeal(
            deal_id=deal_id,
            group_id=group_id,
            found_by_user_id=user_id,
            found_by_username=username,
            route=route,
            price=price,
            currency=currency,
            savings_pct=savings_pct,
            url=url,
            found_at=datetime.now().isoformat()
        )
        
        self.deals.append(deal)
        
        # Actualizar stats del miembro
        member.deals_contributed += 1
        member.points += 100  # 100 puntos por deal
        member.last_active = datetime.now().isoformat()
        
        # Actualizar stats del grupo
        group.total_deals_found += 1
        group.total_savings += (savings_pct / 100) * price
        
        # Registrar contribución
        contribution = GroupContribution(
            contribution_id=hashlib.md5(
                f"{deal_id}{datetime.now()}".encode()
            ).hexdigest()[:12],
            group_id=group_id,
            user_id=user_id,
            username=username,
            contribution_type="deal_found",
            points_earned=100,
            timestamp=datetime.now().isoformat(),
            details={"deal_id": deal_id, "route": route, "savings_pct": savings_pct}
        )
        
        self.contributions.append(contribution)
        self.analytics["total_deals_found"] += 1
        self.analytics["total_savings"] += (savings_pct / 100) * price
        
        self._save_data()
        self._update_analytics()
        
        # Notificar a todos los miembros del grupo
        # (Esto se haría en el bot principal)
        
        return True, f"✅ Deal añadido al grupo '{group.name}'", deal
    
    def claim_deal(self, deal_id: str, user_id: int) -> Tuple[bool, str]:
        """
        Un usuario marca un deal como reclamado.
        """
        deal = next((d for d in self.deals if d.deal_id == deal_id), None)
        
        if not deal:
            return False, "❌ Deal no encontrado"
        
        # Verificar membresía en el grupo
        group = self.groups.get(deal.group_id)
        if not group or not any(m.user_id == user_id for m in group.members):
            return False, "❌ No eres miembro de este grupo"
        
        # Marcar como claimed
        deal.claimed_by.add(user_id)
        
        # Dar puntos al finder
        finder = next((m for m in group.members if m.user_id == deal.found_by_user_id), None)
        if finder:
            finder.points += 50  # 50 puntos adicionales
        
        self._save_data()
        
        return True, "✅ Deal marcado como reclamado"
    
    def get_group_leaderboard(self, group_id: str, limit: int = 10) -> List[Dict]:
        """
        Obtiene el leaderboard de un grupo.
        """
        if group_id not in self.groups:
            return []
        
        group = self.groups[group_id]
        
        leaderboard = sorted(
            [
                {
                    "username": m.username,
                    "points": m.points,
                    "deals_contributed": m.deals_contributed,
                    "role": m.role
                }
                for m in group.members
            ],
            key=lambda x: x["points"],
            reverse=True
        )[:limit]
        
        return leaderboard
    
    def get_user_groups(self, user_id: int) -> List[HuntingGroup]:
        """
        Obtiene todos los grupos de un usuario.
        """
        return [
            group for group in self.groups.values()
            if any(m.user_id == user_id for m in group.members)
        ]
    
    def search_groups(
        self,
        query: Optional[str] = None,
        group_type: Optional[GroupType] = None,
        target_route: Optional[str] = None
    ) -> List[HuntingGroup]:
        """
        Busca grupos públicos.
        """
        results = []
        
        for group in self.groups.values():
            # Solo grupos públicos
            if group.group_type != GroupType.PUBLIC.value:
                continue
            
            # Filtrar por query
            if query and query.lower() not in group.name.lower():
                continue
            
            # Filtrar por tipo
            if group_type and group.group_type != group_type.value:
                continue
            
            # Filtrar por ruta
            if target_route and target_route not in group.target_routes:
                continue
            
            results.append(group)
        
        return results
    
    def _update_analytics(self):
        """Actualiza analytics globales"""
        total_members = sum(len(g.members) for g in self.groups.values())
        total_groups = len(self.groups)
        
        if total_groups > 0:
            self.analytics["avg_members_per_group"] = total_members / total_groups
        
        # Top groups por deals encontrados
        self.analytics["top_groups"] = sorted(
            [
                {
                    "group_id": g.group_id,
                    "name": g.name,
                    "deals_found": g.total_deals_found,
                    "total_savings": g.total_savings,
                    "members": len(g.members)
                }
                for g in self.groups.values()
            ],
            key=lambda x: x["deals_found"],
            reverse=True
        )[:10]
        
        # Top hunters globales
        all_members = []
        for group in self.groups.values():
            all_members.extend(group.members)
        
        self.analytics["top_hunters"] = sorted(
            [
                {
                    "username": m.username,
                    "total_points": m.points,
                    "deals_contributed": m.deals_contributed
                }
                for m in all_members
            ],
            key=lambda x: x["total_points"],
            reverse=True
        )[:10]
        
        # Rutas más populares
        route_counts = {}
        for group in self.groups.values():
            for route in group.target_routes:
                route_counts[route] = route_counts.get(route, 0) + 1
        
        self.analytics["most_popular_routes"] = sorted(
            [{"route": k, "groups": v} for k, v in route_counts.items()],
            key=lambda x: x["groups"],
            reverse=True
        )[:10]
        
        self.analytics["last_updated"] = datetime.now().isoformat()
    
    def get_global_analytics(self) -> Dict:
        """Retorna analytics globales"""
        return self.analytics


if __name__ == "__main__":
    # Testing
    print("🚀 Testing Group Hunting System...")
    
    manager = GroupHuntingManager()
    
    # Crear grupo
    group = manager.create_group(
        name="Cazadores Madrid-Miami",
        description="Grupo para encontrar chollos MAD-MIA",
        owner_id=12345,
        owner_username="john_doe",
        group_type=GroupType.ROUTE_SPECIFIC,
        target_routes=["MAD-MIA"],
        max_price=500.0,
        min_savings_pct=25.0
    )
    
    print(f"\n✅ Grupo creado: {group.name}")
    print(f"   ID: {group.group_id}")
    print(f"   Tipo: {group.group_type}")
    print(f"   Miembros: {len(group.members)}")
    
    # Unirse al grupo
    success, msg = manager.join_group(
        group_id=group.group_id,
        user_id=67890,
        username="jane_smith"
    )
    print(f"\n{msg}")
    
    # Contribuir deal
    success, msg, deal = manager.contribute_deal(
        group_id=group.group_id,
        user_id=67890,
        username="jane_smith",
        route="MAD-MIA",
        price=450.0,
        currency="EUR",
        savings_pct=28.0,
        url="https://example.com/book"
    )
    print(f"\n{msg}")
    
    if deal:
        print(f"   Deal ID: {deal.deal_id}")
        print(f"   Ahorro: {deal.savings_pct}%")
    
    # Leaderboard
    leaderboard = manager.get_group_leaderboard(group.group_id)
    print(f"\n🏆 Leaderboard:")
    for i, entry in enumerate(leaderboard, 1):
        print(f"   {i}. {entry['username']}: {entry['points']} puntos")
    
    print("\n✅ Tests completados!")
