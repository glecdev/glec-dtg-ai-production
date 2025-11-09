#!/usr/bin/env python3
"""
근본적인 데이터 연동 문제 전수 조사 스크립트
모든 구성요소를 체계적으로 검증
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
    print(f"🔍 {title}")
    print(f"{'='*80}")

def print_subsection(title):
    """서브섹션 구분자"""
    print(f"\n{'-'*60}")
    print(f"📋 {title}")
    print(f"{'-'*60}")

def check_process_status():
    """실행 중인 프로세스 상태 확인"""
    print_subsection("시스템 프로세스 상태 확인")
    
    # 필수 프로세스 목록
    required_processes = [
        "influxd",
        "grafana",
        "python",
    ]
    
    running_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
        try:
            pinfo = proc.info
            running_processes.append(pinfo)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    print("🔍 실행 중인 관련 프로세스:")
    for proc in running_processes:
        if any(req in proc['name'].lower() for req in ['influx', 'grafana', 'python']) or \
           (proc['cmdline'] and any('simulator' in str(cmd) for cmd in proc['cmdline'])):
            print(f"   PID {proc['pid']}: {proc['name']}")
            if proc['cmdline']:
                cmdline = ' '.join(proc['cmdline'][:3]) + ('...' if len(proc['cmdline']) > 3 else '')
                print(f"      명령: {cmdline}")
            print(f"      CPU: {proc['cpu_percent']:.1f}% | 메모리: {proc['memory_percent']:.1f}%")
    
    # Docker 컨테이너 확인
    print("\n🐳 Docker 컨테이너 상태:")
    try:
        result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("   Docker가 실행되지 않거나 접근할 수 없습니다.")
    except Exception as e:
        print(f"   Docker 상태 확인 실패: {e}")

def check_influxdb_detailed():
    """InfluxDB 상세 상태 확인"""
    print_subsection("InfluxDB 상세 검증")
    
    # 1. InfluxDB 서비스 상태
    print("1️⃣ InfluxDB 서비스 연결 테스트:")
    try:
        response = requests.get(f"{INFLUXDB_URL}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ InfluxDB 서비스 정상: {health}")
        else:
            print(f"   ❌ InfluxDB 서비스 오류: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ InfluxDB 연결 실패: {e}")
        return False
    
    # 2. 데이터베이스 연결 및 인증 테스트
    print("\n2️⃣ InfluxDB 인증 및 버킷 확인:")
    try:
        client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        
        # 조직 확인
        orgs_api = client.organizations_api()
        orgs = orgs_api.find_organizations()
        org_names = [org.name for org in orgs]
        print(f"   조직 목록: {org_names}")
        
        # 버킷 확인
        buckets_api = client.buckets_api()
        buckets = buckets_api.find_buckets()
        bucket_names = [bucket.name for bucket in buckets.buckets]
        print(f"   버킷 목록: {bucket_names}")
        
        if INFLUXDB_BUCKET not in bucket_names:
            print(f"   ❌ 대상 버킷 '{INFLUXDB_BUCKET}' 없음!")
            return False
        else:
            print(f"   ✅ 대상 버킷 '{INFLUXDB_BUCKET}' 존재")
            
    except Exception as e:
        print(f"   ❌ InfluxDB 인증 실패: {e}")
        return False
    
    # 3. 실제 데이터 존재 여부 확인
    print("\n3️⃣ 실제 데이터 존재 여부:")
    try:
        query_api = client.query_api()
        
        # 전체 레코드 수
        total_query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -1h)
            |> count()
            |> yield(name: "total")
        '''
        
        result = query_api.query(query=total_query)
        total_count = 0
        for table in result:
            for record in table.records:
                total_count += record.get_value()
        
        print(f"   총 레코드 수 (1시간): {total_count:,}개")
        
        if total_count == 0:
            print("   ❌ 데이터가 전혀 없습니다!")
            return False
        
        # 최신 데이터 시간 확인
        latest_query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -24h)
            |> last()
            |> limit(n: 1)
        '''
        
        result = query_api.query(query=latest_query)
        latest_time = None
        for table in result:
            for record in table.records:
                latest_time = record.get_time()
                break
            if latest_time:
                break
        
        if latest_time:
            time_diff = datetime.now(latest_time.tzinfo) - latest_time
            print(f"   최신 데이터: {latest_time.strftime('%Y-%m-%d %H:%M:%S')} ({time_diff.total_seconds():.0f}초 전)")
            
            if time_diff.total_seconds() > 300:  # 5분 이상 오래된 데이터
                print("   ⚠️ 데이터가 5분 이상 오래되었습니다!")
                return False
        
        client.close()
        return True
        
    except Exception as e:
        print(f"   ❌ 데이터 조회 실패: {e}")
        return False

def check_grafana_detailed():
    """Grafana 상세 상태 확인"""
    print_subsection("Grafana 상세 검증")
    
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    # 1. Grafana 서비스 상태
    print("1️⃣ Grafana 서비스 연결:")
    try:
        response = requests.get(f"{GRAFANA_URL}/api/health", auth=auth, timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"   ✅ Grafana 서비스 정상: {health}")
        else:
            print(f"   ❌ Grafana 서비스 오류: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Grafana 연결 실패: {e}")
        return False
    
    # 2. 데이터소스 상태 확인
    print("\n2️⃣ 데이터소스 연결 상태:")
    try:
        response = requests.get(f"{GRAFANA_URL}/api/datasources", auth=auth)
        if response.status_code == 200:
            datasources = response.json()
            
            influxdb_found = False
            for ds in datasources:
                print(f"   데이터소스: {ds['name']} ({ds['type']}) - {ds['url']}")
                
                if ds['type'] == 'influxdb':
                    influxdb_found = True
                    # 연결 테스트
                    test_response = requests.get(f"{GRAFANA_URL}/api/datasources/{ds['id']}/health", auth=auth)
                    if test_response.status_code == 200:
                        health = test_response.json()
                        status = "✅ 정상" if health.get('status') == 'OK' else f"❌ 오류: {health}"
                        print(f"      연결 상태: {status}")
                    else:
                        print(f"      연결 상태: ❌ 테스트 실패 ({test_response.status_code})")
            
            if not influxdb_found:
                print("   ❌ InfluxDB 데이터소스가 설정되지 않았습니다!")
                return False
                
        else:
            print(f"   ❌ 데이터소스 목록 조회 실패: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 데이터소스 확인 실패: {e}")
        return False
    
    # 3. 대시보드 목록 확인
    print("\n3️⃣ 대시보드 존재 여부:")
    try:
        response = requests.get(f"{GRAFANA_URL}/api/search?query=glec", auth=auth)
        if response.status_code == 200:
            dashboards = response.json()
            print(f"   GLEC 관련 대시보드: {len(dashboards)}개")
            
            for db in dashboards[:5]:  # 최대 5개까지 표시
                print(f"      - {db['title']} (UID: {db['uid']})")
                
        else:
            print(f"   ❌ 대시보드 검색 실패: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ 대시보드 확인 실패: {e}")
    
    return True

def check_simulators():
    """시뮬레이터 실행 상태 확인"""
    print_subsection("시뮬레이터 실행 상태 확인")
    
    # 시뮬레이터 파일 목록
    simulator_files = [
        "highway_simulator.py",
        "ultimate_comprehensive_simulator.py", 
        "scenario_based_simulator_v9_2.py"
    ]
    
    print("1️⃣ 시뮬레이터 파일 존재 여부:")
    existing_simulators = []
    for sim_file in simulator_files:
        if os.path.exists(sim_file):
            print(f"   ✅ {sim_file} 존재")
            existing_simulators.append(sim_file)
        else:
            print(f"   ❌ {sim_file} 없음")
    
    # 실행 중인 시뮬레이터 확인
    print("\n2️⃣ 실행 중인 시뮬레이터:")
    running_simulators = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline']:
                cmdline = ' '.join(proc.info['cmdline'])
                if any(sim in cmdline for sim in simulator_files):
                    running_simulators.append(proc.info)
                    print(f"   ✅ PID {proc.info['pid']}: {os.path.basename(cmdline.split()[-1])}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    if not running_simulators:
        print("   ❌ 실행 중인 시뮬레이터가 없습니다!")
        
        # 시뮬레이터 자동 시작 시도
        print("\n3️⃣ 시뮬레이터 자동 시작 시도:")
        for sim_file in existing_simulators:
            if "highway" in sim_file:  # highway_simulator.py 우선
                try:
                    print(f"   🚀 {sim_file} 시작 중...")
                    proc = subprocess.Popen([
                        'python3', sim_file
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    
                    # 3초 대기 후 프로세스 상태 확인
                    time.sleep(3)
                    if proc.poll() is None:
                        print(f"   ✅ {sim_file} 시작 성공 (PID: {proc.pid})")
                        return True
                    else:
                        stdout, stderr = proc.communicate()
                        print(f"   ❌ {sim_file} 시작 실패")
                        if stderr:
                            print(f"      오류: {stderr.decode()[:200]}")
                except Exception as e:
                    print(f"   ❌ {sim_file} 시작 실패: {e}")
        
        return False
    
    return True

def test_data_pipeline():
    """데이터 파이프라인 end-to-end 테스트"""
    print_subsection("데이터 파이프라인 End-to-End 테스트")
    
    print("1️⃣ 실시간 데이터 수집 테스트:")
    try:
        client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
        query_api = client.query_api()
        
        # 현재 시점 레코드 수 측정
        count_query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -30s)
            |> count()
        '''
        
        result1 = query_api.query(query=count_query)
        count1 = sum(record.get_value() for table in result1 for record in table.records)
        
        print(f"   초기 레코드 수 (30초간): {count1}개")
        
        # 10초 대기
        print("   ⏳ 10초 대기 중...")
        time.sleep(10)
        
        # 다시 측정
        result2 = query_api.query(query=count_query)
        count2 = sum(record.get_value() for table in result2 for record in table.records)
        
        print(f"   10초 후 레코드 수 (30초간): {count2}개")
        
        if count2 > count1:
            rate = (count2 - count1) / 10  # 초당 레코드 수
            print(f"   ✅ 실시간 데이터 수집 중: {rate:.1f} 레코드/초")
        else:
            print("   ❌ 새로운 데이터가 수집되지 않음!")
            return False
        
        client.close()
        
    except Exception as e:
        print(f"   ❌ 데이터 수집 테스트 실패: {e}")
        return False
    
    # 2. Grafana에서 실제 쿼리 테스트
    print("\n2️⃣ Grafana 쿼리 실행 테스트:")
    try:
        auth = (GRAFANA_USER, GRAFANA_PASS)
        headers = {"Content-Type": "application/json"}
        
        # 테스트 쿼리
        test_payload = {
            "queries": [{
                "datasource": {"uid": "influxdb"},
                "query": 'from(bucket: "dtg_metrics") |> range(start: -1m) |> filter(fn: (r) => r["_measurement"] == "dtg_metrics" and r["_field"] == "vehicle_speed") |> mean()',
                "refId": "A"
            }]
        }
        
        response = requests.post(
            f"{GRAFANA_URL}/api/ds/query",
            json=test_payload,
            headers=headers,
            auth=auth,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Grafana 쿼리 실행 성공")
            
            # 결과 분석
            has_data = False
            if 'results' in result:
                for key, value in result['results'].items():
                    if 'frames' in value and value['frames']:
                        for frame in value['frames']:
                            if 'data' in frame and 'values' in frame['data']:
                                values = frame['data']['values']
                                if values and len(values) > 0 and len(values[0]) > 0:
                                    has_data = True
                                    avg_speed = values[0][0] if values[0][0] is not None else 0
                                    print(f"      평균 속도: {avg_speed:.1f} km/h")
            
            if not has_data:
                print("   ⚠️ 쿼리는 성공했지만 데이터가 없습니다")
                return False
                
        else:
            print(f"   ❌ Grafana 쿼리 실패: {response.status_code}")
            print(f"      응답: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Grafana 쿼리 테스트 실패: {e}")
        return False
    
    return True

def test_dashboard_panels():
    """실제 대시보드 패널에서 데이터 로딩 테스트"""
    print_subsection("대시보드 패널 데이터 로딩 테스트")
    
    dashboard_uids = [
        "glec-highway-simple",
        "glec-highway-complete"
    ]
    
    auth = (GRAFANA_USER, GRAFANA_PASS)
    
    for uid in dashboard_uids:
        print(f"\n📊 대시보드 테스트: {uid}")
        
        try:
            # 대시보드 정보 가져오기
            response = requests.get(f"{GRAFANA_URL}/api/dashboards/uid/{uid}", auth=auth)
            
            if response.status_code != 200:
                print(f"   ❌ 대시보드 접근 실패: {response.status_code}")
                continue
            
            dashboard_data = response.json()
            dashboard = dashboard_data.get('dashboard', {})
            panels = dashboard.get('panels', [])
            
            print(f"   대시보드: {dashboard.get('title', 'Unknown')}")
            print(f"   패널 수: {len(panels)}개")
            
            # 처음 3개 패널의 쿼리 테스트
            working_panels = 0
            for i, panel in enumerate(panels[:5]):  # 최대 5개 패널 테스트
                if panel.get('type') in ['timeseries', 'stat', 'gauge'] and panel.get('targets'):
                    target = panel['targets'][0]
                    query = target.get('query', '')
                    
                    if query and 'from(bucket:' in query:
                        print(f"      패널 {i+1}: {panel.get('title', 'Untitled')}")
                        
                        # 쿼리에서 v.변수들 실제 값으로 교체
                        test_query = query.replace('v.timeRangeStart', '-5m') \
                                         .replace('v.timeRangeStop', 'now()') \
                                         .replace('v.windowPeriod', '10s')
                        
                        # Grafana를 통해 쿼리 실행
                        test_payload = {
                            "queries": [{
                                "datasource": {"uid": "influxdb"},
                                "query": test_query,
                                "refId": "A"
                            }]
                        }
                        
                        try:
                            query_response = requests.post(
                                f"{GRAFANA_URL}/api/ds/query",
                                json=test_payload,
                                headers={"Content-Type": "application/json"},
                                auth=auth,
                                timeout=10
                            )
                            
                            if query_response.status_code == 200:
                                result = query_response.json()
                                has_data = False
                                
                                if 'results' in result:
                                    for key, value in result['results'].items():
                                        if 'frames' in value and value['frames']:
                                            for frame in value['frames']:
                                                if 'data' in frame and 'values' in frame['data']:
                                                    values = frame['data']['values']
                                                    if values and len(values) > 0 and len(values[0]) > 0:
                                                        has_data = True
                                
                                if has_data:
                                    print(f"         ✅ 데이터 로딩 성공")
                                    working_panels += 1
                                else:
                                    print(f"         ❌ 데이터 없음")
                            else:
                                print(f"         ❌ 쿼리 실패 ({query_response.status_code})")
                                
                        except Exception as e:
                            print(f"         ❌ 쿼리 오류: {str(e)[:50]}")
            
            print(f"   작동하는 패널: {working_panels}/{min(5, len([p for p in panels if p.get('targets')]))}개")
            
        except Exception as e:
            print(f"   ❌ 대시보드 테스트 실패: {e}")

def generate_diagnosis_report():
    """진단 결과 종합 보고서 생성"""
    print_section("종합 진단 보고서 생성")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"data_connection_diagnosis_{timestamp}.md"
    
    report_content = f"""# 🔍 GLEC DTG 데이터 연동 전수 조사 보고서

