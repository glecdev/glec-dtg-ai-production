#!/usr/bin/env python3
"""
긴급 데이터 파이프라인 수정 스크립트
근본 원인: 시뮬레이터 데이터 생성 중단 및 타임스탬프 지연 문제
"""

import subprocess
import time
import os
import psutil
import signal
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient
import requests

# 설정
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "glec-admin-token-123456789"
INFLUXDB_ORG = "glec"
INFLUXDB_BUCKET = "dtg_metrics"

def print_section(title):
    """섹션 구분자"""
    print(f"\n{'='*80}")
    print(f"🚨 {title}")
    print(f"{'='*80}")

def force_restart_simulators():
    """시뮬레이터 강제 재시작"""
    print("1️⃣ 기존 시뮬레이터 프로세스 강제 종료 중...")
    
    simulator_files = [
        'highway_simulator.py',
        'ultimate_comprehensive_simulator.py',
        'scenario_based_simulator_v9_2.py'
    ]
    
    terminated_pids = []
    
    # 모든 관련 프로세스 찾기 및 종료
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if any(sim in cmdline for sim in simulator_files):
                    print(f"   🛑 종료: PID {proc.info['pid']} - {os.path.basename(cmdline.split()[-1])}")
                    proc.terminate()
                    terminated_pids.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # 종료 확인 대기 (3초)
    time.sleep(3)
    
    # 강제 종료가 필요한 프로세스 처리
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['pid'] in terminated_pids and proc.is_running():
                print(f"   💀 강제 종료: PID {proc.info['pid']}")
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    print(f"   ✅ 총 {len(terminated_pids)}개 프로세스 종료 완료")
    
    # 추가 안정화 대기
    time.sleep(2)

