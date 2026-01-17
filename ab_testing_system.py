#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════╗
║  🧪 A/B TESTING FRAMEWORK                                        ║
║  🚀 Cazador Supremo v14.2                                        ║
║  📊 Statistical Significance + Auto-optimization                 ║
╚═══════════════════════════════════════════════════════════════════╝

Framework completo de A/B testing:
- Múltiples variantes por experimento
- Cálculo de significancia estadística
- Auto-assignment de usuarios
- Winner detection automático
- Rollout gradual del ganador

Autor: @Juanka_Spain  
Version: 14.2.0
Date: 2026-01-17
"""

import json
import logging
import random
import math
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  ENUMS & CONSTANTS
# ═══════════════════════════════════════════════════════════════

class ExperimentStatus(Enum):
    """Estado del experimento"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ROLLED_OUT = "rolled_out"


class MetricType(Enum):
    """Tipo de métrica"""
    CONVERSION = "conversion"  # Binaria 0/1
    CONTINUOUS = "continuous"   # Valor numérico
    RATE = "rate"              # Tasa/porcentaje


# Configuración de experimentos predefinidos
PREDEFINED_EXPERIMENTS = {
    'onboarding_steps': {
        'name': 'Onboarding: 2 steps vs 3 steps',
        'description': 'Test if shorter onboarding improves completion',
        'variants': {
            'control': {'steps': 3, 'description': '3-step original'},
            'variant_a': {'steps': 2, 'description': '2-step simplified'},
        },
        'primary_metric': 'completion_rate',
        'metric_type': MetricType.CONVERSION,
        'min_sample_size': 100,
        'confidence_level': 0.95,
    },
    'bonus_amount': {
        'name': 'Onboarding: Bonus amount',
        'description': 'Test different welcome bonus amounts',
        'variants': {
            'control': {'bonus': 200, 'description': '200 coins'},
            'variant_a': {'bonus': 150, 'description': '150 coins'},
            'variant_b': {'bonus': 250, 'description': '250 coins'},
        },
        'primary_metric': 'completion_rate',
        'metric_type': MetricType.CONVERSION,
        'min_sample_size': 150,
        'confidence_level': 0.95,
    },
    'skip_position': {
        'name': 'Onboarding: Skip button position',
        'description': 'Test skip button placement',
        'variants': {
            'control': {'position': 'bottom', 'description': 'Bottom right'},
            'variant_a': {'position': 'top', 'description': 'Top right'},
            'variant_b': {'position': 'hidden': 'description': 'No skip button'},
        },
        'primary_metric': 'completion_rate',
        'metric_type': MetricType.CONVERSION,
        'min_sample_size': 100,
        'confidence_level': 0.95,
    },
    'message_length': {
        'name': 'Message: Text length',
        'description': 'Test shorter vs longer messages',
        'variants': {
            'control': {'length': 'long', 'description': 'Full detailed text'},
            'variant_a': {'length': 'short', 'description': 'Concise text'},
        },
        'primary_metric': 'engagement_rate',
        'metric_type': MetricType.RATE,
        'min_sample_size': 200,
        'confidence_level': 0.95,
    },
    'emoji_density': {
        'name': 'Message: Emoji density',
        'description': 'Test emoji usage in messages',
        'variants': {
            'control': {'emojis_per_line': 1.5, 'description': 'Current density'},
            'variant_a': {'emojis_per_line': 0.8, 'description': 'Low density'},
            'variant_b': {'emojis_per_line': 2.5, 'description': 'High density'},
        },
        'primary_metric': 'user_satisfaction',
        'metric_type': MetricType.CONTINUOUS,
        'min_sample_size': 150,
        'confidence_level': 0.95,
    },
    'cta_placement': {
        'name': 'CTA: Button placement',
        'description': 'Test call-to-action button position',
        'variants': {
            'control': {'placement': 'bottom', 'description': 'Bottom after text'},
            'variant_a': {'placement': 'top', 'description': 'Top before text'},
            'variant_b': {'placement': 'inline', 'description': 'Inline with text'},
        },
        'primary_metric': 'click_through_rate',
        'metric_type': MetricType.RATE,
        'min_sample_size': 200,
        'confidence_level': 0.95,
    },
}