## 📊 조사 개요
- **조사 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **조사 목적**: "여전히 데이터 연동이 되지 않고 있어" 문제의 근본 원인 파악
- **조사 범위**: 전체 데이터 파이프라인 (시뮬레이터 → InfluxDB → Grafana → 대시보드)

## 🔧 조사 결과 요약
실행된 전체 검증 단계들의 결과가 여기에 기록됩니다.

## 📋 권장 조치사항
1. 즉시 조치 필요 항목
2. 단기 개선 사항
3. 장기 모니터링 필요 사항

## 🎯 다음 단계
근본 원인에 따른 구체적 해결 방안

---
*자동 생성된 진단 보고서*
"""
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"📁 진단 보고서 생성: {report_file}")
    return report_file

def main():
    """메인 실행 함수"""
    print("🚀 GLEC DTG 데이터 연동 문제 전수 조사 시작")
    print("=" * 80)
    print(f"조사 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("목적: 근본적인 데이터 연동 문제 해결을 위한 전체 시스템 검증")
    
    # 전수 조사 실행
    results = {}
    
    try:
        # 1. 프로세스 상태 확인
        print_section("1. 시스템 프로세스 상태 분석")
        check_process_status()
        
        # 2. InfluxDB 상세 검증
        print_section("2. InfluxDB 상세 검증")
        results['influxdb'] = check_influxdb_detailed()
        
        # 3. Grafana 상세 검증
        print_section("3. Grafana 상세 검증")
        results['grafana'] = check_grafana_detailed()
        
        # 4. 시뮬레이터 상태 확인
        print_section("4. 시뮬레이터 상태 확인")
        results['simulators'] = check_simulators()
        
        # 5. 데이터 파이프라인 테스트
        print_section("5. 데이터 파이프라인 End-to-End 테스트")
        results['pipeline'] = test_data_pipeline()
        
        # 6. 대시보드 패널 테스트
        print_section("6. 대시보드 패널 데이터 로딩 테스트")
        test_dashboard_panels()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 조사가 중단되었습니다.")
    
    # 최종 결과 요약
    print_section("🎯 전수 조사 최종 결과")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"📊 검증 결과: {passed}/{total}개 구성요소 정상")
    
    for component, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {component}: {'정상' if status else '문제 있음'}")
    
    if passed < total:
        print(f"\n🚨 근본 문제 발견: {total - passed}개 구성요소에서 문제 확인됨")
        print("📋 즉시 해결이 필요합니다.")
    else:
        print(f"\n🎉 모든 구성요소가 정상 작동 중입니다.")
        print("🔍 추가 디버깅이 필요할 수 있습니다.")
    
    # 보고서 생성
    report_file = generate_diagnosis_report()
    print(f"\n📁 상세 진단 보고서: {report_file}")

if __name__ == "__main__":
    main()