def clear_old_data():
    """오래된 데이터 정리 (선택적)"""
    print("2️⃣ 오래된 데이터 정리 (최근 10분만 보관)...")
    
    try:
        # InfluxDB 연결
        client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        
        # 10분 이전 데이터 삭제 (조심스럽게)
        delete_api = client.delete_api()
        
        # 삭제할 시간 범위 설정 (10분 이전)
        start_time = "1970-01-01T00:00:00Z"
        stop_time = (datetime.utcnow() - timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        print(f"   🗑️ 삭제 대상: {stop_time} 이전 데이터")
        
        # 실제 삭제는 주석 처리 (안전을 위해)
        # delete_api.delete(start_time, stop_time, '_measurement="dtg_metrics"', bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG)
        
        print(f"   ⚠️ 데이터 삭제 스킵 (안전을 위해)")
        print(f"   📋 수동으로 필요시 실행: InfluxDB UI에서 오래된 데이터 확인")
        
        client.close()
        
    except Exception as e:
        print(f"   ⚠️ 데이터 정리 실패 (정상적): {e}")

def start_optimized_simulators():
    """최적화된 설정으로 시뮬레이터 시작"""
    print("3️⃣ 최적화된 시뮬레이터 시작...")
    
    started_processes = []
    
    # highway_simulator.py 시작 (주 시뮬레이터)
    if os.path.exists('highway_simulator.py'):
        try:
            print("   🚀 highway_simulator.py 시작 중...")
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'  # 실시간 출력
            
            proc = subprocess.Popen([
                'python3', 'highway_simulator.py'
            ], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            env=env)
            
            started_processes.append(('highway_simulator.py', proc))
            print(f"      ✅ 시작 완료: PID {proc.pid}")
            
        except Exception as e:
            print(f"      ❌ 시작 실패: {e}")
    
    # 잠시 대기 (첫 번째 시뮬레이터 안정화)
    time.sleep(3)
    
    # ultimate_comprehensive_simulator.py 시작 (보조 시뮬레이터)
    if os.path.exists('ultimate_comprehensive_simulator.py'):
        try:
            print("   🚀 ultimate_comprehensive_simulator.py 시작 중...")
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            
            proc = subprocess.Popen([
                'python3', 'ultimate_comprehensive_simulator.py'
            ],
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            env=env)
            
            started_processes.append(('ultimate_comprehensive_simulator.py', proc))
            print(f"      ✅ 시작 완료: PID {proc.pid}")
            
        except Exception as e:
            print(f"      ❌ 시작 실패: {e}")
    
    print(f"   📊 총 {len(started_processes)}개 시뮬레이터 시작")
    
    # 시뮬레이터 안정화 대기 (10초)
    print("   ⏳ 시뮬레이터 안정화 대기 (10초)...")
    time.sleep(10)
    
    # 프로세스 상태 확인
    print("   🔍 시뮬레이터 상태 확인:")
    for name, proc in started_processes:
        if proc.poll() is None:  # 여전히 실행 중
            print(f"      ✅ {name}: 정상 실행 중 (PID: {proc.pid})")
        else:
            print(f"      ❌ {name}: 종료됨 (코드: {proc.returncode})")
            try:
                stdout, stderr = proc.communicate(timeout=1)
                if stderr:
                    print(f"         오류: {stderr.decode()[:100]}")
            except:
                pass
    
    return started_processes

def verify_data_generation():
    """새로운 데이터 생성 확인"""
    print("4️⃣ 새로운 데이터 생성 확인...")
    
    try:
        client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        query_api = client.query_api()
        
        # 첫 번째 측정
        initial_query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -30s)
            |> count()
        '''
        
        result1 = query_api.query(query=initial_query)
        count1 = sum(record.get_value() for table in result1 for record in table.records)
        print(f"   📊 초기 레코드 수 (30초간): {count1:,}개")
        
        # 15초 대기
        print("   ⏳ 15초 대기 후 재측정...")
        time.sleep(15)
        
        # 두 번째 측정
        result2 = query_api.query(query=initial_query)
        count2 = sum(record.get_value() for table in result2 for record in table.records)
        print(f"   📊 15초 후 레코드 수 (30초간): {count2:,}개")
        
        # 데이터 증가율 계산
        if count2 > count1:
            increase = count2 - count1
            rate = increase / 15  # 초당 증가율
            print(f"   ✅ 새로운 데이터 생성 확인!")
            print(f"      증가량: {increase:,}개")
            print(f"      생성 속도: {rate:.1f} 레코드/초")
            
            if rate >= 50:
                print(f"      🎯 성능: 우수")
            elif rate >= 20:
                print(f"      ⚠️ 성능: 보통")
            else:
                print(f"      ❌ 성능: 개선 필요")
                
            return True
        else:
            print(f"   ❌ 새로운 데이터 생성이 확인되지 않음!")
            print(f"   📋 추가 디버깅 필요")
            return False
        
    except Exception as e:
        print(f"   ❌ 데이터 생성 확인 실패: {e}")
        return False
    
    finally:
        if 'client' in locals():
            client.close()

def test_realtime_data_freshness():
    """실시간 데이터 신선도 테스트"""
    print("5️⃣ 실시간 데이터 신선도 테스트...")
    
    try:
        client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        query_api = client.query_api()
        
        # 최신 데이터의 타임스탬프 확인
        latest_query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -5m)
            |> last()
            |> limit(n: 5)
        '''
        
        result = query_api.query(query=latest_query)
        current_time = datetime.now().astimezone()
        
        fresh_data_count = 0
        total_data_count = 0
        
        print(f"   🔍 최신 5개 데이터포인트 신선도:")
        
        for table in result:
            for record in table.records:
                total_data_count += 1
                record_time = record.get_time()
                time_diff = (current_time - record_time).total_seconds()
                
                highway = record.values.get('highway', 'unknown')
                vehicle_id = record.values.get('vehicle_id', 'unknown')
                field = record.values.get('_field', 'unknown')
                
                if time_diff <= 30:  # 30초 이내면 신선
                    fresh_data_count += 1
                    status = "✅ 신선"
                elif time_diff <= 120:  # 2분 이내면 보통
                    status = "⚠️ 보통"
                else:  # 2분 이상이면 오래됨
                    status = "❌ 오래됨"
                
                print(f"      {highway[:8]:8s} | {vehicle_id[:12]:12s} | {field[:15]:15s} | {time_diff:5.0f}초 전 | {status}")
        
        # 신선도 요약
        if total_data_count > 0:
            freshness_ratio = (fresh_data_count / total_data_count) * 100
            print(f"\n   📊 데이터 신선도 요약:")
            print(f"      신선한 데이터: {fresh_data_count}/{total_data_count}개 ({freshness_ratio:.1f}%)")
            
            if freshness_ratio >= 80:
                print(f"      ✅ 신선도 평가: 우수")
                return True
            elif freshness_ratio >= 50:
                print(f"      ⚠️ 신선도 평가: 보통")
                return True
            else:
                print(f"      ❌ 신선도 평가: 미흡")
                return False
        else:
            print(f"   ❌ 데이터를 찾을 수 없음")
            return False
    
    except Exception as e:
        print(f"   ❌ 신선도 테스트 실패: {e}")
        return False
    
    finally:
        if 'client' in locals():
            client.close()

