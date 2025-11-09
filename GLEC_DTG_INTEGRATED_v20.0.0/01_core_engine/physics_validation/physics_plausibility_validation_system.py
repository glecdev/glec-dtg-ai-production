#!/usr/bin/env python3
"""
물리 개연성 검증 시스템 v1.0
실시간 데이터의 물리 법칙 준수성 검증 및 이상치 탐지
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient
import warnings
import json
import time
from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import logging

# 설정
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "glec-admin-token-123456789"
INFLUXDB_ORG = "glec"
INFLUXDB_BUCKET = "dtg_metrics"

class PhysicsValidationEngine:
    """물리 법칙 기반 데이터 검증 엔진"""
    
    def __init__(self):
        self.validation_rules = {
            'speed_acceleration': {
                'name': '속도-가속도 일관성',
                'description': 'v = u + at 법칙 검증',
                'tolerance': 5.0,  # 허용 오차 (%)
                'critical': False
            },
            'fuel_speed_correlation': {
                'name': '연비-속도 상관관계',
                'description': '속도와 연비의 물리적 관계 검증',
                'tolerance': 15.0,
                'critical': True
            },
            'weight_acceleration': {
                'name': '중량-가속도 관계',
                'description': 'F = ma 기반 중량과 가속도 관계',
                'tolerance': 10.0,
                'critical': True
            },
            'co2_fuel_consistency': {
                'name': 'CO2-연료소모 일치성',
                'description': '연료소모량과 CO2 배출량 비례 관계',
                'tolerance': 8.0,
                'critical': True
            },
            'speed_rpm_correlation': {
                'name': '속도-RPM 상관관계',
                'description': '차량 속도와 엔진 RPM의 기계적 관계',
                'tolerance': 12.0,
                'critical': False
            },
            'temperature_performance': {
                'name': '온도-성능 상관관계',
                'description': '엔진온도와 성능지표의 열역학적 관계',
                'tolerance': 20.0,
                'critical': False
            }
        }
        
        # 물리적 상수 및 기준값
        self.physical_constants = {
            'co2_per_liter_diesel': 2.68,  # kg CO2/L 디젤
            'truck_mass_range': (5000, 40000),  # kg (5톤-40톤)
            'max_acceleration': 3.0,  # m/s² (화물차 최대 가속도)
            'optimal_speed_range': (70, 90),  # km/h (연비 최적 속도)
            'rpm_speed_ratio_range': (25, 45)  # RPM당 km/h
        }
        
        self.anomaly_detector = IsolationForest(
            contamination=0.1,  # 10% 이상치로 가정
            random_state=42
        )
        self.scaler = StandardScaler()
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def validate_speed_acceleration_consistency(self, data_df):
        """속도-가속도 일관성 검증"""
        results = {
            'rule_name': 'speed_acceleration',
            'total_records': len(data_df),
            'violations': 0,
            'violation_rate': 0.0,
            'details': []
        }
        
        if 'vehicle_speed' not in data_df.columns or 'acceleration' not in data_df.columns:
            results['error'] = 'Required fields missing: vehicle_speed, acceleration'
            return results
        
        # 시간 간격을 고려한 속도 변화량 계산 (1초 간격 가정)
        dt = 1.0  # seconds
        tolerance = self.validation_rules['speed_acceleration']['tolerance']
        
        violations = []
        for i in range(1, len(data_df)):
            current_speed = data_df.iloc[i]['vehicle_speed']
            prev_speed = data_df.iloc[i-1]['vehicle_speed']
            acceleration = data_df.iloc[i]['acceleration']
            
            # 예상 속도 변화량 (v = u + at)
            expected_speed_change = acceleration * dt * 3.6  # m/s² to km/h conversion
            actual_speed_change = current_speed - prev_speed
            
            # 상대 오차 계산
            if abs(expected_speed_change) > 0.1:  # 최소 임계값
                relative_error = abs(actual_speed_change - expected_speed_change) / abs(expected_speed_change) * 100
                
                if relative_error > tolerance:
                    violations.append({
                        'index': i,
                        'expected_change': expected_speed_change,
                        'actual_change': actual_speed_change,
                        'error_percent': relative_error,
                        'current_speed': current_speed,
                        'acceleration': acceleration
                    })
        
        results['violations'] = len(violations)
        results['violation_rate'] = len(violations) / max(1, len(data_df) - 1) * 100
        results['details'] = violations[:10]  # 최대 10개만 저장
        
        return results

    def validate_fuel_speed_correlation(self, data_df):
        """연비-속도 상관관계 검증"""
        results = {
            'rule_name': 'fuel_speed_correlation',
            'total_records': len(data_df),
            'violations': 0,
            'violation_rate': 0.0,
            'correlation_coefficient': 0.0,
            'details': []
        }
        
        required_fields = ['vehicle_speed', 'fuel_efficiency_kmpl']
        if not all(field in data_df.columns for field in required_fields):
            results['error'] = f'Required fields missing: {required_fields}'
            return results
        
        # 유효한 데이터 필터링
        valid_data = data_df[
            (data_df['vehicle_speed'] > 0) & 
            (data_df['fuel_efficiency_kmpl'] > 0) &
            (data_df['vehicle_speed'] < 200) &  # 200km/h 이하
            (data_df['fuel_efficiency_kmpl'] < 50)  # 50km/L 이하
        ].copy()
        
        if len(valid_data) < 10:
            results['error'] = 'Insufficient valid data for correlation analysis'
            return results
        
        # 상관관계 계산
        correlation = valid_data['vehicle_speed'].corr(valid_data['fuel_efficiency_kmpl'])
        results['correlation_coefficient'] = correlation
        
        # 연비-속도 곡선 모델링 (2차 함수 - 물리적 특성)
        speeds = valid_data['vehicle_speed']
        fuel_effs = valid_data['fuel_efficiency_kmpl']
        
        # 2차 다항식 피팅
        try:
            coeffs = np.polyfit(speeds, fuel_effs, 2)
            poly_func = np.poly1d(coeffs)
            
            # 예측값과 실제값 비교
            predicted_fuel_effs = poly_func(speeds)
            errors = np.abs(fuel_effs - predicted_fuel_effs)
            relative_errors = (errors / fuel_effs) * 100
            
            tolerance = self.validation_rules['fuel_speed_correlation']['tolerance']
            violation_mask = relative_errors > tolerance
            
            violations = []
            violation_indices = np.where(violation_mask)[0]
            for idx in violation_indices[:10]:  # 최대 10개
                violations.append({
                    'index': int(idx),
                    'speed': float(speeds.iloc[idx]),
                    'actual_fuel_eff': float(fuel_effs.iloc[idx]),
                    'predicted_fuel_eff': float(predicted_fuel_effs[idx]),
                    'error_percent': float(relative_errors.iloc[idx])
                })
            
            results['violations'] = int(violation_mask.sum())
            results['violation_rate'] = float(violation_mask.mean() * 100)
            results['details'] = violations
            
        except Exception as e:
            results['error'] = f'Curve fitting failed: {str(e)}'
        
        return results

    def validate_weight_acceleration_relationship(self, data_df):
        """중량-가속도 관계 검증 (F = ma)"""
        results = {
            'rule_name': 'weight_acceleration',
            'total_records': len(data_df),
            'violations': 0,
            'violation_rate': 0.0,
            'details': []
        }
        
        required_fields = ['total_weight', 'acceleration']
        if not all(field in data_df.columns for field in required_fields):
            results['error'] = f'Required fields missing: {required_fields}'
            return results
        
        # 유효한 데이터 필터링
        valid_data = data_df[
            (data_df['total_weight'] > 0) &
            (data_df['acceleration'].abs() > 0.1)  # 최소 가속도 임계값
        ].copy()
        
        if len(valid_data) < 5:
            results['error'] = 'Insufficient valid data'
            return results
        
        # 물리적 기대값 계산
        # 무거운 트럭일수록 가속도가 낮아야 함 (엔진 출력 한계)
        weights = valid_data['total_weight']
        accelerations = valid_data['acceleration'].abs()
        
        # 중량-가속도 반비례 관계 검증
        expected_acc_factor = 1.0 / (weights / 10000)  # 10톤 기준 정규화
        
        violations = []
        tolerance = self.validation_rules['weight_acceleration']['tolerance']
        
        for i, (weight, acceleration) in enumerate(zip(weights, accelerations)):
            # 예상 최대 가속도 (중량 기반)
            max_expected_acc = self.physical_constants['max_acceleration'] * (10000 / weight)
            
            if acceleration > max_expected_acc * (1 + tolerance/100):
                violations.append({
                    'index': i,
                    'weight': float(weight),
                    'acceleration': float(acceleration),
                    'max_expected': float(max_expected_acc),
                    'violation_ratio': float(acceleration / max_expected_acc)
                })
        
        results['violations'] = len(violations)
        results['violation_rate'] = len(violations) / len(valid_data) * 100
        results['details'] = violations[:10]
        
        return results

    def validate_co2_fuel_consistency(self, data_df):
        """CO2-연료소모 일치성 검증"""
        results = {
            'rule_name': 'co2_fuel_consistency',
            'total_records': len(data_df),
            'violations': 0,
            'violation_rate': 0.0,
            'details': []
        }
        
        required_fields = ['co2_emission', 'fuel_efficiency_kmpl', 'vehicle_speed']
        if not all(field in data_df.columns for field in required_fields):
            results['error'] = f'Required fields missing: {required_fields}'
            return results
        
        # 유효한 데이터 필터링
        valid_data = data_df[
            (data_df['co2_emission'] > 0) &
            (data_df['fuel_efficiency_kmpl'] > 0) &
            (data_df['vehicle_speed'] > 0)
        ].copy()
        
        if len(valid_data) < 5:
            results['error'] = 'Insufficient valid data'
            return results
        
        # CO2 배출량 계산 (g/km)
        # 연료소모량(L/km) = 1 / fuel_efficiency_kmpl
        # CO2 배출량 = 연료소모량 × CO2_per_liter
        
        co2_per_liter = self.physical_constants['co2_per_liter_diesel'] * 1000  # g/L
        tolerance = self.validation_rules['co2_fuel_consistency']['tolerance']
        
        violations = []
        
        for i, row in valid_data.iterrows():
            fuel_consumption_per_km = 1.0 / row['fuel_efficiency_kmpl']  # L/km
            expected_co2_per_km = fuel_consumption_per_km * co2_per_liter  # g/km
            actual_co2 = row['co2_emission']
            
            # 상대 오차 계산
            relative_error = abs(actual_co2 - expected_co2_per_km) / expected_co2_per_km * 100
            
            if relative_error > tolerance:
                violations.append({
                    'index': int(i),
                    'actual_co2': float(actual_co2),
                    'expected_co2': float(expected_co2_per_km),
                    'error_percent': float(relative_error),
                    'fuel_efficiency': float(row['fuel_efficiency_kmpl']),
                    'speed': float(row['vehicle_speed'])
                })
        
        results['violations'] = len(violations)
        results['violation_rate'] = len(violations) / len(valid_data) * 100
        results['details'] = violations[:10]
        
        return results

    def detect_anomalies_multivariate(self, data_df):
        """다변량 이상치 탐지"""
        results = {
            'method': 'isolation_forest',
            'total_records': len(data_df),
            'anomalies': 0,
            'anomaly_rate': 0.0,
            'details': []
        }
        
        # 수치형 컬럼만 선택
        numeric_columns = data_df.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_columns) < 3:
            results['error'] = 'Insufficient numeric columns for multivariate analysis'
            return results
        
        # 핵심 물리 변수들 우선 선택
        priority_columns = [
            'vehicle_speed', 'acceleration', 'fuel_efficiency_kmpl', 
            'co2_emission', 'total_weight', 'safety_score'
        ]
        
        selected_columns = [col for col in priority_columns if col in numeric_columns]
        if len(selected_columns) < 3:
            selected_columns = numeric_columns[:6]  # 최대 6개 컬럼
        
        try:
            # 유효한 데이터만 선택 (NaN 제거)
            clean_data = data_df[selected_columns].dropna()
            
            if len(clean_data) < 10:
                results['error'] = 'Insufficient clean data for anomaly detection'
                return results
            
            # 표준화
            scaled_data = self.scaler.fit_transform(clean_data)
            
            # 이상치 탐지
            anomaly_labels = self.anomaly_detector.fit_predict(scaled_data)
            anomaly_scores = self.anomaly_detector.score_samples(scaled_data)
            
            # 이상치 인덱스 추출
            anomaly_indices = np.where(anomaly_labels == -1)[0]
            
            # 상세 정보 수집
            anomalies_detail = []
            for idx in anomaly_indices[:15]:  # 최대 15개
                original_idx = clean_data.index[idx]
                anomaly_data = {
                    'index': int(original_idx),
                    'anomaly_score': float(anomaly_scores[idx]),
                    'values': {}
                }
                
                for col in selected_columns:
                    anomaly_data['values'][col] = float(clean_data.iloc[idx][col])
                
                anomalies_detail.append(anomaly_data)
            
            results['anomalies'] = len(anomaly_indices)
            results['anomaly_rate'] = len(anomaly_indices) / len(clean_data) * 100
            results['details'] = anomalies_detail
            results['selected_features'] = selected_columns
            
        except Exception as e:
            results['error'] = f'Anomaly detection failed: {str(e)}'
        
        return results

    def run_comprehensive_validation(self, data_df):
        """종합 물리 검증 실행"""
        self.logger.info(f"Starting comprehensive physics validation on {len(data_df)} records")
        
        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'total_records': len(data_df),
            'validation_rules': {},
            'anomaly_detection': {},
            'overall_score': 0.0,
            'critical_violations': 0,
            'recommendations': []
        }
        
        # 개별 물리 법칙 검증
        physics_validations = [
            self.validate_speed_acceleration_consistency,
            self.validate_fuel_speed_correlation,
            self.validate_weight_acceleration_relationship,
            self.validate_co2_fuel_consistency
        ]
        
        critical_violations = 0
        total_violation_rate = 0
        valid_tests = 0
        
        for validation_func in physics_validations:
            try:
                result = validation_func(data_df)
                rule_name = result['rule_name']
                validation_results['validation_rules'][rule_name] = result
                
                if 'error' not in result:
                    valid_tests += 1
                    total_violation_rate += result['violation_rate']
                    
                    if (self.validation_rules[rule_name]['critical'] and 
                        result['violation_rate'] > 5.0):  # 5% 이상 위반시 critical
                        critical_violations += 1
                        
            except Exception as e:
                self.logger.error(f"Validation {validation_func.__name__} failed: {e}")
        
        # 이상치 탐지
        try:
            anomaly_result = self.detect_anomalies_multivariate(data_df)
            validation_results['anomaly_detection'] = anomaly_result
        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {e}")
        
        # 전체 점수 계산 (0-100)
        if valid_tests > 0:
            avg_violation_rate = total_violation_rate / valid_tests
            validation_results['overall_score'] = max(0, 100 - avg_violation_rate)
        
        validation_results['critical_violations'] = critical_violations
        
        # 권고사항 생성
        recommendations = []
        if critical_violations > 0:
            recommendations.append("Critical physics violations detected - immediate system review required")
        if avg_violation_rate > 10:
            recommendations.append("High violation rate detected - sensor calibration recommended")
        if 'anomaly_detection' in validation_results and validation_results['anomaly_detection'].get('anomaly_rate', 0) > 15:
            recommendations.append("High anomaly rate - data collection system inspection needed")
        
        if not recommendations:
            recommendations.append("Physics validation passed - system operating within normal parameters")
        
        validation_results['recommendations'] = recommendations
        
        self.logger.info(f"Validation completed. Overall score: {validation_results['overall_score']:.1f}")
        
        return validation_results

def main():
    """메인 실행 함수"""
    print("🔬 물리 개연성 검증 시스템 v1.0 시작")
    print("="*80)
    print(f"검증 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("목적: 실시간 DTG 데이터의 물리 법칙 준수성 검증")
    
    try:
        # InfluxDB 데이터 수집
        print("\n📊 InfluxDB에서 최근 데이터 수집 중...")
        
        client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        query_api = client.query_api()
        
        # 최근 10분간 데이터 조회
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -10m)
            |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''
        
        result = query_api.query_data_frame(query=query)
        
        # 결과가 리스트인 경우 처리
        if isinstance(result, list):
            if len(result) == 0:
                print("❌ 조회된 데이터가 없습니다.")
                return
            result = result[0] if len(result) == 1 else pd.concat(result, ignore_index=True)
        
        if result.empty:
            print("❌ 조회된 데이터가 없습니다.")
            return
        
        print(f"✅ {len(result)}개 레코드 수집 완료")
        print(f"📋 컬럼: {list(result.columns)}")
        
        # 데이터 전처리
        # '_time' 컬럼이 있다면 제거 (분석에 불필요)
        analysis_df = result.drop(columns=[col for col in ['_time', '_start', '_stop', 'table', 'result'] 
                                          if col in result.columns])
        
        # 물리 검증 엔진 초기화 및 실행
        print("\n🔬 물리 검증 엔진 초기화...")
        physics_engine = PhysicsValidationEngine()
        
        print("🧪 종합 물리 검증 실행 중...")
        validation_results = physics_engine.run_comprehensive_validation(analysis_df)
        
        # 결과 출력
        print("\n" + "="*80)
        print("🎯 물리 개연성 검증 결과")
        print("="*80)
        
        print(f"📊 전체 레코드: {validation_results['total_records']:,}개")
        print(f"🏆 전체 점수: {validation_results['overall_score']:.1f}/100")
        print(f"🚨 Critical 위반: {validation_results['critical_violations']}개")
        
        # 개별 검증 결과
        print(f"\n📋 개별 물리 법칙 검증 결과:")
        for rule_name, result in validation_results['validation_rules'].items():
            if 'error' not in result:
                status = "✅" if result['violation_rate'] < 5.0 else "⚠️" if result['violation_rate'] < 15.0 else "❌"
                print(f"   {status} {rule_name}: {result['violation_rate']:.1f}% 위반 ({result['violations']}개)")
            else:
                print(f"   ❌ {rule_name}: 오류 - {result['error']}")
        
        # 이상치 탐지 결과
        if 'anomaly_detection' in validation_results:
            anom_result = validation_results['anomaly_detection']
            if 'error' not in anom_result:
                anom_status = "✅" if anom_result['anomaly_rate'] < 10.0 else "⚠️" if anom_result['anomaly_rate'] < 20.0 else "❌"
                print(f"\n🔍 이상치 탐지 결과:")
                print(f"   {anom_status} 이상치 비율: {anom_result['anomaly_rate']:.1f}% ({anom_result['anomalies']}개)")
            else:
                print(f"\n❌ 이상치 탐지 오류: {anom_result['error']}")
        
        # 권고사항
        print(f"\n💡 권고사항:")
        for i, rec in enumerate(validation_results['recommendations'], 1):
            print(f"   {i}. {rec}")
        
        # 등급 평가
        score = validation_results['overall_score']
        if score >= 90:
            grade = "🥇 EXCELLENT (물리 법칙 완벽 준수)"
        elif score >= 80:
            grade = "🥈 GOOD (양호한 물리적 일관성)"
        elif score >= 70:
            grade = "🥉 FAIR (일부 개선 필요)"
        else:
            grade = "📊 POOR (시스템 점검 필요)"
        
        print(f"\n🏆 종합 평가: {grade}")
        
        # 결과 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"physics_validation_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📁 상세 보고서 저장: {report_file}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ 검증 실행 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()