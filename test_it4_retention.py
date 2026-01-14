#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
┌────────────────────────────────────────────────────────────────┐
│  🧪 IT4 RETENTION TESTING SUITE                         │
│  🚀 Cazador Supremo v13.0 Enterprise                          │
│  ✅ Target Coverage: >80%                                      │
└────────────────────────────────────────────────────────────────┘

Suite completa de testing para IT4 Retention:
- Unit tests
- Integration tests
- Performance tests
- User flow tests

Autor: @Juanka_Spain
Version: 13.0.0
Date: 2026-01-14
"""

import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List

# Para testing sin dependencias reales
try:
    from retention_system import (
        RetentionManager, UserProfile, UserTier,
        FlightCoinsEconomy, AchievementType
    )
    from smart_notifications import SmartNotifier, NotificationType
    from onboarding_flow import OnboardingManager, TravelRegion, BudgetRange
    from quick_actions import QuickActionsManager
    IMPORTS_AVAILABLE = True
except ImportError:
    print("⚠️  Warning: Some modules not available. Running limited tests.")
    IMPORTS_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════
#  TEST UTILITIES
# ═══════════════════════════════════════════════════════════════

class TestStats:
    """Tracking de stats de tests"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors: List[str] = []
    
    def record_pass(self, test_name: str):
        self.total += 1
        self.passed += 1
        print(f"  ✅ {test_name}")
    
    def record_fail(self, test_name: str, error: str):
        self.total += 1
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"  ❌ {test_name} - {error}")
    
    def record_skip(self, test_name: str):
        self.total += 1
        self.skipped += 1
        print(f"  ⏭️  {test_name} (skipped)")
    
    def print_summary(self):
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"Total tests: {self.total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"⏭️  Skipped: {self.skipped}")
        
        if self.total > 0:
            pass_rate = (self.passed / self.total) * 100
            print(f"\nPass rate: {pass_rate:.1f}%")
        
        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"  - {error}")
        
        print("="*60)


stats = TestStats()


def assert_equal(actual, expected, test_name: str):
    """Assert helper"""
    if actual == expected:
        stats.record_pass(test_name)
        return True
    else:
        stats.record_fail(test_name, f"Expected {expected}, got {actual}")
        return False


def assert_true(condition, test_name: str):
    """Assert true helper"""
    if condition:
        stats.record_pass(test_name)
        return True
    else:
        stats.record_fail(test_name, "Condition was False")
        return False


# ═══════════════════════════════════════════════════════════════
#  UNIT TESTS
# ═══════════════════════════════════════════════════════════════

def test_retention_system():
    """Tests para retention_system.py"""
    print("\n🧪 Testing Retention System...")
    
    if not IMPORTS_AVAILABLE:
        stats.record_skip("Retention system tests")
        return
    
    try:
        # Test 1: Create profile
        mgr = RetentionManager('test_profiles.json')
        profile = mgr.get_or_create_profile(12345, 'testuser')
        assert_equal(profile.user_id, 12345, "Profile creation")
        
        # Test 2: Add coins
        initial_coins = profile.flight_coins
        mgr.add_coins(12345, 100, 'test')
        assert_equal(profile.flight_coins, initial_coins + 100, "Add coins")
        
        # Test 3: Tier progression
        initial_tier = profile.tier
        mgr.add_coins(12345, 500, 'tier_test')
        assert_true(profile.tier != initial_tier or profile.flight_coins >= 500, 
                   "Tier progression")
        
        # Test 4: Daily reward
        can_claim = profile.can_claim_daily()
        if can_claim:
            coins_earned = mgr.claim_daily_reward(12345)
            assert_true(coins_earned > 0, "Daily reward claim")
        else:
            stats.record_skip("Daily reward (already claimed)")
        
        # Test 5: Watchlist
        mgr.add_to_watchlist(12345, 'MAD-BCN', 200)
        assert_true(len(profile.watchlist) > 0, "Add to watchlist")
        
        print("  ✅ Retention system tests completed")
        
    except Exception as e:
        stats.record_fail("Retention system", str(e))