def verify_grafana_connectivity():
    """Grafana 연결 및 쿼리 테스트"""
    print("6️⃣ Grafana 연결 및 쿼리 테스트...")
    
    try:
        # Grafana 서비스 상태 확인
        response = requests.get("http://localhost:3000/api/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Grafana 서비스 정상")
        else:
            print(f"   ❌ Grafana 서비스 문제: {response.status_code}")
            return False
        
        # 간단한 쿼리 테스트
        auth = ('admin', 'admin123')
        headers = {'Content-Type': 'application/json'}
        
        test_payload = {
            "queries": [{
                "datasource": {"uid": "influxdb"},
                "query": f'from(bucket: "{INFLUXDB_BUCKET}") |> range(start: -1m) |> limit(n: 1)',
                "refId": "A"
            }]
        }
        
        query_response = requests.post(
            "http://localhost:3000/api/ds/query",
            json=test_payload,
            headers=headers,
            auth=auth,
            timeout=10
        )
        
        if query_response.status_code == 200:
            print("   ✅ Grafana 쿼리 테스트 성공")
            return True
        else:
            print(f"   ❌ Grafana 쿼리 테스트 실패: {query_response.status_code}")
            if query_response.text:
                print(f"      오류: {query_response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Grafana 연결 테스트 실패: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("🚨 긴급 데이터 파이프라인 수정 스크립트 시작")
    print("="*80)
    print("발견된 근본 원인:")
    print("1. 시뮬레이터 데이터 생성 완전 중단 (0 레코드/초)")
    print("2. 평균 150.8초 지연된 오래된 데이터만 존재")
    print("3. 실시간 데이터 신선도 심각하게 저하")
    
    results = []
    
    # 긴급 수정 단계들 실행
    print_section("PHASE 1: 긴급 복구 조치")
    
    # 1. 시뮬레이터 강제 재시작
    force_restart_simulators()
    
    # 2. 오래된 데이터 정리 (선택적)
    clear_old_data()
    
    # 3. 최적화된 시뮬레이터 시작
    started_processes = start_optimized_simulators()
    
    print_section("PHASE 2: 복구 검증")
    
    # 4. 새로운 데이터 생성 확인
    data_gen_success = verify_data_generation()
    results.append(("데이터 생성", data_gen_success))
    
    # 5. 데이터 신선도 테스트
    freshness_success = test_realtime_data_freshness()
    results.append(("데이터 신선도", freshness_success))
    
    # 6. Grafana 연결 테스트
    grafana_success = verify_grafana_connectivity()
    results.append(("Grafana 연결", grafana_success))
    
    print_section("🎯 긴급 수정 결과")
    
    # 결과 요약
    success_count = sum(1 for _, success in results if success)
    total_tests = len(results)
    
    print(f"📊 수정 결과: {success_count}/{total_tests}개 테스트 성공")
    
    for test_name, success in results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"   {test_name}: {status}")
    
    # 시뮬레이터 상태 최종 확인
    print(f"\n🔍 실행 중인 시뮬레이터:")
    running_simulators = 0
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if any(sim in cmdline for sim in ['highway_simulator.py', 'ultimate_comprehensive_simulator.py']):
                    name = os.path.basename(cmdline.split()[-1])
                    print(f"   ✅ PID {proc.info['pid']}: {name}")
                    running_simulators += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # 최종 평가
    if success_count >= 2 and running_simulators >= 1:
        print(f"\n🎉 긴급 수정 성공!")
        print(f"📊 상태:")
        print(f"   - 실행 중인 시뮬레이터: {running_simulators}개")
        print(f"   - 성공한 테스트: {success_count}/{total_tests}개")
        print(f"\n🔗 확인 방법:")
        print(f"   http://localhost:3000/d/glec-highway-simple")
        print(f"   http://localhost:3000/d/glec-highway-complete")
    elif success_count >= 1:
        print(f"\n⚠️ 부분적 수정 완료")
        print(f"📋 추가 모니터링이 필요합니다.")
        print(f"📊 권장사항: 10분 후 데이터 상태 재확인")
    else:
        print(f"\n❌ 긴급 수정 실패")
        print(f"📞 추가 기술 지원이 필요합니다.")
    
    print(f"\n⏰ 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()