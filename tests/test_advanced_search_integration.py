#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration Tests for Advanced Search Methods
Cazador Supremo v14.0

Tests the full integration of advanced search methods with Telegram bot

Author: @Juanka_Spain
Version: 14.0.0
Date: 2026-01-17
"""

import unittest
import sys
import os
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from advanced_search_methods import (
        SearchMethodFactory,
        FlexibleDatesCalendar,
        MultiCitySearch,
        BudgetSearch,
        FlightResult,
        SearchResult
    )
    from advanced_search_commands import (
        AdvancedSearchCommandHandler,
        get_advanced_search_menu
    )
    MODULES_AVAILABLE = True
except ImportError as e:
    MODULES_AVAILABLE = False
    print(f"Warning: Could not import modules: {e}")


class TestAdvancedSearchMethods(unittest.TestCase):
    """Test core search method functionality"""
    
    def setUp(self):
        if not MODULES_AVAILABLE:
            self.skipTest("Modules not available")
        self.factory = SearchMethodFactory()
    
    def test_factory_creates_methods(self):
        """Test that factory can create all method types"""
        methods = [
            'flexible_dates',
            'multi_city',
            'budget',
            'airline_specific',
            'nonstop_only',
            'redeye',
            'nearby_airports',
            'lastminute',
            'seasonal_trends',
            'group_booking'
        ]
        
        for method_name in methods:
            method = self.factory.create(method_name)
            self.assertIsNotNone(method)
            print(f"✅ Factory created: {method_name}")
    
    def test_flexible_dates_calendar(self):
        """Test flexible dates calendar search"""
        calendar = FlexibleDatesCalendar()
        result = calendar.search(
            origin='MAD',
            destination='MIA',
            month='2026-03'
        )
        
        self.assertIsInstance(result, SearchResult)
        self.assertEqual(result.method, 'flexible_dates_calendar')
        self.assertIn('prices', result.metadata)
        self.assertIn('stats', result.metadata)
        self.assertIn('best_day', result.metadata)
        
        # Test output formatting
        output = calendar.format_output(result)
        self.assertIn('CALENDARIO DE PRECIOS', output)
        self.assertIn('MAD', output)
        self.assertIn('MIA', output)
        
        print("✅ FlexibleDatesCalendar test passed")
    
    def test_multi_city_search(self):
        """Test multi-city search"""
        multi_city = MultiCitySearch()
        result = multi_city.search(
            cities=['MAD', 'PAR', 'AMS', 'BER', 'MAD'],
            start_date='2026-06-01',
            stay_days=[2, 2, 2]
        )
        
        self.assertIsInstance(result, SearchResult)
        self.assertEqual(result.method, 'multi_city_search')
        self.assertTrue(len(result.results) > 0)
        self.assertIn('total_price', result.metadata)
        self.assertIn('savings', result.metadata)
        
        # Test output
        output = multi_city.format_output(result)
        self.assertIn('ITINERARIO OPTIMIZADO', output)
        self.assertIn('RESUMEN', output)
        
        print("✅ MultiCitySearch test passed")
    
    def test_budget_search(self):
        """Test budget search"""
        budget_search = BudgetSearch()
        result = budget_search.search(
            origin='MAD',
            budget=500,
            month='2026-07'
        )
        
        self.assertIsInstance(result, SearchResult)
        self.assertEqual(result.method, 'budget_search')
        self.assertTrue(len(result.results) > 0)
        self.assertIn('by_country', result.metadata)
        
        # Verify all results are within budget
        for dest in result.results:
            self.assertLessEqual(dest['price'], 500)
        
        # Test output
        output = budget_search.format_output(result)
        self.assertIn('DESTINOS DENTRO DE', output)
        
        print("✅ BudgetSearch test passed")


class TestCommandHandler(unittest.TestCase):
    """Test Telegram command handler"""
    
    def setUp(self):
        if not MODULES_AVAILABLE:
            self.skipTest("Modules not available")
        self.handler = AdvancedSearchCommandHandler()
    
    def test_handler_initialization(self):
        """Test handler initializes correctly"""
        self.assertIsNotNone(self.handler)
        self.assertIsNotNone(self.handler.factory)
        self.assertIsInstance(self.handler.active_searches, dict)
        print("✅ Handler initialization test passed")
    
    def test_iata_validation(self):
        """Test IATA code validation"""
        valid_codes = ['MAD', 'BCN', 'NYC', 'LAX']
        invalid_codes = ['MADR', 'BC', '123', 'mad', '']
        
        for code in valid_codes:
            self.assertTrue(self.handler._validate_iata(code))
        
        for code in invalid_codes:
            self.assertFalse(self.handler._validate_iata(code))
        
        print("✅ IATA validation test passed")
    
    def test_date_validation(self):
        """Test date validation"""
        valid_dates = ['2026-01-15', '2026-12-31', '2026-06-01']
        invalid_dates = ['2026-13-01', '2026-01-32', '26-01-15', 'invalid']
        
        for date in valid_dates:
            self.assertTrue(self.handler._validate_date(date))
        
        for date in invalid_dates:
            self.assertFalse(self.handler._validate_date(date))
        
        print("✅ Date validation test passed")
    
    def test_month_validation(self):
        """Test month validation"""
        valid_months = ['2026-01', '2026-12', '2027-06']
        invalid_months = ['2026-13', '2026-00', '26-01', 'invalid']
        
        for month in valid_months:
            self.assertTrue(self.handler._validate_month(month))
        
        for month in invalid_months:
            self.assertFalse(self.handler._validate_month(month))
        
        print("✅ Month validation test passed")


class TestMenuGeneration(unittest.TestCase):
    """Test menu generation"""
    
    def test_get_advanced_search_menu(self):
        """Test that menu is generated correctly"""
        if not MODULES_AVAILABLE:
            self.skipTest("Modules not available")
        
        menu = get_advanced_search_menu()
        self.assertIsNotNone(menu)
        
        # Should have 5 rows with 2 buttons each
        self.assertEqual(len(menu.inline_keyboard), 5)
        for row in menu.inline_keyboard:
            self.assertEqual(len(row), 2)
        
        print("✅ Menu generation test passed")


class TestEndToEndScenarios(unittest.TestCase):
    """Test complete user scenarios"""
    
    def setUp(self):
        if not MODULES_AVAILABLE:
            self.skipTest("Modules not available")
        self.handler = AdvancedSearchCommandHandler()
    
    def test_flexible_dates_scenario(self):
        """Test complete flexible dates search flow"""
        # Create search
        calendar = self.handler.factory.create('flexible_dates')
        result = calendar.search('MAD', 'MIA', '2026-03')
        
        # Verify result structure
        self.assertIn('prices', result.metadata)
        self.assertIn('stats', result.metadata)
        self.assertIn('best_day', result.metadata)
        
        best_day = result.metadata['best_day']
        self.assertIn('day', best_day)
        self.assertIn('price', best_day)
        
        # Verify best day is actually the minimum
        prices = result.metadata['prices']
        min_price = min(p for p in prices.values() if p > 0)
        self.assertEqual(best_day['price'], min_price)
        
        print("✅ Flexible dates scenario test passed")
    
    def test_multi_city_scenario(self):
        """Test complete multi-city search flow"""
        # Create search
        multi_city = self.handler.factory.create('multi_city')
        result = multi_city.search(
            cities=['MAD', 'PAR', 'AMS', 'MAD'],
            start_date='2026-06-01',
            stay_days=[3, 3]
        )
        
        # Verify segments
        segments = result.results
        self.assertEqual(len(segments), 3)  # 3 flights for 4 cities
        
        # Verify savings calculation
        metadata = result.metadata
        self.assertGreater(metadata['separate_price'], metadata['total_price'])
        self.assertGreater(metadata['savings'], 0)
        
        print("✅ Multi-city scenario test passed")
    
    def test_budget_search_scenario(self):
        """Test complete budget search flow"""
        # Create search
        budget_search = self.handler.factory.create('budget')
        result = budget_search.search('MAD', 300, '2026-07')
        
        # All results should be within budget
        for dest in result.results:
            self.assertLessEqual(dest['price'], 300)
        
        # Should have country grouping
        by_country = result.metadata['by_country']
        self.assertGreater(len(by_country), 0)
        
        print("✅ Budget search scenario test passed")


class TestPerformance(unittest.TestCase):
    """Test performance characteristics"""
    
    def setUp(self):
        if not MODULES_AVAILABLE:
            self.skipTest("Modules not available")
        self.factory = SearchMethodFactory()
    
    def test_search_response_time(self):
        """Test that searches complete quickly"""
        import time
        
        # Test flexible dates
        start = time.time()
        calendar = self.factory.create('flexible_dates')
        result = calendar.search('MAD', 'MIA', '2026-03')
        duration = time.time() - start
        
        self.assertLess(duration, 2.0, "Search should complete in under 2 seconds")
        print(f"✅ Flexible dates completed in {duration:.3f}s")
        
        # Test multi-city
        start = time.time()
        multi_city = self.factory.create('multi_city')
        result = multi_city.search(['MAD', 'PAR', 'AMS', 'MAD'], '2026-06-01', [2, 2])
        duration = time.time() - start
        
        self.assertLess(duration, 2.0, "Search should complete in under 2 seconds")
        print(f"✅ Multi-city completed in {duration:.3f}s")


def run_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("ADVANCED SEARCH INTEGRATION TESTS - v14.0")
    print("="*70 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestAdvancedSearchMethods))
    suite.addTests(loader.loadTestsFromTestCase(TestCommandHandler))
    suite.addTests(loader.loadTestsFromTestCase(TestMenuGeneration))
    suite.addTests(loader.loadTestsFromTestCase(TestEndToEndScenarios))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
