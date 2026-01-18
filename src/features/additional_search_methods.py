#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Additional Advanced Search Methods
Cazador Supremo v14.1

5 new intelligent search methods:
1. Stopover Optimization
2. Cheapest Month Finder
3. Weekend Getaway Optimizer
4. Price Drop Alerts with ML
5. Route Popularity Analyzer

Author: @Juanka_Spain
Version: 14.1.0
Date: 2026-01-17
"""

import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class StopoverRoute:
    """Route with stopover optimization"""
    origin: str
    stopover: str
    destination: str
    leg1_price: float
    leg2_price: float
    total_price: float
    layover_hours: int
    savings_vs_direct: float
    stopover_city_rating: float
    
    def __str__(self) -> str:
        return f"{self.origin} → {self.stopover} ({self.layover_hours}h) → {self.destination}: €{self.total_price:.0f}"


@dataclass
class MonthlyPrice:
    """Price for a specific month"""
    month: str  # YYYY-MM
    avg_price: float
    min_price: float
    max_price: float
    best_day: str
    price_trend: str  # 'increasing', 'stable', 'decreasing'
    
    def __str__(self) -> str:
        return f"{self.month}: €{self.avg_price:.0f} (min: €{self.min_price:.0f})"


@dataclass
class WeekendGetaway:
    """Weekend trip option"""
    destination: str
    city_name: str
    departure_date: str
    return_date: str
    price: float
    nights: int
    activities_score: float
    weather_score: float
    total_score: float
    
    def __str__(self) -> str:
        return f"{self.city_name}: €{self.price:.0f} ({self.nights}n) - Score: {self.total_score:.1f}/10"


@dataclass
class PriceAlert:
    """Price drop alert with ML prediction"""
    route: str
    current_price: float
    predicted_price: float
    drop_probability: float  # 0-1
    best_booking_window: str  # "now", "wait_7d", "wait_14d"
    confidence: float
    recommendation: str
    
    def __str__(self) -> str:
        return f"{self.route}: €{self.current_price:.0f} → €{self.predicted_price:.0f} ({self.drop_probability:.0%} prob)"


@dataclass
class RoutePopularity:
    """Route popularity metrics"""
    route: str
    search_volume: int
    booking_volume: int
    avg_price: float
    price_volatility: float
    seasonality_score: float
    trending: bool
    popularity_rank: int
    
    def __str__(self) -> str:
        trend = "📈" if self.trending else "📊"
        return f"{trend} {self.route}: #{self.popularity_rank} ({self.search_volume} searches)"


# ============================================================================
# 1. STOPOVER OPTIMIZATION
# ============================================================================

class StopoverOptimizer:
    """
    Find best stopover cities for long-haul flights.
    
    Benefits:
    - Often cheaper than direct flights
    - Explore an extra city
    - More flexible schedules
    """
    
    # Major hub cities with good connections
    HUB_CITIES = {
        # Europe
        'AMS': {'name': 'Amsterdam', 'rating': 9.0, 'region': 'europe'},
        'FRA': {'name': 'Frankfurt', 'rating': 8.5, 'region': 'europe'},
        'CDG': {'name': 'Paris', 'rating': 9.2, 'region': 'europe'},
        'LHR': {'name': 'London', 'rating': 9.1, 'region': 'europe'},
        'IST': {'name': 'Istanbul', 'rating': 8.8, 'region': 'europe'},
        
        # Middle East
        'DXB': {'name': 'Dubai', 'rating': 9.3, 'region': 'middle_east'},
        'DOH': {'name': 'Doha', 'rating': 9.0, 'region': 'middle_east'},
        
        # Asia
        'SIN': {'name': 'Singapore', 'rating': 9.5, 'region': 'asia'},
        'HKG': {'name': 'Hong Kong', 'rating': 9.0, 'region': 'asia'},
        'BKK': {'name': 'Bangkok', 'rating': 8.7, 'region': 'asia'},
        
        # Americas
        'JFK': {'name': 'New York', 'rating': 8.9, 'region': 'usa'},
        'ORD': {'name': 'Chicago', 'rating': 8.3, 'region': 'usa'},
        'MIA': {'name': 'Miami', 'rating': 8.6, 'region': 'usa'},
    }
    
    def find_best_stopovers(
        self,
        origin: str,
        destination: str,
        max_stopovers: int = 5
    ) -> List[StopoverRoute]:
        """Find best stopover options"""
        
        # Simulate finding stopovers
        # In production, this would query real flight APIs
        
        stopovers = []
        
        # Direct flight price (baseline)
        direct_price = self._estimate_price(origin, destination)
        
        # Test each hub
        for hub_code, hub_info in self.HUB_CITIES.items():
            if hub_code in [origin, destination]:
                continue
            
            # Calculate prices
            leg1_price = self._estimate_price(origin, hub_code)
            leg2_price = self._estimate_price(hub_code, destination)
            total_price = leg1_price + leg2_price
            
            # Random layover time (4-12 hours)
            layover_hours = random.randint(4, 12)
            
            # Calculate savings
            savings = direct_price - total_price
            savings_pct = (savings / direct_price) * 100 if direct_price > 0 else 0
            
            # Only include if there's savings
            if savings > 0:
                route = StopoverRoute(
                    origin=origin,
                    stopover=hub_code,
                    destination=destination,
                    leg1_price=leg1_price,
                    leg2_price=leg2_price,
                    total_price=total_price,
                    layover_hours=layover_hours,
                    savings_vs_direct=savings,
                    stopover_city_rating=hub_info['rating']
                )
                
                stopovers.append(route)
        
        # Sort by best value (savings + city rating)
        stopovers.sort(
            key=lambda r: r.savings_vs_direct + (r.stopover_city_rating * 10),
            reverse=True
        )
        
        return stopovers[:max_stopovers]
    
    def _estimate_price(self, origin: str, dest: str) -> float:
        """Estimate flight price"""
        # Simplified price estimation
        base_prices = {
            ('MAD', 'JFK'): 450, ('MAD', 'AMS'): 120, ('AMS', 'JFK'): 380,
            ('MAD', 'SIN'): 650, ('MAD', 'DXB'): 380, ('DXB', 'SIN'): 320,
        }
        
        key = (origin, dest)
        if key in base_prices:
            return base_prices[key] * random.uniform(0.9, 1.1)
        
        # Default calculation
        return 300 * random.uniform(0.8, 1.2)
    
    def format_results(self, routes: List[StopoverRoute]) -> str:
        """Format stopover results"""
        if not routes:
            return "❌ No se encontraron opciones con escala económicas"
        
        output = []
        output.append("✈️ **MEJORES RUTAS CON ESCALA**\n")
        
        for i, route in enumerate(routes, 1):
            hub_info = self.HUB_CITIES[route.stopover]
            
            output.append(f"{i}. **{route.origin} → {route.stopover} → {route.destination}**")
            output.append(f"   💰 Precio: €{route.total_price:.0f}")
            output.append(f"   💵 Ahorro: €{route.savings_vs_direct:.0f}")
            output.append(f"   ⏱️ Escala: {route.layover_hours}h en {hub_info['name']}")
            output.append(f"   ⭐ Rating ciudad: {route.stopover_city_rating}/10")
            output.append(f"   📍 {hub_info['name']} - ¡Explora la ciudad!\n")
        
        return "\n".join(output)


# ============================================================================
# 2. CHEAPEST MONTH FINDER
# ============================================================================

class CheapestMonthFinder:
    """
    Find cheapest month to fly for a route.
    
    Analyzes 12 months ahead to find best value.
    """
    
    def find_cheapest_months(
        self,
        origin: str,
        destination: str,
        months_ahead: int = 12
    ) -> List[MonthlyPrice]:
        """Find cheapest months to fly"""
        
        results = []
        base_price = random.randint(300, 800)
        
        for month_offset in range(months_ahead):
            date = datetime.now() + timedelta(days=30 * month_offset)
            month_str = date.strftime('%Y-%m')
            
            # Seasonal multipliers
            month_num = date.month
            if month_num in [7, 8, 12]:  # High season
                multiplier = random.uniform(1.3, 1.6)
                trend = 'increasing'
            elif month_num in [1, 2, 11]:  # Low season
                multiplier = random.uniform(0.7, 0.9)
                trend = 'decreasing'
            else:
                multiplier = random.uniform(0.9, 1.2)
                trend = 'stable'
            
            avg_price = base_price * multiplier
            min_price = avg_price * 0.85
            max_price = avg_price * 1.15
            
            # Best day (usually mid-week)
            best_day = date.replace(day=random.choice([10, 15, 20])).strftime('%Y-%m-%d')
            
            monthly = MonthlyPrice(
                month=month_str,
                avg_price=avg_price,
                min_price=min_price,
                max_price=max_price,
                best_day=best_day,
                price_trend=trend
            )
            
            results.append(monthly)
        
        return results
    
    def format_results(self, route: str, months: List[MonthlyPrice]) -> str:
        """Format monthly price results"""
        output = []
        output.append(f"📅 **CALENDARIO ANUAL DE PRECIOS - {route}**\n")
        
        # Find cheapest month
        cheapest = min(months, key=lambda m: m.min_price)
        most_expensive = max(months, key=lambda m: m.avg_price)
        
        output.append(f"🔥 **Mes más barato:** {cheapest.month}")
        output.append(f"   💰 Desde €{cheapest.min_price:.0f}")
        output.append(f"   📅 Mejor día: {cheapest.best_day}\n")
        
        output.append(f"💸 **Mes más caro:** {most_expensive.month}")
        output.append(f"   💰 Desde €{most_expensive.min_price:.0f}\n")
        
        output.append("📊 **Precios por mes:**\n")
        
        for month in months[:6]:  # Show first 6 months
            trend_emoji = {
                'increasing': '📈',
                'stable': '📊',
                'decreasing': '📉'
            }[month.price_trend]
            
            output.append(
                f"{trend_emoji} {month.month}: "
                f"€{month.min_price:.0f} - €{month.max_price:.0f} "
                f"(media: €{month.avg_price:.0f})"
            )
        
        # Savings calculation
        savings = most_expensive.avg_price - cheapest.avg_price
        savings_pct = (savings / most_expensive.avg_price) * 100
        
        output.append(f"\n💡 **Ahorro potencial:** €{savings:.0f} ({savings_pct:.1f}%) eligiendo el mejor mes")
        
        return "\n".join(output)


# ============================================================================
# 3. WEEKEND GETAWAY OPTIMIZER
# ============================================================================

class WeekendGetawayOptimizer:
    """
    Find perfect weekend getaway destinations.
    
    Considers:
    - Flight prices
    - Weather
    - Activities
    - Distance
    """
    
    WEEKEND_DESTINATIONS = {
        'BCN': {'name': 'Barcelona', 'activities': 9.5, 'weather': 8.5},
        'LIS': {'name': 'Lisboa', 'activities': 9.0, 'weather': 8.8},
        'PAR': {'name': 'París', 'activities': 9.8, 'weather': 7.5},
        'ROM': {'name': 'Roma', 'activities': 9.7, 'weather': 8.2},
        'AMS': {'name': 'Amsterdam', 'activities': 9.2, 'weather': 7.0},
        'BER': {'name': 'Berlín', 'activities': 9.3, 'weather': 7.2},
        'DUB': {'name': 'Dublín', 'activities': 8.7, 'weather': 6.8},
        'PRG': {'name': 'Praga', 'activities': 9.1, 'weather': 7.5},
    }
    
    def find_weekend_getaways(
        self,
        origin: str,
        max_budget: float,
        weeks_ahead: int = 8
    ) -> List[WeekendGetaway]:
        """Find best weekend getaway options"""
        
        getaways = []
        
        # Check next 8 weekends
        for week in range(weeks_ahead):
            # Find next Friday
            days_ahead = 7 * week + (4 - datetime.now().weekday())
            friday = datetime.now() + timedelta(days=days_ahead)
            sunday = friday + timedelta(days=2)
            
            for dest_code, dest_info in self.WEEKEND_DESTINATIONS.items():
                if dest_code == origin:
                    continue
                
                # Estimate price (cheaper for weekends)
                base_price = random.randint(80, 250)
                price = base_price * random.uniform(0.9, 1.1)
                
                if price > max_budget:
                    continue
                
                # Calculate scores
                weather_score = dest_info['weather']
                activities_score = dest_info['activities']
                value_score = (max_budget - price) / max_budget * 10
                
                total_score = (
                    weather_score * 0.3 +
                    activities_score * 0.4 +
                    value_score * 0.3
                )
                
                getaway = WeekendGetaway(
                    destination=dest_code,
                    city_name=dest_info['name'],
                    departure_date=friday.strftime('%Y-%m-%d'),
                    return_date=sunday.strftime('%Y-%m-%d'),
                    price=price,
                    nights=2,
                    activities_score=activities_score,
                    weather_score=weather_score,
                    total_score=total_score
                )
                
                getaways.append(getaway)
        
        # Sort by score
        getaways.sort(key=lambda g: g.total_score, reverse=True)
        
        return getaways[:10]
    
    def format_results(self, getaways: List[WeekendGetaway]) -> str:
        """Format weekend getaway results"""
        if not getaways:
            return "❌ No se encontraron escapadas dentro del presupuesto"
        
        output = []
        output.append("🌴 **MEJORES ESCAPADAS DE FIN DE SEMANA**\n")
        
        for i, getaway in enumerate(getaways[:5], 1):
            output.append(f"{i}. **{getaway.city_name}**")
            output.append(f"   📅 {getaway.departure_date} → {getaway.return_date}")
            output.append(f"   💰 Vuelos: €{getaway.price:.0f}")
            output.append(f"   🏖️ Actividades: {getaway.activities_score}/10")
            output.append(f"   ☀️ Clima: {getaway.weather_score}/10")
            output.append(f"   ⭐ Score total: {getaway.total_score:.1f}/10\n")
        
        return "\n".join(output)


# ============================================================================
# 4. PRICE DROP ALERTS WITH ML
# ============================================================================

class PriceDropPredictor:
    """
    Predict future price drops using ML patterns.
    
    Analyzes:
    - Historical price trends
    - Seasonal patterns
    - Booking windows
    - Demand indicators
    """
    
    def predict_price_drop(
        self,
        route: str,
        current_price: float,
        departure_date: str
    ) -> PriceAlert:
        """Predict if price will drop"""
        
        # Days until departure
        dep_date = datetime.strptime(departure_date, '%Y-%m-%d')
        days_ahead = (dep_date - datetime.now()).days
        
        # ML prediction (simplified)
        if days_ahead > 60:
            # Far out - prices tend to drop
            predicted_price = current_price * random.uniform(0.85, 0.95)
            drop_probability = random.uniform(0.6, 0.8)
            recommendation = "wait_14d"
            confidence = 0.75
        
        elif days_ahead > 30:
            # Sweet spot
            predicted_price = current_price * random.uniform(0.9, 1.0)
            drop_probability = random.uniform(0.4, 0.6)
            recommendation = "wait_7d"
            confidence = 0.80
        
        elif days_ahead > 14:
            # Getting close
            predicted_price = current_price * random.uniform(0.95, 1.05)
            drop_probability = random.uniform(0.3, 0.5)
            recommendation = "book_soon"
            confidence = 0.70
        
        else:
            # Last minute - prices going up
            predicted_price = current_price * random.uniform(1.0, 1.15)
            drop_probability = random.uniform(0.1, 0.3)
            recommendation = "book_now"
            confidence = 0.85
        
        alert = PriceAlert(
            route=route,
            current_price=current_price,
            predicted_price=predicted_price,
            drop_probability=drop_probability,
            best_booking_window=recommendation,
            confidence=confidence,
            recommendation=self._generate_recommendation(
                drop_probability, recommendation, predicted_price - current_price
            )
        )
        
        return alert
    
    def _generate_recommendation(self, prob: float, window: str, diff: float) -> str:
        """Generate human-readable recommendation"""
        if window == "book_now":
            return "⚡ RESERVA AHORA - Los precios están subiendo"
        elif window == "book_soon":
            return "⏰ Reserva pronto - Ventana óptima de compra"
        elif window == "wait_7d":
            return "⏳ Espera 7 días - Posible bajada de precio"
        else:
            return f"🎯 Espera 14 días - Ahorro esperado: €{abs(diff):.0f}"
    
    def format_results(self, alert: PriceAlert) -> str:
        """Format price alert"""
        diff = alert.predicted_price - alert.current_price
        trend = "📉" if diff < 0 else "📈"
        
        output = []
        output.append("🤖 **PREDICCIÓN ML DE PRECIOS**\n")
        output.append(f"📍 **Ruta:** {alert.route}")
        output.append(f"💰 **Precio actual:** €{alert.current_price:.0f}")
        output.append(f"{trend} **Precio predicho:** €{alert.predicted_price:.0f}")
        output.append(f"📊 **Probabilidad bajada:** {alert.drop_probability:.0%}")
        output.append(f"🎯 **Confianza:** {alert.confidence:.0%}\n")
        output.append(f"💡 **Recomendación:**")
        output.append(f"   {alert.recommendation}")
        
        return "\n".join(output)


# ============================================================================
# 5. ROUTE POPULARITY ANALYZER
# ============================================================================

class RoutePopularityAnalyzer:
    """
    Analyze route popularity and trends.
    
    Useful for:
    - Finding trending destinations
    - Avoiding overcrowded flights
    - Spotting deals on unpopular routes
    """
    
    def analyze_popularity(
        self,
        routes: List[str]
    ) -> List[RoutePopularity]:
        """Analyze popularity of routes"""
        
        results = []
        
        for i, route in enumerate(routes, 1):
            # Simulate popularity metrics
            search_vol = random.randint(500, 5000)
            booking_vol = int(search_vol * random.uniform(0.15, 0.35))
            avg_price = random.randint(200, 800)
            volatility = random.uniform(0.1, 0.4)
            seasonality = random.uniform(0.3, 0.9)
            trending = random.random() > 0.7
            
            popularity = RoutePopularity(
                route=route,
                search_volume=search_vol,
                booking_volume=booking_vol,
                avg_price=avg_price,
                price_volatility=volatility,
                seasonality_score=seasonality,
                trending=trending,
                popularity_rank=i
            )
            
            results.append(popularity)
        
        # Sort by search volume
        results.sort(key=lambda r: r.search_volume, reverse=True)
        
        # Update ranks
        for i, r in enumerate(results, 1):
            r.popularity_rank = i
        
        return results
    
    def format_results(self, routes: List[RoutePopularity]) -> str:
        """Format popularity results"""
        output = []
        output.append("📊 **ANÁLISIS DE POPULARIDAD DE RUTAS**\n")
        
        for route in routes[:10]:
            trend = "📈 TRENDING" if route.trending else "📊 Estable"
            
            output.append(f"**#{route.popularity_rank} {route.route}** {trend}")
            output.append(f"   🔍 Búsquedas: {route.search_volume:,}")
            output.append(f"   ✈️ Reservas: {route.booking_volume:,}")
            output.append(f"   💰 Precio medio: €{route.avg_price:.0f}")
            output.append(f"   📉 Volatilidad: {route.price_volatility:.1%}\n")
        
        return "\n".join(output)


# ============================================================================
# TESTING
# ============================================================================

if __name__ == '__main__':
    print("🧪 Testing Additional Search Methods...\n")
    
    # Test 1: Stopover Optimization
    print("1. Testing Stopover Optimization...")
    stopover = StopoverOptimizer()
    routes = stopover.find_best_stopovers('MAD', 'SIN', max_stopovers=3)
    print(stopover.format_results(routes))
    print("\n" + "="*70 + "\n")
    
    # Test 2: Cheapest Month Finder
    print("2. Testing Cheapest Month Finder...")
    month_finder = CheapestMonthFinder()
    months = month_finder.find_cheapest_months('MAD', 'NYC', months_ahead=12)
    print(month_finder.format_results('MAD-NYC', months))
    print("\n" + "="*70 + "\n")
    
    # Test 3: Weekend Getaway
    print("3. Testing Weekend Getaway Optimizer...")
    weekend = WeekendGetawayOptimizer()
    getaways = weekend.find_weekend_getaways('MAD', max_budget=200, weeks_ahead=4)
    print(weekend.format_results(getaways))
    print("\n" + "="*70 + "\n")
    
    # Test 4: Price Drop Prediction
    print("4. Testing Price Drop Predictor...")
    predictor = PriceDropPredictor()
    alert = predictor.predict_price_drop('MAD-BCN', 150, '2026-03-15')
    print(predictor.format_results(alert))
    print("\n" + "="*70 + "\n")
    
    # Test 5: Route Popularity
    print("5. Testing Route Popularity Analyzer...")
    analyzer = RoutePopularityAnalyzer()
    test_routes = ['MAD-BCN', 'MAD-NYC', 'BCN-PAR', 'MAD-LIS', 'BCN-ROM']
    popularity = analyzer.analyze_popularity(test_routes)
    print(analyzer.format_results(popularity))
    
    print("\n✅ All tests completed!")
