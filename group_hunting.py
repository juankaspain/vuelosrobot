#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
┌────────────────────────────────────────────────────────────────┐
│  👥 GROUP DEAL HUNTING - Collaborative Search            │
│  🚀 Cazador Supremo v13.1 Enterprise                          │
│  🎯 Target: 100+ Active Groups                            │
└────────────────────────────────────────────────────────────────┘

Sistema colaborativo de búsqueda de deals:
- Grupos privados
- Votación de deals
- Recompensas colectivas
- Gamification grupal

Autor: @Juanka_Spain
Version: 13.1.0
Date: 2026-01-14
"""

import json
import logging
import secrets
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class GroupRole(Enum):
    ADMIN = "admin"
    MEMBER = "member"


@dataclass
class HuntingGroup:
    group_id: str
    name: str
    created_by: int
    created_at: str
    members: Dict[int, str] = field(default_factory=dict)  # user_id -> role
    deals_shared: int = 0
    total_votes: int = 0
    level: int = 1
    coins_earned: float = 0.0
    is_active: bool = True


@dataclass
class GroupDeal:
    deal_id: str
    group_id: str
    shared_by: int
    route: str
    price: float
    timestamp: str
    votes: int = 0
    voters: List[int] = field(default_factory=list)
    comments: List[Dict] = field(default_factory=list)


class GroupHuntingManager:
    def __init__(self, groups_file: str = 'hunting_groups.json'):
        self.groups_file = Path(groups_file)
        self.groups: Dict[str, HuntingGroup] = {}
        self._load_data()
        logger.info("👥 GroupHuntingManager initialized")
    
    def _load_data(self):
        if self.groups_file.exists():
            try:
                with open(self.groups_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for group_id, group_data in data.items():
                    self.groups[group_id] = HuntingGroup(**group_data)
                logger.info(f"✅ Loaded {len(self.groups)} hunting groups")
            except Exception as e:
                logger.error(f"❌ Error loading groups: {e}")
    
    def _save_data(self):
        try:
            data = {gid: asdict(g) for gid, g in self.groups.items()}
            with open(self.groups_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Error saving groups: {e}")
    
    def create_group(self, name: str, creator_id: int) -> str:
        group_id = f"GRP_{secrets.token_hex(4).upper()}"
        group = HuntingGroup(
            group_id=group_id,
            name=name,
            created_by=creator_id,
            created_at=datetime.now().isoformat(),
            members={creator_id: GroupRole.ADMIN.value}
        )
        self.groups[group_id] = group
        self._save_data()
        logger.info(f"🎉 Group created: {group_id} - {name}")
        return group_id
    
    def add_member(self, group_id: str, user_id: int, role: GroupRole = GroupRole.MEMBER):
        if group_id in self.groups:
            self.groups[group_id].members[user_id] = role.value
            self._save_data()
    
    def share_deal(self, group_id: str, user_id: int, route: str, price: float) -> str:
        if group_id not in self.groups:
            return None
        
        deal_id = f"DEAL_{secrets.token_hex(4).upper()}"
        deal = GroupDeal(
            deal_id=deal_id,
            group_id=group_id,
            shared_by=user_id,
            route=route,
            price=price,
            timestamp=datetime.now().isoformat()
        )
        
        group = self.groups[group_id]
        group.deals_shared += 1
        group.coins_earned += 25  # Reward por compartir
        
        self._save_data()
        return deal_id


if __name__ == '__main__':
    print("✅ Group hunting module loaded")
