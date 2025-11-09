#!/usr/bin/env python3
"""
고급 안전 점수 알고리즘 v2.0
Critical Requirement #3: 실시간 안전 점수 산출
"""

import numpy as np
from datetime import datetime, timedelta

class AdvancedSafetyScorer:
    """고급 안전 점수 산출 시스템"""
    
    def __init__(self):
        self.safety_weights = {
            'speed_compliance': 0.30,      # 속도 준수
            'acceleration_smoothness': 0.25,  # 가속도 부드러움
            'fuel_efficiency': 0.20,      # 연비 효율
            'braking_pattern': 0.15,      # 제동 패턴
            'lane_stability': 0.10        # 차선 안정성
        }
        
        # 위험 임계값
        self.risk_thresholds = {
            'critical': 30,    # 30점 이하 = 즉시 경고
            'high': 50,        # 50점 이하 = 주의 필요
            'medium': 70,      # 70점 이하 = 모니터링
            'low': 85          # 85점 이상 = 안전
        }
    
    def calculate_speed_compliance_score(self, current_speed, speed_limit):
        """속도 준수 점수"""
        if speed_limit <= 0:
            return 50  # 기본값
        
        speed_ratio = current_speed / speed_limit
        
        if speed_ratio <= 0.9:  # 90% 이하
            return 100
        elif speed_ratio <= 1.0:  # 100% 이하
            return 90
        elif speed_ratio <= 1.1:  # 110% 이하
            return 70
        elif speed_ratio <= 1.2:  # 120% 이하
            return 40
        else:
            return 0  # 위험한 과속
    
    def calculate_acceleration_smoothness(self, acceleration_history):
        """가속도 부드러움 점수"""
        if len(acceleration_history) < 2:
            return 50
        
        # 가속도 변화율의 표준편차로 부드러움 측정
        acc_changes = np.diff(acceleration_history)
        smoothness = 100 - min(100, np.std(acc_changes) * 20)
        
        return max(0, smoothness)
    
    def calculate_fuel_efficiency_score(self, current_efficiency, optimal_efficiency):
        """연비 효율 점수"""
        if optimal_efficiency <= 0:
            return 50
        
        efficiency_ratio = current_efficiency / optimal_efficiency
        
        if efficiency_ratio >= 0.95:  # 95% 이상
            return 100
        elif efficiency_ratio >= 0.85:  # 85% 이상
            return 80
        elif efficiency_ratio >= 0.70:  # 70% 이상
            return 60
        else:
            return max(0, efficiency_ratio * 100)
    
    def calculate_overall_safety_score(self, metrics):
        """종합 안전 점수 계산"""
        speed_score = self.calculate_speed_compliance_score(
            metrics.get('current_speed', 0),
            metrics.get('speed_limit', 100)
        )
        
        accel_score = self.calculate_acceleration_smoothness(
            metrics.get('acceleration_history', [0])
        )
        
        fuel_score = self.calculate_fuel_efficiency_score(
            metrics.get('fuel_efficiency', 0),
            metrics.get('optimal_fuel_efficiency', 8.0)
        )
        
        # 가중 평균 계산
        overall_score = (
            speed_score * self.safety_weights['speed_compliance'] +
            accel_score * self.safety_weights['acceleration_smoothness'] +
            fuel_score * self.safety_weights['fuel_efficiency'] +
            75 * self.safety_weights['braking_pattern'] +  # 기본값
            75 * self.safety_weights['lane_stability']     # 기본값
        )
        
        return {
            'overall_score': round(overall_score, 1),
            'components': {
                'speed_compliance': speed_score,
                'acceleration_smoothness': accel_score,
                'fuel_efficiency': fuel_score
            },
            'risk_level': self.get_risk_level(overall_score),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_risk_level(self, score):
        """위험도 수준 결정"""
        if score <= self.risk_thresholds['critical']:
            return 'CRITICAL'
        elif score <= self.risk_thresholds['high']:
            return 'HIGH'
        elif score <= self.risk_thresholds['medium']:
            return 'MEDIUM'
        else:
            return 'LOW'

if __name__ == "__main__":
    scorer = AdvancedSafetyScorer()
    
    # 테스트 데이터
    test_metrics = {
        'current_speed': 85,
        'speed_limit': 90,
        'acceleration_history': [0.5, 0.8, 0.3, 0.1, -0.2],
        'fuel_efficiency': 7.2,
        'optimal_fuel_efficiency': 8.0
    }
    
    result = scorer.calculate_overall_safety_score(test_metrics)
    print(f"안전 점수: {result}")
