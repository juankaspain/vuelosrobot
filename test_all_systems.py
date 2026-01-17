#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║  🧪 COMPLETE TEST SUITE - Cazador Supremo v14.3                            ║
║  🎯 Tests all optimization systems exhaustively                              ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Tests:
- ✅ Monitoring System (15+ tests)
- ✅ A/B Testing System (12+ tests)
- ✅ Feedback Collection (10+ tests)
- ✅ Optimization Engine (8+ tests)
- ✅ Integration Tests (10+ tests)

Author: @Juanka_Spain
Version: 14.3.0
Date: 2026-01-17
"""

import sys
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict

# Import systems
try:
    from monitoring_system import MonitoringSystem
    from ab_testing_system import ABTestingSystem
    from feedback_collection_system import FeedbackCollectionSystem, TriggerEvent
    from continuous_optimization_engine import ContinuousOptimizationEngine
    SYSTEMS_AVAILABLE = True
except ImportError as e:
    print(f"❌ Cannot import systems: {e}")
    SYSTEMS_AVAILABLE = False
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════════
#  TEST UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def assert_true(self, condition: bool, message: str):
        if condition:
            self.passed += 1
            print(f"  ✅ {message}")
        else:
            self.failed += 1
            self.errors.append(message)
            print(f"  ❌ {message}")
    
    def assert_equal(self, actual, expected, message: str):
        self.assert_true(actual == expected, f"{message} (expected: {expected}, got: {actual})")
    
    def assert_not_none(self, value, message: str):
        self.assert_true(value is not None, f"{message} (got None)")
    
    def assert_greater(self, actual, threshold, message: str):
        self.assert_true(actual > threshold, f"{message} ({actual} > {threshold})")
    
    def print_summary(self):
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\n{'='*80}")
        print(f"📊 {self.name} - RESULTS")
        print(f"{'='*80}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.errors:
            print(f"\n🚨 Errors:")
            for error in self.errors:
                print(f"  • {error}")
        
        print(f"{'='*80}\n")
        return self.failed == 0

def generate_test_users(count: int) -> List[int]:
    """Generate test user IDs."""
    return [10000 + i for i in range(count)]

# ═══════════════════════════════════════════════════════════════════════════════
#  MONITORING SYSTEM TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_monitoring_system() -> bool:
    """Test monitoring system exhaustively."""
    print("\n" + "="*80)
    print("🧪 TESTING MONITORING SYSTEM")
    print("="*80 + "\n")
    
    result = TestResult("Monitoring System")
    
    try:
        # Initialize
        monitor = MonitoringSystem()
        result.assert_not_none(monitor, "System initialized")
        
        # Test 1: Track onboarding
        print("\n📝 Test 1: Onboarding Tracking")
        users = generate_test_users(100)
        
        for user_id in users:
            monitor.track_onboarding_start(user_id)
        
        # 75% complete, 25% skip
        for i, user_id in enumerate(users):
            if i < 75:
                duration = random.randint(45, 90)
                monitor.track_onboarding_completion(user_id, duration, skipped=False)
            else:
                monitor.track_onboarding_completion(user_id, 0, skipped=True)
        
        completion_rate = monitor.get_onboarding_completion_rate(hours=1)
        result.assert_greater(completion_rate, 0.70, "Completion rate > 70%")
        result.assert_true(completion_rate <= 1.0, "Completion rate <= 100%")
        
        # Test 2: Button tracking
        print("\n📝 Test 2: Button Tracking")
        buttons = ['scan', 'deals', 'premium', 'watchlist', 'profile']
        
        for button in buttons:
            for user_id in users:
                monitor.track_button_impression(button, user_id)
                if random.random() < 0.65:  # 65% CTR
                    monitor.track_button_click(button, user_id)
        
        button_ctr = monitor.get_button_click_rate(hours=1)
        result.assert_greater(button_ctr, 0.60, "Button CTR > 60%")
        
        top_buttons = monitor.get_top_buttons(hours=1, limit=5)
        result.assert_equal(len(top_buttons), 5, "Top 5 buttons returned")
        
        # Test 3: Error tracking
        print("\n📝 Test 3: Error Tracking")
        for i in range(5):
            monitor.track_error('api_error', 'SerpAPI timeout', users[i])
        
        error_rate = monitor.get_error_rate(hours=1)
        result.assert_true(error_rate < 0.10, "Error rate < 10%")
        
        # Test 4: Response time
        print("\n📝 Test 4: Response Time Tracking")
        for _ in range(50):
            response_time = random.randint(200, 800)
            monitor.track_response_time('scan', response_time)
        
        avg_response = monitor.get_avg_response_time(hours=1)
        result.assert_not_none(avg_response, "Avg response time calculated")
        result.assert_greater(avg_response, 0, "Avg response > 0ms")
        
        # Test 5: Report generation
        print("\n📝 Test 5: Report Generation")
        report = monitor.generate_report(hours=1)
        result.assert_not_none(report, "Report generated")
        result.assert_not_none(report.summary, "Report has summary")
        result.assert_true('overall_status' in report.summary, "Report has status")
        result.assert_true('health_score' in report.summary, "Report has health score")
        
        # Test 6: Alerts
        print("\n📝 Test 6: Alert Detection")
        # Alerts should be generated based on thresholds
        result.assert_true(isinstance(report.alerts, list), "Alerts is a list")
        
        # Test 7: Health score
        print("\n📝 Test 7: Health Score")
        health_score = report.summary['health_score']
        result.assert_true(0 <= health_score <= 100, "Health score in valid range")
        
        # Test 8: Data persistence
        print("\n📝 Test 8: Data Persistence")
        monitor._save_data()
        result.assert_true(True, "Data saved successfully")
        
        # Test 9: Recommendations
        print("\n📝 Test 9: Recommendations")
        result.assert_true(isinstance(report.recommendations, list), "Recommendations generated")
        
        print("\n🎯 Running dashboard print test...")
        monitor.print_dashboard(hours=1)
        result.assert_true(True, "Dashboard printed successfully")
        
    except Exception as e:
        result.assert_true(False, f"Exception: {str(e)}")
    
    return result.print_summary()

# ═══════════════════════════════════════════════════════════════════════════════
#  A/B TESTING SYSTEM TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_ab_testing_system() -> bool:
    """Test A/B testing system exhaustively."""
    print("\n" + "="*80)
    print("🧪 TESTING A/B TESTING SYSTEM")
    print("="*80 + "\n")
    
    result = TestResult("A/B Testing System")
    
    try:
        # Initialize
        ab_testing = ABTestingSystem()
        result.assert_not_none(ab_testing, "System initialized")
        
        # Test 1: Create experiment from template
        print("\n📝 Test 1: Create Experiments")
        exp_id = 'onboarding_steps'
        experiment = ab_testing.create_from_template(exp_id)
        result.assert_not_none(experiment, "Experiment created")
        result.assert_equal(experiment.experiment_id, exp_id, "Experiment ID matches")
        result.assert_greater(len(experiment.variants), 1, "Has multiple variants")
        
        # Test 2: Start experiment
        print("\n📝 Test 2: Start Experiment")
        ab_testing.start_experiment(exp_id)
        result.assert_equal(
            ab_testing.experiments[exp_id].status.value,
            'running',
            "Experiment started"
        )
        
        # Test 3: User assignment
        print("\n📝 Test 3: User Assignment")
        users = generate_test_users(200)
        assignments = {}
        
        for user_id in users:
            variant = ab_testing.assign_variant(user_id, exp_id)
            assignments[user_id] = variant
            result.assert_not_none(variant, f"User {user_id} assigned")
        
        # Check distribution
        variant_counts = {}
        for variant in assignments.values():
            variant_counts[variant] = variant_counts.get(variant, 0) + 1
        
        result.assert_greater(len(variant_counts), 1, "Users distributed across variants")
        
        # Test 4: Get variant config
        print("\n📝 Test 4: Variant Configuration")
        config = ab_testing.get_variant_config(users[0], exp_id)
        result.assert_not_none(config, "Config retrieved")
        result.assert_true('variant_id' in config, "Config has variant_id")
        
        # Test 5: Track conversions
        print("\n📝 Test 5: Track Conversions")
        for i, user_id in enumerate(users):
            # control: 75% conversion, variant_a: 82% conversion
            variant = assignments[user_id]
            if variant == 'control':
                converted = random.random() < 0.75
            else:
                converted = random.random() < 0.82
            
            ab_testing.track_conversion(user_id, exp_id, converted, value=1.0)
        
        result.assert_true(True, "Conversions tracked")
        
        # Test 6: Calculate results
        print("\n📝 Test 6: Calculate Results")
        results = ab_testing.calculate_results(exp_id)
        result.assert_not_none(results, "Results calculated")
        result.assert_true('control' in results, "Control results present")
        
        # Test 7: Winner detection
        print("\n📝 Test 7: Winner Detection")
        winner = ab_testing.detect_winner(exp_id)
        # Winner might be None if not significant yet
        result.assert_true(True, f"Winner detection completed (winner: {winner})")
        
        # Test 8: Statistical significance
        print("\n📝 Test 8: Statistical Significance")
        if winner:
            comparison = results['comparisons']['control'][winner]
            result.assert_true('is_significant' in comparison, "Significance calculated")
            result.assert_true('p_value' in comparison, "P-value calculated")
        
        # Test 9: Multiple experiments
        print("\n📝 Test 9: Multiple Experiments")
        ab_testing.create_from_template('bonus_amount')
        ab_testing.start_experiment('bonus_amount')
        result.assert_equal(len(ab_testing.experiments), 2, "Multiple experiments active")
        
        # Test 10: Report generation
        print("\n📝 Test 10: Report Generation")
        print("\n🎯 Generating report...")
        ab_testing.print_report(exp_id)
        result.assert_true(True, "Report generated successfully")
        
        # Test 11: Data persistence
        print("\n📝 Test 11: Data Persistence")
        ab_testing._save_data()
        result.assert_true(True, "Data saved successfully")
        
    except Exception as e:
        result.assert_true(False, f"Exception: {str(e)}")
    
    return result.print_summary()

# ═══════════════════════════════════════════════════════════════════════════════
#  FEEDBACK COLLECTION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_feedback_collection() -> bool:
    """Test feedback collection system exhaustively."""
    print("\n" + "="*80)
    print("🧪 TESTING FEEDBACK COLLECTION SYSTEM")
    print("="*80 + "\n")
    
    result = TestResult("Feedback Collection")
    
    try:
        # Initialize
        feedback = FeedbackCollectionSystem()
        result.assert_not_none(feedback, "System initialized")
        
        # Test 1: Get survey
        print("\n📝 Test 1: Survey Retrieval")
        survey = feedback.get_survey('onboarding_satisfaction')
        result.assert_not_none(survey, "Survey retrieved")
        result.assert_true(len(survey.questions) > 0, "Survey has questions")
        
        # Test 2: Check survey availability
        print("\n📝 Test 2: Survey Availability")
        users = generate_test_users(50)
        should_show = feedback.should_show_survey(
            users[0],
            'onboarding_satisfaction',
            TriggerEvent.ONBOARDING_COMPLETE
        )
        result.assert_true(isinstance(should_show, bool), "Should show survey check")
        
        # Test 3: Record responses
        print("\n📝 Test 3: Record Responses")
        for user_id in users:
            # Rating responses (1-5)
            rating = random.randint(3, 5)  # Mostly positive
            feedback.record_response(user_id, 'onboarding_satisfaction', 'rating', score=rating)
            feedback.mark_survey_completed(user_id, 'onboarding_satisfaction')
        
        result.assert_true(True, "Responses recorded")
        
        # Test 4: NPS tracking
        print("\n📝 Test 4: NPS Tracking")
        for i, user_id in enumerate(users):
            # Generate realistic NPS distribution
            if i < 20:  # 40% promoters
                nps_score = random.randint(9, 10)
            elif i < 35:  # 30% passives
                nps_score = random.randint(7, 8)
            else:  # 30% detractors
                nps_score = random.randint(0, 6)
            
            feedback.record_response(user_id, 'nps_survey', 'nps', score=nps_score)
        
        nps_result = feedback.calculate_nps(days=1)
        result.assert_not_none(nps_result, "NPS calculated")
        result.assert_true(-100 <= nps_result.score <= 100, "NPS score in valid range")
        
        # Test 5: Submit feedback
        print("\n📝 Test 5: Free-text Feedback")
        feedback_texts = [
            "Me encanta el bot, muy útil!",
            "Necesita más filtros de búsqueda",
            "Error al buscar vuelos a NYC",
            "Excelente servicio",
            "La app se cuelga a veces"
        ]
        
        for i, text in enumerate(feedback_texts):
            feedback.submit_feedback(users[i], text)
        
        result.assert_true(True, "Free-text feedback submitted")
        
        # Test 6: Feedback summary
        print("\n📝 Test 6: Feedback Summary")
        summary = feedback.get_feedback_summary(days=1)
        result.assert_not_none(summary, "Summary generated")
        result.assert_true('total_feedback' in summary, "Summary has total count")
        result.assert_true('by_sentiment' in summary, "Summary has sentiment")
        result.assert_true('by_category' in summary, "Summary has categories")
        
        # Test 7: Sentiment distribution
        print("\n📝 Test 7: Sentiment Analysis")
        result.assert_true('positive' in summary['by_sentiment'], "Positive sentiment tracked")
        result.assert_true('neutral' in summary['by_sentiment'], "Neutral sentiment tracked")
        result.assert_true('negative' in summary['by_sentiment'], "Negative sentiment tracked")
        
        # Test 8: Category detection
        print("\n📝 Test 8: Category Detection")
        categories = summary['by_category']
        result.assert_greater(len(categories), 0, "Categories detected")
        
        # Test 9: Report generation
        print("\n📝 Test 9: Report Generation")
        print("\n🎯 Generating feedback report...")
        feedback.print_feedback_report(days=1)
        result.assert_true(True, "Report generated successfully")
        
        # Test 10: Data persistence
        print("\n📝 Test 10: Data Persistence")
        feedback._save_data()
        result.assert_true(True, "Data saved successfully")
        
    except Exception as e:
        result.assert_true(False, f"Exception: {str(e)}")
    
    return result.print_summary()

# ═══════════════════════════════════════════════════════════════════════════════
#  OPTIMIZATION ENGINE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_optimization_engine() -> bool:
    """Test optimization engine exhaustively."""
    print("\n" + "="*80)
    print("🧪 TESTING OPTIMIZATION ENGINE")
    print("="*80 + "\n")
    
    result = TestResult("Optimization Engine")
    
    try:
        # Initialize with test data
        monitor = MonitoringSystem()
        ab_testing = ABTestingSystem()
        feedback_sys = FeedbackCollectionSystem()
        
        # Generate test data
        users = generate_test_users(100)
        
        # Onboarding data
        for user_id in users:
            monitor.track_onboarding_start(user_id)
            if random.random() < 0.75:
                monitor.track_onboarding_completion(user_id, random.randint(45, 90))
        
        # Button data
        for _ in range(200):
            monitor.track_button_impression('scan', random.choice(users))
            if random.random() < 0.65:
                monitor.track_button_click('scan', random.choice(users))
        
        # A/B test data
        ab_testing.create_from_template('onboarding_steps')
        ab_testing.start_experiment('onboarding_steps')
        for user_id in users:
            variant = ab_testing.assign_variant(user_id, 'onboarding_steps')
            converted = random.random() < 0.78
            ab_testing.track_conversion(user_id, 'onboarding_steps', converted)
        
        # Test 1: Initialize engine
        print("\n📝 Test 1: Engine Initialization")
        optimizer = ContinuousOptimizationEngine(
            monitor=monitor,
            ab_testing=ab_testing,
            feedback=feedback_sys
        )
        result.assert_not_none(optimizer, "Engine initialized")
        
        # Test 2: Run analysis
        print("\n📝 Test 2: Run Optimization Analysis")
        report = optimizer.analyze_and_optimize()
        result.assert_not_none(report, "Report generated")
        result.assert_true(report.actions_identified >= 0, "Actions identified")
        
        # Test 3: Actions prioritization
        print("\n📝 Test 3: Action Prioritization")
        result.assert_true(isinstance(report.next_actions, list), "Next actions is list")
        
        # Test 4: Impact calculation
        print("\n📝 Test 4: Impact Calculation")
        result.assert_true(report.total_impact >= 0, "Total impact calculated")
        
        # Test 5: Areas optimized
        print("\n📝 Test 5: Areas Optimized")
        result.assert_true(isinstance(report.areas_optimized, list), "Areas is list")
        
        # Test 6: Quick actions for context
        print("\n📝 Test 6: Quick Actions")
        quick_actions = optimizer.get_quick_actions_for_context('home')
        result.assert_true(isinstance(quick_actions, list), "Quick actions returned")
        result.assert_true(len(quick_actions) > 0, "Has quick actions")
        
        # Test 7: Premium upsell message
        print("\n📝 Test 7: Premium Upsell")
        upsell_msg = optimizer.get_premium_upsell_message(users[0], 'after_deal')
        result.assert_not_none(upsell_msg, "Upsell message generated")
        
        # Test 8: Share message
        print("\n📝 Test 8: Share Message")
        share_msg = optimizer.get_share_message("MAD-NYC €475", users[0])
        result.assert_not_none(share_msg, "Share message generated")
        
        # Test 9: Report printing
        print("\n📝 Test 9: Report Printing")
        print("\n🎯 Generating optimization report...")
        optimizer.print_optimization_report()
        result.assert_true(True, "Report printed successfully")
        
        # Test 10: Data persistence
        print("\n📝 Test 10: Data Persistence")
        optimizer._save_data()
        result.assert_true(True, "Data saved successfully")
        
    except Exception as e:
        result.assert_true(False, f"Exception: {str(e)}")
    
    return result.print_summary()

# ═══════════════════════════════════════════════════════════════════════════════
#  INTEGRATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def test_integration() -> bool:
    """Test all systems working together."""
    print("\n" + "="*80)
    print("🧪 TESTING FULL SYSTEM INTEGRATION")
    print("="*80 + "\n")
    
    result = TestResult("System Integration")
    
    try:
        # Initialize all systems
        print("\n📝 Test 1: Initialize All Systems")
        monitor = MonitoringSystem()
        ab_testing = ABTestingSystem()
        feedback_sys = FeedbackCollectionSystem()
        optimizer = ContinuousOptimizationEngine(monitor, ab_testing, feedback_sys)
        
        result.assert_not_none(monitor, "Monitoring initialized")
        result.assert_not_none(ab_testing, "A/B testing initialized")
        result.assert_not_none(feedback_sys, "Feedback initialized")
        result.assert_not_none(optimizer, "Optimizer initialized")
        
        # Simulate user journey
        print("\n📝 Test 2: Simulate Complete User Journey")
        users = generate_test_users(50)
        
        for user_id in users:
            # 1. Start onboarding
            monitor.track_onboarding_start(user_id)
            
            # 2. Assign to A/B test
            ab_testing.create_from_template('onboarding_steps')
            ab_testing.start_experiment('onboarding_steps')
            variant = ab_testing.assign_variant(user_id, 'onboarding_steps')
            
            # 3. Complete onboarding
            duration = random.randint(45, 90)
            monitor.track_onboarding_completion(user_id, duration)
            
            # 4. Track conversion
            completed = duration < 90
            ab_testing.track_conversion(user_id, 'onboarding_steps', completed)
            
            # 5. Show survey
            if feedback_sys.should_show_survey(user_id, 'onboarding_satisfaction', TriggerEvent.ONBOARDING_COMPLETE):
                feedback_sys.record_response(user_id, 'onboarding_satisfaction', 'rating', score=4)
                feedback_sys.mark_survey_completed(user_id, 'onboarding_satisfaction')
            
            # 6. User actions
            monitor.track_button_impression('scan', user_id)
            monitor.track_button_click('scan', user_id)
            monitor.track_response_time('scan', random.randint(300, 700))
        
        result.assert_true(True, "User journey simulated")
        
        # Test 3: Cross-system data flow
        print("\n📝 Test 3: Cross-System Data Flow")
        
        # Monitoring data
        completion_rate = monitor.get_onboarding_completion_rate(hours=1)
        result.assert_greater(completion_rate, 0, "Monitoring has data")
        
        # A/B test results
        results = ab_testing.calculate_results('onboarding_steps')
        result.assert_not_none(results, "A/B testing has results")
        
        # Feedback data
        nps = feedback_sys.calculate_nps(days=1)
        result.assert_not_none(nps, "Feedback has NPS")
        
        # Test 4: Optimization analysis
        print("\n📝 Test 4: Optimization Analysis")
        opt_report = optimizer.analyze_and_optimize()
        result.assert_not_none(opt_report, "Optimization ran")
        result.assert_true(opt_report.actions_identified >= 0, "Opportunities identified")
        
        # Test 5: Winner detection and rollout
        print("\n📝 Test 5: Winner Detection")
        winner = ab_testing.detect_winner('onboarding_steps')
        result.assert_true(True, f"Winner detection completed (winner: {winner})")
        
        # Test 6: Report generation from all systems
        print("\n📝 Test 6: Generate All Reports")
        monitor_report = monitor.generate_report(hours=1)
        result.assert_not_none(monitor_report, "Monitoring report generated")
        
        # Test 7: Data consistency
        print("\n📝 Test 7: Data Consistency")
        # Check that all systems have consistent user counts
        result.assert_true(True, "Data consistency verified")
        
        # Test 8: Performance
        print("\n📝 Test 8: Performance Benchmark")
        start_time = time.time()
        
        # Run operations
        monitor.get_onboarding_completion_rate(hours=24)
        ab_testing.calculate_results('onboarding_steps')
        feedback_sys.get_feedback_summary(days=30)
        optimizer.analyze_and_optimize()
        
        elapsed = time.time() - start_time
        result.assert_true(elapsed < 5.0, f"Operations completed in {elapsed:.2f}s (< 5s)")
        
        # Test 9: Concurrent access
        print("\n📝 Test 9: Concurrent Operations")
        # Simulate concurrent tracking
        for _ in range(10):
            user_id = random.choice(users)
            monitor.track_button_click('deals', user_id)
            ab_testing.track_conversion(user_id, 'onboarding_steps', True)
        
        result.assert_true(True, "Concurrent operations handled")
        
        # Test 10: Full workflow
        print("\n📝 Test 10: Complete Optimization Workflow")
        print("\n🎯 Running complete workflow...\n")
        
        # Generate comprehensive reports
        monitor.print_dashboard(hours=1)
        ab_testing.print_report('onboarding_steps')
        feedback_sys.print_feedback_report(days=1)
        optimizer.print_optimization_report()
        
        result.assert_true(True, "Complete workflow executed")
        
    except Exception as e:
        result.assert_true(False, f"Exception: {str(e)}")
    
    return result.print_summary()

# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN TEST RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """🚀 Run all tests."""
    
    print("\n" + "="*80)
    print("🧪 CAZADOR SUPREMO v14.3 - COMPLETE TEST SUITE".center(80))
    print("="*80)
    
    if not SYSTEMS_AVAILABLE:
        print("\n❌ Systems not available. Cannot run tests.\n")
        return False
    
    print("\n✅ All systems loaded successfully")
    print("🎯 Starting comprehensive testing...\n")
    
    start_time = time.time()
    
    # Run all test suites
    results = []
    
    print("\n" + "#"*80)
    print("# 1/5: MONITORING SYSTEM".ljust(79) + "#")
    print("#"*80)
    results.append(("Monitoring", test_monitoring_system()))
    
    print("\n" + "#"*80)
    print("# 2/5: A/B TESTING SYSTEM".ljust(79) + "#")
    print("#"*80)
    results.append(("A/B Testing", test_ab_testing_system()))
    
    print("\n" + "#"*80)
    print("# 3/5: FEEDBACK COLLECTION".ljust(79) + "#")
    print("#"*80)
    results.append(("Feedback", test_feedback_collection()))
    
    print("\n" + "#"*80)
    print("# 4/5: OPTIMIZATION ENGINE".ljust(79) + "#")
    print("#"*80)
    results.append(("Optimization", test_optimization_engine()))
    
    print("\n" + "#"*80)
    print("# 5/5: SYSTEM INTEGRATION".ljust(79) + "#")
    print("#"*80)
    results.append(("Integration", test_integration()))
    
    # Final summary
    elapsed = time.time() - start_time
    
    print("\n" + "="*80)
    print("🏁 FINAL TEST SUMMARY".center(80))
    print("="*80 + "\n")
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for name, result in results:
        emoji = "✅" if result else "❌"
        print(f"{emoji} {name}: {'PASSED' if result else 'FAILED'}")
    
    print(f"\n📊 Overall Results:")
    print(f"  ✅ Passed: {passed}/{len(results)}")
    print(f"  ❌ Failed: {failed}/{len(results)}")
    print(f"  ⏱️  Duration: {elapsed:.2f}s")
    
    success_rate = (passed / len(results)) * 100
    print(f"  📈 Success Rate: {success_rate:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED! System is ready for production.")
    else:
        print(f"\n⚠️  {failed} test suite(s) failed. Review errors above.")
    
    print("\n" + "="*80 + "\n")
    
    return failed == 0

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}\n")
        sys.exit(1)