# ═══════════════════════════════════════════════════════════════
#  DATA CLASSES  
# ═══════════════════════════════════════════════════════════════

@dataclass
class ExperimentVariant:
    """Variante de experimento"""
    variant_id: str
    config: Dict
    description: str
    users: List[int] = None
    
    def __post_init__(self):
        if self.users is None:
            self.users = []
    
    def to_dict(self) -> Dict:
        return {
            'variant_id': self.variant_id,
            'config': self.config,
            'description': self.description,
            'users_count': len(self.users)
        }


@dataclass  
class ExperimentMetric:
    """Métrica de experimento"""
    name: str
    type: MetricType
    values: Dict[str, List[float]]  # variant_id -> [values]
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'type': self.type.value,
            'values': {k: len(v) for k, v in self.values.items()}
        }


@dataclass
class ExperimentResult:
    """Resultado de experimento"""
    variant_id: str
    sample_size: int
    mean: float
    std_dev: float
    confidence_interval: Tuple[float, float]
    conversion_rate: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            'variant_id': self.variant_id,
            'sample_size': self.sample_size,
            'mean': self.mean,
            'std_dev': self.std_dev,
            'confidence_interval': list(self.confidence_interval),
            'conversion_rate': self.conversion_rate
        }


@dataclass
class Experiment:
    """Experimento A/B"""
    experiment_id: str
    name: str
    description: str
    status: ExperimentStatus
    variants: Dict[str, ExperimentVariant]
    primary_metric: str
    metric_type: MetricType
    created_at: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    winner_variant: Optional[str] = None
    min_sample_size: int = 100
    confidence_level: float = 0.95
    traffic_allocation: Dict[str, float] = None
    
    def __post_init__(self):
        if self.traffic_allocation is None:
            # Equal split por default
            n = len(self.variants)
            self.traffic_allocation = {v: 1/n for v in self.variants.keys()}
    
    def to_dict(self) -> Dict:
        return {
            'experiment_id': self.experiment_id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'variants': {k: v.to_dict() for k, v in self.variants.items()},
            'primary_metric': self.primary_metric,
            'metric_type': self.metric_type.value,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'ended_at': self.ended_at,
            'winner_variant': self.winner_variant,
            'min_sample_size': self.min_sample_size,
            'confidence_level': self.confidence_level,
            'traffic_allocation': self.traffic_allocation
        }


# ═══════════════════════════════════════════════════════════════
#  A/B TESTING SYSTEM
# ═══════════════════════════════════════════════════════════════