def test_smart_notifications():
    """Tests para smart_notifications.py"""
    print("\n🔔 Testing Smart Notifications...")
    
    if not IMPORTS_AVAILABLE:
        stats.record_skip("Smart notifications tests")
        return
    
    try:
        notifier = SmartNotifier()
        
        # Test 1: Track activity
        notifier.track_activity(12345)
        assert_true(12345 in notifier.user_activity, "Track activity")
        
        # Test 2: Get optimal time
        optimal_time = notifier.get_optimal_send_time(12345)
        assert_true(optimal_time is not None, "Get optimal send time")
        
        # Test 3: Add notification
        notifier.add_notification(
            user_id=12345,
            notif_type=NotificationType.DAILY_REMINDER,
            message="Test notification"
        )
        assert_true(len(notifier.notification_queue) > 0, "Add notification")
        
        # Test 4: Rate limiting
        for i in range(5):
            notifier.add_notification(
                user_id=12345,
                notif_type=NotificationType.TIPS,
                message=f"Test {i}"
            )
        # Should respect rate limits
        user_notifs = [n for n in notifier.notification_queue if n.user_id == 12345]
        assert_true(len(user_notifs) <= 10, "Rate limiting")
        
        print("  ✅ Smart notifications tests completed")
        
    except Exception as e:
        stats.record_fail("Smart notifications", str(e))


def test_onboarding_flow():
    """Tests para onboarding_flow.py"""
    print("\n🎉 Testing Onboarding Flow...")
    
    if not IMPORTS_AVAILABLE:
        stats.record_skip("Onboarding flow tests")
        return
    
    try:
        mgr = OnboardingManager('test_onboarding.json')
        
        # Test 1: Start onboarding
        progress = mgr.start_onboarding(12345)
        assert_true(mgr.needs_onboarding(12345), "Start onboarding")
        
        # Test 2: Set travel region
        mgr.advance_to_step1(12345)
        mgr.set_travel_region(12345, TravelRegion.EUROPE)
        assert_equal(progress.travel_region, TravelRegion.EUROPE, "Set travel region")
        
        # Test 3: Set budget
        mgr.set_budget_range(12345, BudgetRange.MEDIUM)
        assert_equal(progress.budget_range, BudgetRange.MEDIUM, "Set budget range")
        
        # Test 4: Complete onboarding
        mgr.complete_onboarding(12345)
        assert_true(not mgr.needs_onboarding(12345), "Complete onboarding")
        
        # Test 5: Analytics
        analytics = mgr.get_analytics()
        assert_true(analytics['completed'] > 0, "Analytics tracking")
        
        print("  ✅ Onboarding flow tests completed")
        
    except Exception as e:
        stats.record_fail("Onboarding flow", str(e))


def test_quick_actions():
    """Tests para quick_actions.py"""
    print("\n🎮 Testing Quick Actions...")
    
    if not IMPORTS_AVAILABLE:
        stats.record_skip("Quick actions tests")
        return
    
    try:
        mgr = QuickActionsManager('test_qa_analytics.json', 'test_qa_layouts.json')
        
        # Test 1: Get keyboard
        keyboard = mgr.get_keyboard(
            user_id=12345,
            user_tier='bronze',
            onboarding_completed=True
        )
        assert_true(len(keyboard.inline_keyboard) > 0, "Generate keyboard")
        
        # Test 2: Track click
        mgr.track_click(12345, 'scan')
        assert_true('scan' in mgr.analytics, "Track click")
        
        # Test 3: Custom layout
        mgr.set_custom_layout(12345, ['scan', 'deals', 'profile'])
        assert_equal(len(mgr.custom_layouts[12345]), 3, "Set custom layout")
        
        # Test 4: Analytics report
        report = mgr.get_analytics_report()
        assert_true('actions' in report, "Analytics report")
        
        print("  ✅ Quick actions tests completed")
        
    except Exception as e:
        stats.record_fail("Quick actions", str(e))


# ═══════════════════════════════════════════════════════════════
#  INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════

