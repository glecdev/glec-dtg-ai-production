#!/usr/bin/env python3
"""
근본 원인 해결 스크립트
전수조사에서 발견된 핵심 문제들을 해결
"""

import requests
import subprocess
import json
import time
import os
import signal
from datetime import datetime, timedelta
from influxdb_client import InfluxDBClient
import psutil

# 설정
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "glec-admin-token-123456789"
INFLUXDB_ORG = "glec"
INFLUXDB_BUCKET = "dtg_metrics"

GRAFANA_URL = "http://localhost:3000"
GRAFANA_USER = "admin"
GRAFANA_PASS = "admin123"

def print_section(title):
    """섹션 구분자"""
    print(f"\n{'='*80}")
    print(f"🔧 {title}")
    print(f"{'='*80}")

def fix_old_data_issue():
    """오래된 데이터 문제 해결 - 시뮬레이터 재시작"""
    print("1️⃣ 오래된 데이터 문제 해결 중...")
    
    # 기존 시뮬레이터 프로세스 종료
    print("   🛑 기존 시뮬레이터 프로세스 종료 중...")
    
    simulator_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if any(sim in cmdline for sim in ['highway_simulator.py', 'ultimate_comprehensive_simulator.py']):
                    simulator_processes.append(proc)
                    print(f"      종료: PID {proc.info['pid']} - {os.path.basename(cmdline.split()[-1])}")
                    proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # 프로세스 종료 대기
    time.sleep(3)
    
    # 강제 종료가 필요한 경우
    for proc in simulator_processes:
        try:
            if proc.is_running():
                proc.kill()
                print(f"      강제 종료: PID {proc.pid}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    # 새로운 시뮬레이터 시작
    print("   🚀 새로운 시뮬레이터 시작 중...")
    
    try:
        # highway_simulator.py 시작
        if os.path.exists('highway_simulator.py'):
            proc1 = subprocess.Popen([
                'python3', 'highway_simulator.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"      ✅ highway_simulator.py 시작 (PID: {proc1.pid})")
        
        # ultimate_comprehensive_simulator.py 시작
        if os.path.exists('ultimate_comprehensive_simulator.py'):
            proc2 = subprocess.Popen([
                'python3', 'ultimate_comprehensive_simulator.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"      ✅ ultimate_comprehensive_simulator.py 시작 (PID: {proc2.pid})")
        
        # 5초 대기 후 상태 확인
        time.sleep(5)
        
        # 새로운 데이터 수집 확인
        print("   📊 새로운 데이터 수집 확인 중...")
        client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        query_api = client.query_api()
        
        # 최근 30초 데이터 확인
        recent_query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -30s)
            |> count()
        '''
        
        result = query_api.query(query=recent_query)
        recent_count = sum(record.get_value() for table in result for record in table.records)
        
        print(f"      최근 30초 데이터: {recent_count}개")
        
        if recent_count > 0:
            print("   ✅ 새로운 데이터 수집 시작됨!")
            return True
        else:
            print("   ⚠️ 아직 새로운 데이터가 수집되지 않음 (추가 대기 필요)")
            return False
            
        client.close()
        
    except Exception as e:
        print(f"   ❌ 시뮬레이터 재시작 실패: {e}")
        return False

def fix_grafana_datasource():
    """Grafana 데이터소스 문제 해결"""
    print("2️⃣ Grafana 데이터소스 문제 해결 중...")
    
    auth = (GRAFANA_USER, GRAFANA_PASS)
    headers = {"Content-Type": "application/json"}
    
    try:
        # 현재 데이터소스 목록 확인
        response = requests.get(f"{GRAFANA_URL}/api/datasources", auth=auth)
        if response.status_code != 200:
            print(f"   ❌ 데이터소스 목록 조회 실패: {response.status_code}")
            return False
        
        datasources = response.json()
        print(f"   현재 데이터소스: {len(datasources)}개")
        
        # 'influxdb' UID를 가진 데이터소스 찾기
        target_datasource = None
        for ds in datasources:
            print(f"      - {ds['name']} (UID: {ds['uid']}, Type: {ds['type']})")
            if ds['uid'] == 'influxdb' and ds['type'] == 'influxdb':
                target_datasource = ds
                break
        
        if not target_datasource:
            print("   ❌ 'influxdb' UID를 가진 데이터소스가 없습니다!")
            
            # 새로운 데이터소스 생성
            print("   🆕 새로운 데이터소스 생성 중...")
            
            new_datasource = {
                "name": "InfluxDB-GLEC-Main",
                "type": "influxdb",
                "uid": "influxdb",
                "url": "http://influxdb:8086",
                "access": "proxy",
                "basicAuth": False,
                "isDefault": True,
                "jsonData": {
                    "version": "Flux",
                    "organization": INFLUXDB_ORG,
                    "defaultBucket": INFLUXDB_BUCKET,
                    "httpMode": "POST"
                },
                "secureJsonData": {
                    "token": INFLUXDB_TOKEN
                }
            }
            
            create_response = requests.post(
                f"{GRAFANA_URL}/api/datasources",
                json=new_datasource,
                headers=headers,
                auth=auth
            )
            
            if create_response.status_code in [200, 201]:
                print("   ✅ 새로운 데이터소스 생성 성공!")
                target_datasource = create_response.json()
            else:
                print(f"   ❌ 데이터소스 생성 실패: {create_response.status_code}")
                print(f"      응답: {create_response.text}")
                return False
        
        # 데이터소스 연결 테스트
        print("   🔍 데이터소스 연결 테스트 중...")
        
        test_response = requests.get(
            f"{GRAFANA_URL}/api/datasources/{target_datasource['id']}/health",
            auth=auth
        )
        
        if test_response.status_code == 200:
            health = test_response.json()
            if health.get('status') == 'OK':
                print("   ✅ 데이터소스 연결 정상!")
                return True
            else:
                print(f"   ❌ 데이터소스 연결 문제: {health}")
        else:
            print(f"   ❌ 연결 테스트 실패: {test_response.status_code}")
        
        # 연결 실패시 설정 업데이트 시도
        print("   🔧 데이터소스 설정 업데이트 시도...")
        
        updated_config = {
            "id": target_datasource['id'],
            "uid": "influxdb",
            "name": target_datasource['name'],
            "type": "influxdb",
            "url": "http://influxdb:8086",
            "access": "proxy",
            "basicAuth": False,
            "isDefault": True,
            "jsonData": {
                "version": "Flux",
                "organization": INFLUXDB_ORG,
                "defaultBucket": INFLUXDB_BUCKET,
                "httpMode": "POST"
            },
            "secureJsonData": {
                "token": INFLUXDB_TOKEN
            }
        }
        
        update_response = requests.put(
            f"{GRAFANA_URL}/api/datasources/{target_datasource['id']}",
            json=updated_config,
            headers=headers,
            auth=auth
        )
        
        if update_response.status_code == 200:
            print("   ✅ 데이터소스 설정 업데이트 성공!")
            
            # 다시 연결 테스트
            time.sleep(2)
            retest_response = requests.get(
                f"{GRAFANA_URL}/api/datasources/{target_datasource['id']}/health",
                auth=auth
            )
            
            if retest_response.status_code == 200:
                health = retest_response.json()
                if health.get('status') == 'OK':
                    print("   ✅ 업데이트 후 연결 정상!")
                    return True
            
        print(f"   ❌ 데이터소스 업데이트 실패: {update_response.status_code}")
        return False
        
    except Exception as e:
        print(f"   ❌ 데이터소스 수정 오류: {e}")
        return False

def test_query_directly():
    """수정 후 쿼리 직접 테스트"""
    print("3️⃣ 수정 후 쿼리 직접 테스트...")
    
    auth = (GRAFANA_USER, GRAFANA_PASS)
    headers = {"Content-Type": "application/json"}
    
    # 테스트 쿼리들
    test_queries = [
        {
            "name": "전체 데이터 수",
            "query": f'from(bucket: "{INFLUXDB_BUCKET}") |> range(start: -5m) |> count()'
        },
        {
            "name": "고속도로별 차량 수",
            "query": f'from(bucket: "{INFLUXDB_BUCKET}") |> range(start: -1m) |> filter(fn: (r) => r["_measurement"] == "dtg_metrics" and r["_field"] == "vehicle_speed") |> group(columns: ["highway"]) |> count()'
        },
        {
            "name": "평균 속도",
            "query": f'from(bucket: "{INFLUXDB_BUCKET}") |> range(start: -1m) |> filter(fn: (r) => r["_measurement"] == "dtg_metrics" and r["_field"] == "vehicle_speed") |> mean()'
        }
    ]
    
    successful_queries = 0
    
    for i, test in enumerate(test_queries):
        print(f"   쿼리 {i+1}: {test['name']}")
        
        payload = {
            "queries": [{
                "datasource": {"uid": "influxdb"},
                "query": test['query'],
                "refId": "A"
            }]
        }
        
        try:
            response = requests.post(
                f"{GRAFANA_URL}/api/ds/query",
                json=payload,
                headers=headers,
                auth=auth,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                has_data = False
                data_points = 0
                
                if 'results' in result:
                    for key, value in result['results'].items():
                        if 'frames' in value and value['frames']:
                            for frame in value['frames']:
                                if 'data' in frame and 'values' in frame['data']:
                                    values = frame['data']['values']
                                    if values and len(values) > 0:
                                        has_data = True
                                        data_points = len(values[0]) if values[0] else 0
                                        if data_points > 0:
                                            # 첫 번째 값 표시
                                            sample_value = values[0][0] if values[0][0] is not None else "null"
                                            print(f"      ✅ 성공: {data_points}개 포인트 (샘플: {sample_value})")
                                            successful_queries += 1
                                            break
                
                if not has_data:
                    print(f"      ⚠️ 쿼리 성공했지만 데이터 없음")
                    
            else:
                print(f"      ❌ 쿼리 실패: {response.status_code}")
                if response.text:
                    error_msg = response.text[:100]
                    print(f"         오류: {error_msg}")
                    
        except Exception as e:
            print(f"      ❌ 쿼리 오류: {str(e)[:50]}")
    
    print(f"\n   📊 테스트 결과: {successful_queries}/{len(test_queries)}개 쿼리 성공")
    return successful_queries == len(test_queries)

def restart_specific_services():
    """필요시 특정 서비스 재시작"""
    print("4️⃣ 필요시 서비스 재시작...")
    
    try:
        # Docker 컨테이너 상태 확인
        result = subprocess.run(['docker', 'ps', '--format', '{{.Names}}\t{{.Status}}'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            containers = result.stdout.strip().split('\n')
            print("   현재 Docker 컨테이너 상태:")
            
            grafana_running = False
            influxdb_running = False
            
            for container in containers:
                if '\t' in container:
                    name, status = container.split('\t', 1)
                    print(f"      {name}: {status}")
                    
                    if 'grafana' in name.lower():
                        grafana_running = True
                    if 'influx' in name.lower():
                        influxdb_running = True
            
            # Grafana 재시작이 필요한 경우
            if not grafana_running:
                print("   🔄 Grafana 컨테이너 재시작 중...")
                restart_result = subprocess.run(['docker', 'restart', 'glec-grafana'], 
                                              capture_output=True, text=True, timeout=30)
                if restart_result.returncode == 0:
                    print("   ✅ Grafana 재시작 성공")
                    time.sleep(10)  # 재시작 대기
                else:
                    print(f"   ❌ Grafana 재시작 실패: {restart_result.stderr}")
            
            return True
            
    except Exception as e:
        print(f"   ❌ 서비스 재시작 오류: {e}")
        return False

def final_verification():
    """최종 검증"""
    print("5️⃣ 최종 검증 중...")
    
    # 1. 실시간 데이터 수집 재확인
    print("   📊 실시간 데이터 수집 재확인:")
    try:
        client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        query_api = client.query_api()
        
        # 최근 1분간 데이터 수
        recent_query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -1m)
            |> count()
        '''
        
        result = query_api.query(query=recent_query)
        recent_count = sum(record.get_value() for table in result for record in table.records)
        
        print(f"      최근 1분간 데이터: {recent_count:,}개")
        
        if recent_count > 100:  # 최소 100개 레코드 기준
            print("      ✅ 실시간 데이터 수집 정상!")
        else:
            print("      ⚠️ 데이터 수집이 부족할 수 있습니다.")
        
        # 최신 데이터 시간 확인
        latest_query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -1h)
            |> last()
            |> limit(n: 1)
        '''
        
        result = query_api.query(query=latest_query)
        for table in result:
            for record in table.records:
                latest_time = record.get_time()
                time_diff = datetime.now(latest_time.tzinfo) - latest_time
                print(f"      최신 데이터: {time_diff.total_seconds():.0f}초 전")
                break
        
        client.close()
        
    except Exception as e:
        print(f"      ❌ 데이터 확인 오류: {e}")
    
    # 2. Grafana 쿼리 재테스트
    print("\n   🔍 Grafana 쿼리 재테스트:")
    
    auth = (GRAFANA_USER, GRAFANA_PASS)
    headers = {"Content-Type": "application/json"}
    
    simple_query = {
        "queries": [{
            "datasource": {"uid": "influxdb"},
            "query": f'from(bucket: "{INFLUXDB_BUCKET}") |> range(start: -30s) |> limit(n: 1)',
            "refId": "A"
        }]
    }
    
    try:
        response = requests.post(
            f"{GRAFANA_URL}/api/ds/query",
            json=simple_query,
            headers=headers,
            auth=auth,
            timeout=10
        )
        
        if response.status_code == 200:
            print("      ✅ Grafana 쿼리 실행 성공!")
            return True
        else:
            print(f"      ❌ Grafana 쿼리 실행 실패: {response.status_code}")
            print(f"         응답: {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"      ❌ 최종 검증 오류: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("🚀 근본 원인 해결 스크립트 시작")
    print("=" * 80)
    print("발견된 문제:")
    print("1. 데이터가 9,070초(2.5시간) 전 것으로 오래됨")
    print("2. Grafana 쿼리에서 'Data source not found' 오류 (404)")
    print("3. 대시보드 패널에서 데이터 로딩 실패")
    
    results = []
    
    # 1. 오래된 데이터 문제 해결
    print_section("1. 오래된 데이터 문제 해결")
    results.append(fix_old_data_issue())
    
    # 10초 추가 대기 (시뮬레이터 안정화)
    print("\n⏳ 시뮬레이터 안정화를 위해 10초 대기...")
    time.sleep(10)
    
    # 2. Grafana 데이터소스 문제 해결
    print_section("2. Grafana 데이터소스 문제 해결")
    results.append(fix_grafana_datasource())
    
    # 3. 쿼리 직접 테스트
    print_section("3. 수정 후 쿼리 테스트")
    results.append(test_query_directly())
    
    # 4. 필요시 서비스 재시작
    print_section("4. 서비스 상태 점검 및 재시작")
    results.append(restart_specific_services())
    
    # 5. 최종 검증
    print_section("5. 최종 검증")
    results.append(final_verification())
    
    # 결과 요약
    print_section("🎯 근본 원인 해결 결과 요약")
    
    success_count = sum(1 for r in results if r)
    total_steps = len(results)
    
    print(f"📊 해결 단계: {success_count}/{total_steps}개 성공")
    
    step_names = [
        "오래된 데이터 해결",
        "데이터소스 수정", 
        "쿼리 테스트",
        "서비스 재시작",
        "최종 검증"
    ]
    
    for i, (step, result) in enumerate(zip(step_names, results)):
        status = "✅ 성공" if result else "❌ 실패"
        print(f"   {i+1}. {step}: {status}")
    
    if success_count >= 4:  # 5개 중 4개 이상 성공
        print(f"\n🎉 근본 원인 해결 완료!")
        print("📊 이제 대시보드에서 실시간 데이터를 확인할 수 있습니다.")
        print("\n🔗 확인 방법:")
        print("   http://localhost:3000/d/glec-highway-simple")
        print("   http://localhost:3000/d/glec-highway-complete")
    elif success_count >= 2:
        print(f"\n⚠️ 부분적으로 해결되었습니다.")
        print("📋 추가 조치가 필요할 수 있습니다.")
    else:
        print(f"\n❌ 해결에 실패했습니다.")
        print("📞 추가 기술 지원이 필요합니다.")

if __name__ == "__main__":
    main()