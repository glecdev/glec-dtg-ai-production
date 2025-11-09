#!/usr/bin/env python3
"""
심층적 데이터 파이프라인 문제 진단 및 해결
지연시간 1초~238초 불일치 문제의 근본 원인 파악
"""

import requests
import subprocess
import json
import time
import os
import signal
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import psutil
import statistics
import threading

# 설정
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "glec-admin-token-123456789"
INFLUXDB_ORG = "glec"
INFLUXDB_BUCKET = "dtg_metrics"

def print_section(title):
    """섹션 구분자"""
    print(f"\n{'='*80}")
    print(f"🔍 {title}")
    print(f"{'='*80}")

def print_subsection(title):
    """서브섹션 구분자"""
    print(f"\n{'-'*60}")
    print(f"📋 {title}")
    print(f"{'-'*60}")

def analyze_data_timestamps():
    """데이터 타임스탬프 심층 분석"""
    print_subsection("데이터 타임스탬프 일관성 분석")
    
    try:
        client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        query_api = client.query_api()
        
        # 최근 5분간 모든 데이터의 타임스탬프 분석
        timestamp_query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -5m)
            |> keep(columns: ["_time", "highway", "vehicle_id", "_field"])
            |> limit(n: 1000)
        '''
        
        print("   📊 최근 5분간 데이터 타임스탬프 수집 중...")
        result = query_api.query(query=timestamp_query)
        
        timestamps = []
        current_time = datetime.now().astimezone()
        
        for table in result:
            for record in table.records:
                record_time = record.get_time()
                time_diff = (current_time - record_time).total_seconds()
                timestamps.append({
                    'time': record_time,
                    'delay': time_diff,
                    'highway': record.values.get('highway', 'unknown'),
                    'vehicle_id': record.values.get('vehicle_id', 'unknown'),
                    'field': record.values.get('_field', 'unknown')
                })
        
        if timestamps:
            delays = [ts['delay'] for ts in timestamps]
            
            print(f"   📈 분석된 데이터 포인트: {len(timestamps)}개")
            print(f"   ⏱️ 지연시간 통계:")
            print(f"      최소: {min(delays):.1f}초")
            print(f"      최대: {max(delays):.1f}초") 
            print(f"      평균: {statistics.mean(delays):.1f}초")
            print(f"      중간값: {statistics.median(delays):.1f}초")
            
            # 지연시간 분포 분석
            delay_ranges = {
                "실시간 (0-5초)": 0,
                "약간 지연 (5-30초)": 0,
                "심각한 지연 (30-300초)": 0,
                "극심한 지연 (300초+)": 0
            }
            
            for delay in delays:
                if delay <= 5:
                    delay_ranges["실시간 (0-5초)"] += 1
                elif delay <= 30:
                    delay_ranges["약간 지연 (5-30초)"] += 1
                elif delay <= 300:
                    delay_ranges["심각한 지연 (30-300초)"] += 1
                else:
                    delay_ranges["극심한 지연 (300초+)"] += 1
            
            print(f"\n   📊 지연시간 분포:")
            for range_name, count in delay_ranges.items():
                percentage = (count / len(delays)) * 100
                print(f"      {range_name}: {count}개 ({percentage:.1f}%)")
            
            # 고속도로별 지연 패턴 분석
            highway_delays = {}
            for ts in timestamps:
                highway = ts['highway']
                if highway not in highway_delays:
                    highway_delays[highway] = []
                highway_delays[highway].append(ts['delay'])
            
            print(f"\n   🛣️ 고속도로별 지연 패턴:")
            for highway, delays in highway_delays.items():
                if delays:
                    avg_delay = statistics.mean(delays)
                    print(f"      {highway}: 평균 {avg_delay:.1f}초 ({len(delays)}개 샘플)")
            
            # 가장 문제가 되는 데이터 찾기
            problem_data = [ts for ts in timestamps if ts['delay'] > 60]  # 1분 이상 지연
            if problem_data:
                print(f"\n   🚨 심각한 지연 데이터 ({len(problem_data)}개):")
                for i, pd in enumerate(problem_data[:5]):  # 최대 5개만 표시
                    print(f"      {i+1}. {pd['highway']} | 차량 {pd['vehicle_id']} | {pd['delay']:.0f}초 지연")
            
            return delays
            
    except Exception as e:
        print(f"   ❌ 타임스탬프 분석 실패: {e}")
        return []
    
    finally:
        if 'client' in locals():
            client.close()

def check_simulator_data_generation():
    """시뮬레이터 데이터 생성 패턴 분석"""
    print_subsection("시뮬레이터 데이터 생성 패턴 분석")
    
    try:
        client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        query_api = client.query_api()
        
        # 실시간 데이터 생성 속도 측정
        print("   📊 실시간 데이터 생성 속도 측정 (30초 간격으로 3회)...")
        
        measurements = []
        for i in range(3):
            # 현재 레코드 수 측정
            count_query = f'''
            from(bucket: "{INFLUXDB_BUCKET}")
                |> range(start: -1m)
                |> count()
            '''
            
            result = query_api.query(query=count_query)
            current_count = sum(record.get_value() for table in result for record in table.records)
            
            measurements.append({
                'time': datetime.now(),
                'count': current_count
            })
            
            print(f"      측정 {i+1}: {current_count:,}개 레코드 (최근 1분)")
            
            if i < 2:  # 마지막 측정이 아니면 대기
                time.sleep(30)
        
        # 생성 속도 계산
        if len(measurements) >= 2:
            time_diff = (measurements[-1]['time'] - measurements[0]['time']).total_seconds()
            count_diff = measurements[-1]['count'] - measurements[0]['count']
            rate = count_diff / time_diff if time_diff > 0 else 0
            
            print(f"\n   📈 데이터 생성 속도:")
            print(f"      시간 간격: {time_diff:.0f}초")
            print(f"      레코드 증가: {count_diff:,}개")
            print(f"      생성 속도: {rate:.1f} 레코드/초")
            
            # 목표 성능과 비교
            target_rate = 100  # 목표: 초당 100개
            performance_ratio = (rate / target_rate) * 100
            
            if performance_ratio >= 90:
                print(f"      ✅ 성능 상태: 우수 ({performance_ratio:.1f}%)")
            elif performance_ratio >= 70:
                print(f"      ⚠️ 성능 상태: 보통 ({performance_ratio:.1f}%)")
            else:
                print(f"      ❌ 성능 상태: 미흡 ({performance_ratio:.1f}%)")
            
            return rate
            
    except Exception as e:
        print(f"   ❌ 시뮬레이터 분석 실패: {e}")
        return 0
    
    finally:
        if 'client' in locals():
            client.close()

def check_influxdb_performance():
    """InfluxDB 성능 및 부하 분석"""
    print_subsection("InfluxDB 성능 및 부하 분석")
    
    try:
        # 1. InfluxDB 메트릭 API 호출
        print("   📊 InfluxDB 내부 메트릭 조회...")
        
        metrics_response = requests.get(f"{INFLUXDB_URL}/metrics", timeout=10)
        if metrics_response.status_code == 200:
            metrics_text = metrics_response.text
            
            # 주요 메트릭 추출
            key_metrics = {
                'http_requests_total': 0,
                'storage_points_written_total': 0,
                'storage_wal_writes_total': 0,
                'go_memstats_heap_inuse_bytes': 0
            }
            
            for line in metrics_text.split('\n'):
                for metric_name in key_metrics.keys():
                    if line.startswith(metric_name) and not line.startswith('#'):
                        try:
                            value = float(line.split()[-1])
                            key_metrics[metric_name] = value
                        except:
                            pass
            
            print(f"      HTTP 요청 총계: {key_metrics['http_requests_total']:,.0f}")
            print(f"      저장된 포인트 총계: {key_metrics['storage_points_written_total']:,.0f}")
            print(f"      WAL 쓰기 총계: {key_metrics['storage_wal_writes_total']:,.0f}")
            print(f"      힙 메모리 사용량: {key_metrics['go_memstats_heap_inuse_bytes']/1024/1024:.1f} MB")
        
        # 2. 쿼리 성능 테스트
        print("\n   ⚡ 쿼리 성능 테스트...")
        
        client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        query_api = client.query_api()
        
        test_queries = [
            {
                'name': '단순 카운트',
                'query': f'from(bucket: "{INFLUXDB_BUCKET}") |> range(start: -1m) |> count()',
                'complexity': 'low'
            },
            {
                'name': '필터 + 집계',
                'query': f'from(bucket: "{INFLUXDB_BUCKET}") |> range(start: -5m) |> filter(fn: (r) => r["_field"] == "vehicle_speed") |> mean()',
                'complexity': 'medium'
            },
            {
                'name': '고속도로별 그룹화',
                'query': f'from(bucket: "{INFLUXDB_BUCKET}") |> range(start: -2m) |> filter(fn: (r) => r["_field"] == "vehicle_speed") |> group(columns: ["highway"]) |> count()',
                'complexity': 'high'
            }
        ]
        
        query_performance = {}
        
        for test in test_queries:
            start_time = time.time()
            try:
                result = query_api.query(query=test['query'])
                end_time = time.time()
                
                # 결과 수집
                result_count = 0
                for table in result:
                    result_count += len(table.records)
                
                execution_time = (end_time - start_time) * 1000  # 밀리초
                query_performance[test['name']] = {
                    'time_ms': execution_time,
                    'result_count': result_count,
                    'complexity': test['complexity'],
                    'status': 'success'
                }
                
                print(f"      {test['name']}: {execution_time:.1f}ms ({result_count}개 결과)")
                
            except Exception as e:
                query_performance[test['name']] = {
                    'time_ms': -1,
                    'result_count': 0,
                    'complexity': test['complexity'],
                    'status': f'error: {str(e)[:50]}'
                }
                print(f"      {test['name']}: ❌ 실패 - {str(e)[:50]}")
        
        # 성능 요약
        successful_queries = [q for q in query_performance.values() if q['status'] == 'success']
        if successful_queries:
            avg_time = statistics.mean([q['time_ms'] for q in successful_queries])
            print(f"\n      📈 쿼리 성능 요약:")
            print(f"         성공률: {len(successful_queries)}/{len(test_queries)} ({len(successful_queries)/len(test_queries)*100:.1f}%)")
            print(f"         평균 실행시간: {avg_time:.1f}ms")
            
            if avg_time < 500:
                print(f"         ✅ 성능: 우수")
            elif avg_time < 2000:
                print(f"         ⚠️ 성능: 보통")
            else:
                print(f"         ❌ 성능: 개선 필요")
        
        return query_performance
        
    except Exception as e:
        print(f"   ❌ InfluxDB 성능 분석 실패: {e}")
        return {}
    
    finally:
        if 'client' in locals():
            client.close()

def analyze_data_consistency():
    """데이터 일관성 및 품질 분석"""
    print_subsection("데이터 일관성 및 품질 분석")
    
    try:
        client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        query_api = client.query_api()
        
        # 1. 필드별 데이터 완성도 확인
        print("   📊 필드별 데이터 완성도 분석...")
        
        fields_query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -5m)
            |> group(columns: ["_field"])
            |> count()
        '''
        
        result = query_api.query(query=fields_query)
        field_counts = {}
        
        for table in result:
            for record in table.records:
                field_name = record.values.get('_field', 'unknown')
                count = record.get_value()
                field_counts[field_name] = count
        
        if field_counts:
            total_records = sum(field_counts.values())
            print(f"      총 레코드 수: {total_records:,}개")
            print(f"      필드 종류: {len(field_counts)}개")
            
            # 상위 10개 필드 표시
            sorted_fields = sorted(field_counts.items(), key=lambda x: x[1], reverse=True)
            print(f"      주요 필드별 레코드 수:")
            for i, (field, count) in enumerate(sorted_fields[:10]):
                percentage = (count / total_records) * 100
                print(f"         {i+1:2d}. {field:25s}: {count:6,}개 ({percentage:5.1f}%)")
        
        # 2. 고속도로별 데이터 균형 확인
        print(f"\n   🛣️ 고속도로별 데이터 분포 분석...")
        
        highway_query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -5m)
            |> group(columns: ["highway"])
            |> count()
        '''
        
        result = query_api.query(query=highway_query)
        highway_counts = {}
        
        for table in result:
            for record in table.records:
                highway = record.values.get('highway', 'unknown')
                count = record.get_value()
                highway_counts[highway] = count
        
        if highway_counts:
            total_highway_records = sum(highway_counts.values())
            print(f"      고속도로별 데이터 분포:")
            
            for highway, count in sorted(highway_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_highway_records) * 100
                print(f"         {highway:15s}: {count:6,}개 ({percentage:5.1f}%)")
            
            # 데이터 균형 평가
            counts = list(highway_counts.values())
            if len(counts) > 1:
                std_dev = statistics.stdev(counts)
                mean_count = statistics.mean(counts)
                cv = (std_dev / mean_count) * 100  # 변동계수
                
                print(f"\n      데이터 균형 분석:")
                print(f"         평균 레코드 수: {mean_count:.0f}")
                print(f"         표준편차: {std_dev:.0f}")
                print(f"         변동계수: {cv:.1f}%")
                
                if cv < 10:
                    print(f"         ✅ 균형 상태: 매우 좋음")
                elif cv < 25:
                    print(f"         ⚠️ 균형 상태: 보통")
                else:
                    print(f"         ❌ 균형 상태: 개선 필요")
        
        # 3. 데이터 품질 이상치 탐지
        print(f"\n   🔍 데이터 품질 이상치 탐지...")
        
        quality_checks = [
            {
                'name': '비정상적인 속도',
                'query': f'from(bucket: "{INFLUXDB_BUCKET}") |> range(start: -5m) |> filter(fn: (r) => r["_field"] == "vehicle_speed" and (r["_value"] < 0 or r["_value"] > 200)) |> count()',
                'threshold': 'anomaly'
            },
            {
                'name': '비정상적인 연비',
                'query': f'from(bucket: "{INFLUXDB_BUCKET}") |> range(start: -5m) |> filter(fn: (r) => r["_field"] == "fuel_efficiency" and (r["_value"] < 0 or r["_value"] > 50)) |> count()',
                'threshold': 'anomaly'
            }
        ]
        
        for check in quality_checks:
            try:
                result = query_api.query(query=check['query'])
                anomaly_count = sum(record.get_value() for table in result for record in table.records)
                
                if anomaly_count > 0:
                    print(f"         ⚠️ {check['name']}: {anomaly_count}개 이상치 발견")
                else:
                    print(f"         ✅ {check['name']}: 정상 범위")
                    
            except Exception as e:
                print(f"         ❌ {check['name']}: 검사 실패 - {str(e)[:30]}")
        
        return {
            'field_counts': field_counts,
            'highway_counts': highway_counts
        }
        
    except Exception as e:
        print(f"   ❌ 데이터 일관성 분석 실패: {e}")
        return {}
    
    finally:
        if 'client' in locals():
            client.close()

def suggest_optimization_solutions(analysis_results):
    """분석 결과를 바탕으로 최적화 솔루션 제안"""
    print_section("최적화 솔루션 및 권고사항")
    
    # 지연시간 문제 해결방안
    delays = analysis_results.get('delays', [])
    if delays:
        avg_delay = statistics.mean(delays)
        max_delay = max(delays)
        
        print_subsection("지연시간 문제 해결방안")
        
        if max_delay > 300:  # 5분 이상 지연
            print("   🚨 극심한 지연 문제 발견!")
            print("   📋 권고사항:")
            print("      1. 시뮬레이터 프로세스 완전 재시작")
            print("      2. InfluxDB 배치 쓰기 설정 최적화")
            print("      3. 네트워크 지연시간 점검")
            print("      4. 시스템 리소스 사용량 모니터링")
        elif avg_delay > 30:  # 30초 이상 평균 지연
            print("   ⚠️ 심각한 지연 문제 존재")
            print("   📋 권고사항:")
            print("      1. InfluxDB 쿼리 최적화")
            print("      2. 데이터 수집 주기 조정")
            print("      3. 메모리 사용량 점검")
        else:
            print("   ✅ 지연시간 대체로 양호")
    
    # 성능 최적화 권고
    data_rate = analysis_results.get('data_rate', 0)
    print_subsection("성능 최적화 권고")
    
    if data_rate < 50:  # 초당 50개 미만
        print("   ❌ 데이터 생성 속도 미흡")
        print("   📋 개선 방안:")
        print("      1. 시뮬레이터 멀티프로세싱 활용")
        print("      2. 배치 크기 증가")
        print("      3. CPU 자원 할당 증대")
    elif data_rate < 100:  # 초당 100개 미만
        print("   ⚠️ 데이터 생성 속도 보통")
        print("   📋 개선 방안:")
        print("      1. 컨커런시 설정 조정")
        print("      2. 메모리 버퍼 크기 최적화")
    else:
        print("   ✅ 데이터 생성 속도 양호")
    
    # InfluxDB 최적화 권고
    query_performance = analysis_results.get('query_performance', {})
    print_subsection("InfluxDB 최적화 권고")
    
    successful_queries = [q for q in query_performance.values() if q['status'] == 'success']
    if successful_queries:
        avg_query_time = statistics.mean([q['time_ms'] for q in successful_queries])
        
        if avg_query_time > 2000:  # 2초 이상
            print("   ❌ 쿼리 성능 미흡")
            print("   📋 최적화 방안:")
            print("      1. 인덱스 설정 최적화")
            print("      2. 샤드 지속시간 조정")
            print("      3. 압축 정책 재검토")
            print("      4. 메모리 캐시 크기 증대")
        elif avg_query_time > 500:  # 0.5초 이상
            print("   ⚠️ 쿼리 성능 보통")
            print("   📋 개선 방안:")
            print("      1. 쿼리 패턴 최적화")
            print("      2. 태그 vs 필드 구조 재검토")
        else:
            print("   ✅ 쿼리 성능 양호")
    
    # 구체적인 실행 계획 제시
    print_subsection("즉시 실행 가능한 해결 계획")
    
    print("   🎯 Phase 1: 긴급 조치 (5분 이내)")
    print("      1. 시뮬레이터 프로세스 재시작")
    print("      2. InfluxDB 연결 상태 확인")
    print("      3. 메모리/CPU 사용률 점검")
    
    print("\n   🎯 Phase 2: 설정 최적화 (30분 이내)")
    print("      1. InfluxDB 배치 크기 조정")
    print("      2. 시뮬레이터 데이터 생성 주기 최적화")
    print("      3. Grafana 쿼리 타임아웃 설정")
    
    print("\n   🎯 Phase 3: 구조적 개선 (1시간 이내)")
    print("      1. 데이터 스키마 최적화")
    print("      2. 실시간 모니터링 알람 구축")
    print("      3. 자동 복구 메커니즘 구현")

def main():
    """메인 실행 함수"""
    print("🚀 심층적 데이터 파이프라인 문제 진단 시작")
    print("="*80)
    print(f"분석 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("목적: 지연시간 1초~238초 불일치 문제의 근본 원인 파악 및 해결")
    
    analysis_results = {}
    
    try:
        # 1. 데이터 타임스탬프 분석
        print_section("1. 데이터 타임스탬프 심층 분석")
        delays = analyze_data_timestamps()
        analysis_results['delays'] = delays
        
        # 2. 시뮬레이터 성능 분석
        print_section("2. 시뮬레이터 데이터 생성 분석")
        data_rate = check_simulator_data_generation()
        analysis_results['data_rate'] = data_rate
        
        # 3. InfluxDB 성능 분석
        print_section("3. InfluxDB 성능 및 부하 분석")
        query_performance = check_influxdb_performance()
        analysis_results['query_performance'] = query_performance
        
        # 4. 데이터 일관성 분석
        print_section("4. 데이터 일관성 및 품질 분석")
        data_quality = analyze_data_consistency()
        analysis_results['data_quality'] = data_quality
        
        # 5. 최적화 솔루션 제안
        print_section("5. 최적화 솔루션 및 권고사항")
        suggest_optimization_solutions(analysis_results)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 분석이 중단되었습니다.")
    
    # 최종 진단 보고서
    print_section("🎯 심층 진단 최종 결과")
    
    # 종합 점수 계산
    scores = []
    
    # 지연시간 점수 (0-100)
    if 'delays' in analysis_results and analysis_results['delays']:
        avg_delay = statistics.mean(analysis_results['delays'])
        if avg_delay <= 5:
            delay_score = 100
        elif avg_delay <= 30:
            delay_score = 80 - (avg_delay - 5) * 2
        elif avg_delay <= 300:
            delay_score = 30 - (avg_delay - 30) * 0.1
        else:
            delay_score = 0
        scores.append(('지연시간', delay_score))
    
    # 데이터 생성 속도 점수 (0-100)
    if 'data_rate' in analysis_results:
        rate = analysis_results['data_rate']
        if rate >= 100:
            rate_score = 100
        elif rate >= 50:
            rate_score = 50 + (rate - 50) * 1
        else:
            rate_score = rate * 1
        scores.append(('데이터 생성 속도', rate_score))
    
    # 쿼리 성능 점수 (0-100)
    if 'query_performance' in analysis_results:
        qp = analysis_results['query_performance']
        successful_queries = [q for q in qp.values() if q['status'] == 'success']
        if successful_queries:
            avg_time = statistics.mean([q['time_ms'] for q in successful_queries])
            if avg_time <= 500:
                query_score = 100
            elif avg_time <= 2000:
                query_score = 80 - (avg_time - 500) * 0.04
            else:
                query_score = max(0, 20 - (avg_time - 2000) * 0.01)
            scores.append(('쿼리 성능', query_score))
    
    # 종합 점수 출력
    if scores:
        overall_score = statistics.mean([score for _, score in scores])
        
        print(f"📊 시스템 성능 종합 평가:")
        for component, score in scores:
            print(f"   {component}: {score:.1f}/100점")
        print(f"   ━━━━━━━━━━━━━━━━━━━━━━")
        print(f"   종합 점수: {overall_score:.1f}/100점")
        
        if overall_score >= 80:
            grade = "✅ 우수"
            action = "정기 모니터링 유지"
        elif overall_score >= 60:
            grade = "⚠️ 보통"
            action = "성능 최적화 권장"
        else:
            grade = "❌ 미흡"
            action = "즉시 개선 조치 필요"
        
        print(f"   평가 등급: {grade}")
        print(f"   권장 조치: {action}")
    
    # 보고서 파일 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"deep_pipeline_diagnosis_{timestamp}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"\n📁 상세 진단 보고서: {report_file}")
    print(f"🔧 다음 단계: 권고사항 기반 최적화 실행")

if __name__ == "__main__":
    main()