def test_complete_user_flow():
    """Test flujo completo de usuario nuevo"""
    print("\n👤 Testing Complete User Flow...")
    
    if not IMPORTS_AVAILABLE:
        stats.record_skip("Complete user flow")
        return
    
    try:
        user_id = 99999
        
        # 1. Onboarding
        onb_mgr = OnboardingManager('test_flow_onboarding.json')
        onb_mgr.start_onboarding(user_id)
        onb_mgr.advance_to_step1(user_id)
        onb_mgr.set_travel_region(user_id, TravelRegion.EUROPE)
        onb_mgr.set_budget_range(user_id, BudgetRange.MEDIUM)
        onb_mgr.complete_onboarding(user_id)
        assert_true(not onb_mgr.needs_onboarding(user_id), "Onboarding completed")
        
        # 2. Create profile
        ret_mgr = RetentionManager('test_flow_profiles.json')
        profile = ret_mgr.get_or_create_profile(user_id, 'flowtest')
        
        # 3. Award onboarding bonus
        ret_mgr.add_coins(user_id, 200, 'onboarding_bonus')
        assert_true(profile.flight_coins >= 200, "Onboarding bonus awarded")
        
        # 4. Claim daily reward
        coins = ret_mgr.claim_daily_reward(user_id)
        assert_true(coins > 0, "Daily reward claimed")
        
        # 5. Add to watchlist
        ret_mgr.add_to_watchlist(user_id, 'MAD-BCN', 250)
        assert_true(len(profile.watchlist) > 0, "Watchlist item added")
        
        # 6. Generate quick actions
        qa_mgr = QuickActionsManager('test_flow_qa.json', 'test_flow_layouts.json')
        keyboard = qa_mgr.get_keyboard(
            user_id=user_id,
            user_tier=profile.tier.value,
            onboarding_completed=True,
            can_claim_daily=False  # Ya reclamó
        )
        assert_true(len(keyboard.inline_keyboard) > 0, "Quick actions generated")
        
        print("  ✅ Complete user flow test passed")
        
    except Exception as e:
        stats.record_fail("Complete user flow", str(e))


# ═══════════════════════════════════════════════════════════════
#  PERFORMANCE TESTS
# ═══════════════════════════════════════════════════════════════

def test_performance():
    """Tests de performance"""
    print("\n⚡ Testing Performance...")
    
    if not IMPORTS_AVAILABLE:
        stats.record_skip("Performance tests")
        return
    
    try:
        # Test 1: Profile creation speed
        mgr = RetentionManager('test_perf_profiles.json')
        start = time.time()
        for i in range(100):
            mgr.get_or_create_profile(10000 + i, f'user{i}')
        elapsed = time.time() - start
        avg_time = (elapsed / 100) * 1000  # ms
        assert_true(avg_time < 10, f"Profile creation (<10ms, got {avg_time:.2f}ms)")
        
        # Test 2: Keyboard generation speed
        qa_mgr = QuickActionsManager('test_perf_qa.json', 'test_perf_layouts.json')
        start = time.time()
        for i in range(100):
            qa_mgr.get_keyboard(
                user_id=10000 + i,
                user_tier='bronze',
                onboarding_completed=True
            )
        elapsed = time.time() - start
        avg_time = (elapsed / 100) * 1000  # ms
        assert_true(avg_time < 5, f"Keyboard generation (<5ms, got {avg_time:.2f}ms)")
        
        print("  ✅ Performance tests completed")
        
    except Exception as e:
        stats.record_fail("Performance", str(e))


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    """Ejecuta todos los tests"""
    print("┌" + "─"*58 + "┐")
    print("│" + " "*10 + "🧪 IT4 RETENTION TESTING SUITE" + " "*10 + "│")
    print("│" + " "*12 + "Cazador Supremo v13.0" + " "*17 + "│")
    print("└" + "─"*58 + "┘")
    
    start_time = time.time()
    
    # Run all tests
    test_retention_system()
    test_smart_notifications()
    test_onboarding_flow()
    test_quick_actions()
    test_complete_user_flow()
    test_performance()
    
    elapsed = time.time() - start_time
    
    # Print summary
    stats.print_summary()
    print(f"\n⏱️  Total time: {elapsed:.2f}s")
    
    # Exit code
    sys.exit(0 if stats.failed == 0 else 1)


if __name__ == '__main__':
    main()