class ABTestingSystem:
    """
    Framework completo de A/B testing.
    
    Features:
    - Crear y gestionar experimentos
    - Asignar usuarios a variantes
    - Trackear métricas por variante
    - Calcular significancia estadística
    - Detectar winner automáticamente
    - Rollout gradual del ganador
    """
    
    def __init__(self, data_file: str = 'ab_testing_data.json'):
        self.data_file = Path(data_file)
        
        # Storage
        self.experiments: Dict[str, Experiment] = {}
        self.user_assignments: Dict[int, Dict[str, str]] = defaultdict(dict)  # user_id -> {exp_id: variant}
        self.metrics: Dict[str, ExperimentMetric] = {}  # exp_id -> metric
        
        self._load_data()
        
        logger.info("🧪 ABTestingSystem initialized")
    
    def _load_data(self):
        """Carga datos de experimentos."""
        if not self.data_file.exists():
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstruir experimentos
            for exp_data in data.get('experiments', []):
                variants = {
                    k: ExperimentVariant(
                        variant_id=k,
                        config=v['config'],
                        description=v['description'],
                        users=v.get('users', [])
                    )
                    for k, v in exp_data['variants'].items()
                }
                
                exp = Experiment(
                    experiment_id=exp_data['experiment_id'],
                    name=exp_data['name'],
                    description=exp_data['description'],
                    status=ExperimentStatus(exp_data['status']),
                    variants=variants,
                    primary_metric=exp_data['primary_metric'],
                    metric_type=MetricType(exp_data['metric_type']),
                    created_at=exp_data['created_at'],
                    started_at=exp_data.get('started_at'),
                    ended_at=exp_data.get('ended_at'),
                    winner_variant=exp_data.get('winner_variant'),
                    min_sample_size=exp_data.get('min_sample_size', 100),
                    confidence_level=exp_data.get('confidence_level', 0.95),
                    traffic_allocation=exp_data.get('traffic_allocation')
                )
                
                self.experiments[exp.experiment_id] = exp
            
            # User assignments
            self.user_assignments = defaultdict(dict, data.get('user_assignments', {}))
            
            logger.info(f"✅ Loaded {len(self.experiments)} experiments")
        except Exception as e:
            logger.error(f"❌ Error loading A/B testing data: {e}")
    
    def _save_data(self):
        """Guarda datos a archivo."""
        try:
            data = {
                'experiments': [exp.to_dict() for exp in self.experiments.values()],
                'user_assignments': dict(self.user_assignments),
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("💾 A/B testing data saved")
        except Exception as e:
            logger.error(f"❌ Error saving A/B testing data: {e}")
    
    # ═══════════════════════════════════════════════════════════
    #  EXPERIMENT MANAGEMENT
    # ═══════════════════════════════════════════════════════════
    
    def create_experiment(self, experiment_id: str, name: str,
                         description: str, variants_config: Dict,
                         primary_metric: str, metric_type: MetricType,
                         **kwargs) -> Experiment:
        """Crea nuevo experimento."""
        
        # Crear variantes
        variants = {}
        for variant_id, config in variants_config.items():
            variants[variant_id] = ExperimentVariant(
                variant_id=variant_id,
                config=config,
                description=config.get('description', variant_id)
            )
        
        exp = Experiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            status=ExperimentStatus.DRAFT,
            variants=variants,
            primary_metric=primary_metric,
            metric_type=metric_type,
            created_at=datetime.now().isoformat(),
            **kwargs
        )
        
        self.experiments[experiment_id] = exp
        self._save_data()
        
        logger.info(f"🧪 Experiment created: {name}")
        return exp
    
    def create_from_template(self, template_name: str) -> Experiment:
        """Crea experimento desde template."""
        if template_name not in PREDEFINED_EXPERIMENTS:
            raise ValueError(f"Template not found: {template_name}")
        
        template = PREDEFINED_EXPERIMENTS[template_name]
        
        return self.create_experiment(
            experiment_id=template_name,
            name=template['name'],
            description=template['description'],
            variants_config=template['variants'],
            primary_metric=template['primary_metric'],
            metric_type=template['metric_type'],
            min_sample_size=template['min_sample_size'],
            confidence_level=template['confidence_level']
        )
    
    def start_experiment(self, experiment_id: str):
        """Inicia experimento."""
        exp = self.experiments[experiment_id]
        exp.status = ExperimentStatus.RUNNING
        exp.started_at = datetime.now().isoformat()
        
        # Inicializar métrica
        self.metrics[experiment_id] = ExperimentMetric(
            name=exp.primary_metric,
            type=exp.metric_type,
            values={v: [] for v in exp.variants.keys()}
        )
        
        self._save_data()
        logger.info(f"▶️ Experiment started: {exp.name}")
    
    def stop_experiment(self, experiment_id: str):
        """Detiene experimento."""
        exp = self.experiments[experiment_id]
        exp.status = ExperimentStatus.COMPLETED
        exp.ended_at = datetime.now().isoformat()
        
        self._save_data()
        logger.info(f"⏹️ Experiment stopped: {exp.name}")
    
    # ═══════════════════════════════════════════════════════════
    #  USER ASSIGNMENT
    # ═══════════════════════════════════════════════════════════
    
    def assign_variant(self, user_id: int, experiment_id: str) -> str:
        """Asigna usuario a variante."""
        
        # Si ya está asignado, retornar variante existente
        if experiment_id in self.user_assignments[user_id]:
            return self.user_assignments[user_id][experiment_id]
        
        exp = self.experiments[experiment_id]
        
        # Si hay winner, asignar a winner
        if exp.winner_variant:
            variant_id = exp.winner_variant
        else:
            # Asignar basado en traffic allocation
            variant_id = self._random_assignment(exp.traffic_allocation)
        
        # Guardar assignment
        self.user_assignments[user_id][experiment_id] = variant_id
        exp.variants[variant_id].users.append(user_id)
        
        self._save_data()
        return variant_id
    
    def _random_assignment(self, allocation: Dict[str, float]) -> str:
        """Asignación aleatoria basada en pesos."""
        rand = random.random()
        cumulative = 0.0
        
        for variant_id, weight in allocation.items():
            cumulative += weight
            if rand < cumulative:
                return variant_id
        
        # Fallback al último
        return list(allocation.keys())[-1]
    
    def get_variant(self, user_id: int, experiment_id: str) -> Optional[str]:
        """Obtiene variante asignada a usuario."""
        return self.user_assignments[user_id].get(experiment_id)
    
    def get_variant_config(self, user_id: int, experiment_id: str) -> Dict:
        """Obtiene configuración de variante para usuario."""
        variant_id = self.get_variant(user_id, experiment_id)
        if not variant_id:
            # Auto-assign
            variant_id = self.assign_variant(user_id, experiment_id)
        
        exp = self.experiments[experiment_id]
        return exp.variants[variant_id].config
    
    # ═══════════════════════════════════════════════════════════
    #  METRIC TRACKING
    # ═══════════════════════════════════════════════════════════
    
    def track_metric(self, user_id: int, experiment_id: str, value: float):
        """Trackea métrica para usuario."""
        if experiment_id not in self.experiments:
            return
        
        exp = self.experiments[experiment_id]
        if exp.status != ExperimentStatus.RUNNING:
            return
        
        variant_id = self.get_variant(user_id, experiment_id)
        if not variant_id:
            return
        
        # Guardar valor
        if experiment_id not in self.metrics:
            self.metrics[experiment_id] = ExperimentMetric(
                name=exp.primary_metric,
                type=exp.metric_type,
                values={v: [] for v in exp.variants.keys()}
            )
        
        self.metrics[experiment_id].values[variant_id].append(value)
    
    def track_conversion(self, user_id: int, experiment_id: str, converted: bool):
        """Trackea conversión (métrica binaria)."""
        self.track_metric(user_id, experiment_id, 1.0 if converted else 0.0)
    
    # ═══════════════════════════════════════════════════════════
    #  STATISTICAL ANALYSIS
    # ═══════════════════════════════════════════════════════════
    
    def calculate_results(self, experiment_id: str) -> Dict[str, ExperimentResult]:
        """Calcula resultados por variante."""
        exp = self.experiments[experiment_id]
        metric = self.metrics.get(experiment_id)
        
        if not metric:
            return {}
        
        results = {}
        
        for variant_id, values in metric.values.items():
            if not values:
                continue
            
            n = len(values)
            mean = sum(values) / n
            variance = sum((x - mean) ** 2 for x in values) / n
            std_dev = math.sqrt(variance)
            
            # Confidence interval
            z_score = 1.96  # 95% confidence
            margin = z_score * (std_dev / math.sqrt(n))
            ci = (mean - margin, mean + margin)
            
            # Conversion rate (para métricas binarias)
            conversion_rate = mean if metric.type == MetricType.CONVERSION else None
            
            results[variant_id] = ExperimentResult(
                variant_id=variant_id,
                sample_size=n,
                mean=mean,
                std_dev=std_dev,
                confidence_interval=ci,
                conversion_rate=conversion_rate
            )
        
        return results
    
    def calculate_significance(self, experiment_id: str, 
                              variant_a: str, variant_b: str) -> Tuple[bool, float]:
        """Calcula si diferencia es estadísticamente significativa."""
        results = self.calculate_results(experiment_id)
        
        if variant_a not in results or variant_b not in results:
            return False, 0.0
        
        result_a = results[variant_a]
        result_b = results[variant_b]
        
        # Z-test para diferencia de medias
        mean_diff = result_a.mean - result_b.mean
        se_diff = math.sqrt(
            (result_a.std_dev ** 2 / result_a.sample_size) +
            (result_b.std_dev ** 2 / result_b.sample_size)
        )
        
        if se_diff == 0:
            return False, 0.0
        
        z_score = abs(mean_diff / se_diff)
        
        # P-value (aproximado)
        # Para z > 1.96, p < 0.05 (95% confidence)
        is_significant = z_score > 1.96
        
        # Lift percentage
        if result_b.mean != 0:
            lift = ((result_a.mean - result_b.mean) / result_b.mean) * 100
        else:
            lift = 0.0
        
        return is_significant, lift
    
    def detect_winner(self, experiment_id: str) -> Optional[str]:
        """Detecta winner automáticamente."""
        exp = self.experiments[experiment_id]
        results = self.calculate_results(experiment_id)
        
        # Verificar mínimo de muestras
        for result in results.values():
            if result.sample_size < exp.min_sample_size:
                logger.info(f"⏳ Not enough samples yet for {experiment_id}")
                return None
        
        # Encontrar variante con mejor métrica
        best_variant = max(results.items(), key=lambda x: x[1].mean)[0]
        control_variant = 'control'
        
        if best_variant == control_variant:
            logger.info(f"🎯 Control is winning in {experiment_id}")
            return None
        
        # Verificar significancia vs control
        is_significant, lift = self.calculate_significance(
            experiment_id, best_variant, control_variant
        )
        
        if is_significant and lift > 5:  # >5% lift mínimo
            logger.info(f"🏆 Winner detected: {best_variant} (+{lift:.1f}% lift)")
            return best_variant
        
        logger.info(f"⏳ No clear winner yet in {experiment_id}")
        return None
    
    def rollout_winner(self, experiment_id: str, winner_variant: str = None):
        """Rollout gradual del winner."""
        exp = self.experiments[experiment_id]
        
        if not winner_variant:
            winner_variant = self.detect_winner(experiment_id)
        
        if not winner_variant:
            logger.warning(f"⚠️ No winner to rollout for {experiment_id}")
            return
        
        # Actualizar experiment
        exp.winner_variant = winner_variant
        exp.status = ExperimentStatus.ROLLED_OUT
        exp.ended_at = datetime.now().isoformat()
        
        # Actualizar traffic allocation (100% al winner)
        exp.traffic_allocation = {v: 0.0 for v in exp.variants.keys()}
        exp.traffic_allocation[winner_variant] = 1.0
        
        self._save_data()
        logger.info(f"🚀 Rolled out winner: {winner_variant}")
    
    # ═══════════════════════════════════════════════════════════
    #  REPORTING
    # ═══════════════════════════════════════════════════════════
    
    def generate_report(self, experiment_id: str) -> Dict:
        """Genera reporte de experimento."""
        exp = self.experiments[experiment_id]
        results = self.calculate_results(experiment_id)
        
        report = {
            'experiment': exp.to_dict(),
            'results': {k: v.to_dict() for k, v in results.items()},
            'comparisons': {},
            'winner': None,
            'recommendations': []
        }
        
        # Comparaciones vs control
        control_variant = 'control'
        if control_variant in results:
            for variant_id in results.keys():
                if variant_id == control_variant:
                    continue
                
                is_sig, lift = self.calculate_significance(
                    experiment_id, variant_id, control_variant
                )
                
                report['comparisons'][variant_id] = {
                    'vs_control': True,
                    'is_significant': is_sig,
                    'lift_pct': lift,
                    'verdict': 'winner' if is_sig and lift > 0 else 
                              ('loser' if is_sig and lift < 0 else 'inconclusive')
                }
        
        # Detectar winner
        winner = self.detect_winner(experiment_id)
        report['winner'] = winner
        
        # Recomendaciones
        if winner:
            report['recommendations'].append(
                f"🏆 Rollout {winner} - statistically significant improvement"
            )
        else:
            total_samples = sum(r.sample_size for r in results.values())
            if total_samples < exp.min_sample_size * len(exp.variants):
                report['recommendations'].append(
                    f"⏳ Continue experiment - need more samples"
                )
            else:
                report['recommendations'].append(
                    f"🤔 No clear winner - consider new variations"
                )
        
        return report
    
    def print_report(self, experiment_id: str):
        """Imprime reporte en consola."""
        report = self.generate_report(experiment_id)
        exp_data = report['experiment']
        
        print("\n" + "="*70)
        print(f"🧪 A/B TEST REPORT: {exp_data['name']}".center(70))
        print("="*70 + "\n")
        
        print(f"Experiment ID: {exp_data['experiment_id']}")
        print(f"Status: {exp_data['status']}")
        print(f"Primary Metric: {exp_data['primary_metric']}\n")
        
        # Results by variant
        print("RESULTS BY VARIANT:")
        for variant_id, result in report['results'].items():
            print(f"\n  {variant_id}:")
            print(f"    Sample Size: {result['sample_size']}")
            if result['conversion_rate'] is not None:
                print(f"    Conversion Rate: {result['conversion_rate']:.2%}")
            print(f"    Mean: {result['mean']:.4f}")
            print(f"    Std Dev: {result['std_dev']:.4f}")
            ci = result['confidence_interval']
            print(f"    95% CI: [{ci[0]:.4f}, {ci[1]:.4f}]")
        
        # Comparisons
        if report['comparisons']:
            print("\nCOMPARISONS VS CONTROL:")
            for variant_id, comp in report['comparisons'].items():
                sig = "✅ YES" if comp['is_significant'] else "❌ NO"
                lift = comp['lift_pct']
                verdict = comp['verdict'].upper()
                print(f"\n  {variant_id}:")
                print(f"    Significant: {sig}")
                print(f"    Lift: {lift:+.1f}%")
                print(f"    Verdict: {verdict}")
        
        # Winner
        if report['winner']:
            print(f"\n🏆 WINNER: {report['winner']}")
        else:
            print(f"\n⏳ NO CLEAR WINNER YET")
        
        # Recommendations
        print("\nRECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  {rec}")
        
        print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    # 🧪 Test del sistema
    print("🧪 Testing ABTestingSystem...\n")
    
    ab = ABTestingSystem()
    
    # Crear experimento desde template
    print("1. Creating experiment from template...")
    exp = ab.create_from_template('onboarding_steps')
    ab.start_experiment('onboarding_steps')
    
    # Simular usuarios
    print("2. Simulating user interactions...")
    for user_id in range(1000, 1200):
        variant = ab.assign_variant(user_id, 'onboarding_steps')
        
        # Simular conversión (3-step: 75%, 2-step: 82%)
        if variant == 'control':
            converted = random.random() < 0.75
        else:
            converted = random.random() < 0.82
        
        ab.track_conversion(user_id, 'onboarding_steps', converted)
    
    # Generar reporte
    print("\n3. Generating report...")
    ab.print_report('onboarding_steps')
    
    print("\n✅ Test completed!")
