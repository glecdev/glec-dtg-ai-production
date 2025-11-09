#!/usr/bin/env python3
"""
고속도로별 대시보드 쿼리 테스트
"""

from influxdb_client import InfluxDBClient
from datetime import datetime, timedelta
import time

# InfluxDB 설정
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "glec-admin-token-123456789"
INFLUXDB_ORG = "glec"
INFLUXDB_BUCKET = "dtg_metrics"

def test_highway_queries():
    """고속도로별 쿼리 테스트"""
    print("🔍 고속도로별 대시보드 쿼리 테스트...")
    print("=" * 60)
    
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    query_api = client.query_api()
    
    # 1. 태그 확인
    print("\n1️⃣ 사용 가능한 태그 확인:")
    tag_query = f'''
    import "influxdata/influxdb/schema"
    schema.tagKeys(bucket: "{INFLUXDB_BUCKET}")
    '''
    
    try:
        result = query_api.query(query=tag_query)
        tags = []
        for table in result:
            for record in table.records:
                tags.append(record.get_value())
        print(f"   태그: {', '.join(tags)}")
    except Exception as e:
        print(f"   ❌ 태그 조회 오류: {e}")
    
    # 2. highway 태그 값 확인
    print("\n2️⃣ highway 태그 값 확인:")
    highway_query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -5m)
        |> filter(fn: (r) => r["_measurement"] == "dtg_metrics")
        |> keep(columns: ["highway"])
        |> distinct(column: "highway")
    '''
    
    try:
        result = query_api.query(query=highway_query)
        highways = []
        for table in result:
            for record in table.records:
                highway = record.values.get("highway")
                if highway:
                    highways.append(highway)
        
        highways = list(set(highways))
        print(f"   고속도로: {', '.join(highways)}")
    except Exception as e:
        print(f"   ❌ 고속도로 조회 오류: {e}")
    
    # 3. 각 고속도로별 데이터 수 확인
    print("\n3️⃣ 고속도로별 데이터 수 (최근 1분):")
    
    highways_to_test = ["경부고속도로", "서해안고속도로", "호남고속도로", "영동고속도로", "중부고속도로"]
    
    for highway in highways_to_test:
        count_query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
            |> range(start: -1m)
            |> filter(fn: (r) => r["_measurement"] == "dtg_metrics")
            |> filter(fn: (r) => r["highway"] == "{highway}")
            |> filter(fn: (r) => r["_field"] == "vehicle_speed")
            |> count()
        '''
        
        try:
            result = query_api.query(query=count_query)
            count = 0
            for table in result:
                for record in table.records:
                    count += record.get_value()
            print(f"   {highway}: {count}개")
        except Exception as e:
            print(f"   {highway}: ❌ 오류 - {e}")
    
    # 4. 샘플 쿼리 테스트 (대시보드에서 사용하는 형식)
    print("\n4️⃣ 대시보드 쿼리 형식 테스트:")
    
    # 경부고속도로 평균 속도
    dashboard_query = f'''
    from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -5m)
        |> filter(fn: (r) => r["_measurement"] == "dtg_metrics")
        |> filter(fn: (r) => r["highway"] == "경부고속도로")
        |> filter(fn: (r) => r["_field"] == "vehicle_speed")
        |> aggregateWindow(every: 10s, fn: mean, createEmpty: false)
        |> yield(name: "mean")
    '''
    
    try:
        result = query_api.query(query=dashboard_query)
        points = 0
        last_value = None
        last_time = None
        
        for table in result:
            for record in table.records:
                points += 1
                last_value = record.get_value()
                last_time = record.get_time()
        
        if points > 0:
            print(f"   ✅ 경부고속도로 평균속도 쿼리 성공")
            print(f"      데이터 포인트: {points}개")
            if last_value and last_time:
                print(f"      최신 데이터: {last_value:.1f} km/h @ {last_time.strftime('%H:%M:%S')}")
        else:
            print(f"   ❌ 경부고속도로 평균속도 쿼리 실패 - 데이터 없음")
    except Exception as e:
        print(f"   ❌ 쿼리 오류: {e}")
    
    # 5. 모든 필드 확인
    print("\n5️⃣ 사용 가능한 필드 확인:")
    field_query = f'''
    import "influxdata/influxdb/schema"
    schema.fieldKeys(bucket: "{INFLUXDB_BUCKET}")
    '''
    
    try:
        result = query_api.query(query=field_query)
        fields = []
        for table in result:
            for record in table.records:
                fields.append(record.get_value())
        print(f"   필드 ({len(fields)}개): {', '.join(fields[:10])}...")
    except Exception as e:
        print(f"   ❌ 필드 조회 오류: {e}")
    
    client.close()

def test_specific_panel_query():
    """특정 패널 쿼리 테스트"""
    print("\n\n6️⃣ 특정 패널 쿼리 직접 테스트:")
    
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    query_api = client.query_api()
    
    # 경부고속도로 실시간 속도 차트 쿼리
    test_queries = [
        {
            "name": "경부고속도로 실시간 속도",
            "query": '''from(bucket: "dtg_metrics")
  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
  |> filter(fn: (r) => r["_measurement"] == "dtg_metrics")
  |> filter(fn: (r) => r["highway"] == "경부고속도로")
  |> filter(fn: (r) => r["_field"] == "vehicle_speed")
  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)'''
        },
        {
            "name": "경부고속도로 차량별 속도",
            "query": '''from(bucket: "dtg_metrics")
  |> range(start: -5m)
  |> filter(fn: (r) => r["_measurement"] == "dtg_metrics")
  |> filter(fn: (r) => r["highway"] == "경부고속도로")
  |> filter(fn: (r) => r["_field"] == "vehicle_speed")
  |> group(columns: ["vehicle_id"])'''
        }
    ]
    
    for test in test_queries:
        print(f"\n   테스트: {test['name']}")
        # v.timeRangeStart를 실제 시간으로 대체
        query = test['query'].replace('v.timeRangeStart', '-5m').replace('v.timeRangeStop', 'now()').replace('v.windowPeriod', '10s')
        
        try:
            result = query_api.query(query=query)
            records = 0
            vehicles = set()
            
            for table in result:
                for record in table.records:
                    records += 1
                    vehicle = record.values.get("vehicle_id")
                    if vehicle:
                        vehicles.add(vehicle)
            
            print(f"      ✅ 성공: {records}개 레코드")
            if vehicles:
                print(f"      차량: {', '.join(list(vehicles)[:5])}...")
        except Exception as e:
            print(f"      ❌ 실패: {e}")
    
    client.close()

def main():
    """메인 함수"""
    print("🚀 고속도로별 대시보드 데이터 연동 문제 진단")
    print("=" * 60)
    print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 쿼리 테스트
    test_highway_queries()
    test_specific_panel_query()
    
    print("\n\n🔧 문제 해결 방안:")
    print("1. 대시보드의 데이터소스가 'influxdb'로 설정되어 있는지 확인")
    print("2. 쿼리에서 bucket 이름이 'dtg_metrics'인지 확인")
    print("3. highway 태그 필터가 정확한 한글 이름과 일치하는지 확인")
    print("4. 시간 범위가 적절히 설정되어 있는지 확인")

if __name__ == "__main__":
    main()