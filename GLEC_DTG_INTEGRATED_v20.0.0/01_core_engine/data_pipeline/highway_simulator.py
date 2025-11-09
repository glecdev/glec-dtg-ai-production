#!/usr/bin/env python3
"""
고속도로별 시뮬레이터 - 한국 주요 5개 고속도로 데이터 생성
- 경부고속도로, 서해안고속도로, 호남고속도로, 영동고속도로, 중부고속도로
"""

import time
import random
import math
import numpy as np
from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# InfluxDB 설정
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "glec-admin-token-123456789"
INFLUXDB_ORG = "glec"
INFLUXDB_BUCKET = "dtg_metrics"

# 고속도로별 구간 데이터
HIGHWAYS = {
    "경부고속도로": {
        "id": "gyeongbu",
        "total_distance": 428.8,
        "sections": [
            {"name": "서울-수원", "start_km": 0, "end_km": 40, "speed_limit": 100},
            {"name": "수원-천안", "start_km": 40, "end_km": 84, "speed_limit": 110},
            {"name": "천안-대전", "start_km": 84, "end_km": 167, "speed_limit": 110},
            {"name": "대전-구미", "start_km": 167, "end_km": 273, "speed_limit": 110},
            {"name": "구미-대구", "start_km": 273, "end_km": 323, "speed_limit": 100},
            {"name": "대구-부산", "start_km": 323, "end_km": 428.8, "speed_limit": 100}
        ],
        "traffic_patterns": {
            "morning_rush": {"06:00-09:00": 0.7},
            "evening_rush": {"17:00-20:00": 0.6},
            "normal": {"default": 0.9}
        },
        "accident_zones": [(145, 150), (280, 285), (380, 385)]
    },
    "서해안고속도로": {
        "id": "west_coast",
        "total_distance": 336.3,
        "sections": [
            {"name": "서울-안산", "start_km": 0, "end_km": 35, "speed_limit": 100},
            {"name": "안산-평택", "start_km": 35, "end_km": 90, "speed_limit": 110},
            {"name": "평택-서천", "start_km": 90, "end_km": 180, "speed_limit": 110},
            {"name": "서천-군산", "start_km": 180, "end_km": 250, "speed_limit": 110},
            {"name": "군산-목포", "start_km": 250, "end_km": 336.3, "speed_limit": 100}
        ],
        "traffic_patterns": {
            "weekend": {"Sat,Sun": 0.5},
            "weekday": {"Mon-Fri": 0.8}
        },
        "accident_zones": [(45, 50), (200, 205)]
    },
    "호남고속도로": {
        "id": "honam",
        "total_distance": 251.4,
        "sections": [
            {"name": "논산-익산", "start_km": 0, "end_km": 55, "speed_limit": 110},
            {"name": "익산-정읍", "start_km": 55, "end_km": 100, "speed_limit": 110},
            {"name": "정읍-광주", "start_km": 100, "end_km": 180, "speed_limit": 110},
            {"name": "광주-순천", "start_km": 180, "end_km": 251.4, "speed_limit": 100}
        ],
        "traffic_patterns": {
            "harvest_season": {"Sep-Oct": 0.6},
            "normal": {"default": 0.85}
        },
        "accident_zones": [(75, 80), (150, 155)]
    },
    "영동고속도로": {
        "id": "yeongdong",
        "total_distance": 234.4,
        "sections": [
            {"name": "인천-용인", "start_km": 0, "end_km": 50, "speed_limit": 100},
            {"name": "용인-여주", "start_km": 50, "end_km": 100, "speed_limit": 110},
            {"name": "여주-원주", "start_km": 100, "end_km": 150, "speed_limit": 100},
            {"name": "원주-강릉", "start_km": 150, "end_km": 234.4, "speed_limit": 90}
        ],
        "traffic_patterns": {
            "winter_sports": {"Dec-Feb": 0.5},
            "summer_vacation": {"Jul-Aug": 0.6},
            "normal": {"default": 0.8}
        },
        "accident_zones": [(120, 125), (180, 190)]  # 산악지역
    },
    "중부고속도로": {
        "id": "jungbu",
        "total_distance": 148.9,
        "sections": [
            {"name": "하남-이천", "start_km": 0, "end_km": 45, "speed_limit": 110},
            {"name": "이천-음성", "start_km": 45, "end_km": 90, "speed_limit": 110},
            {"name": "음성-통영", "start_km": 90, "end_km": 148.9, "speed_limit": 100}
        ],
        "traffic_patterns": {
            "normal": {"default": 0.9}
        },
        "accident_zones": [(60, 65)]
    }
}

# 차량 유형
VEHICLE_TYPES = {
    "대형트럭": {
        "tonnage": 25,
        "max_speed": 90,
        "fuel_efficiency": 3.0,
        "empty_weight": 12000,
        "co2_factor": 3.2
    },
    "중형트럭": {
        "tonnage": 11,
        "max_speed": 100,
        "fuel_efficiency": 4.0,
        "empty_weight": 8000,
        "co2_factor": 3.0
    },
    "소형트럭": {
        "tonnage": 5,
        "max_speed": 110,
        "fuel_efficiency": 5.5,
        "empty_weight": 4000,
        "co2_factor": 2.8
    },
    "버스": {
        "tonnage": 15,
        "max_speed": 100,
        "fuel_efficiency": 3.5,
        "empty_weight": 10000,
        "co2_factor": 3.1
    }
}

# 날씨 조건
WEATHER_CONDITIONS = {
    "맑음": {"speed_factor": 1.0, "safety_penalty": 0},
    "비": {"speed_factor": 0.8, "safety_penalty": 15},
    "눈": {"speed_factor": 0.6, "safety_penalty": 25},
    "안개": {"speed_factor": 0.7, "safety_penalty": 20},
    "강풍": {"speed_factor": 0.85, "safety_penalty": 10}
}

class HighwaySimulator:
    def __init__(self):
        print("🚛 고속도로별 시뮬레이터 초기화...")
        
        # InfluxDB 클라이언트
        self.influx_client = InfluxDBClient(
            url=INFLUXDB_URL,
            token=INFLUXDB_TOKEN,
            org=INFLUXDB_ORG
        )
        self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
        
        self.is_running = False
        self.simulation_vehicles = []
        
        print("✅ 초기화 완료")
    
    def initialize_vehicles(self):
        """각 고속도로에 차량 배치"""
        self.simulation_vehicles = []
        
        for highway_name, highway_data in HIGHWAYS.items():
            # 고속도로당 10-20대 차량 생성
            num_vehicles = random.randint(10, 20)
            
            for i in range(num_vehicles):
                vehicle_type = random.choice(list(VEHICLE_TYPES.keys()))
                vehicle_spec = VEHICLE_TYPES[vehicle_type]
                
                # 차량 초기 위치 랜덤 설정
                initial_position = random.uniform(0, highway_data["total_distance"])
                
                vehicle = {
                    "id": f"{highway_data['id']}_vehicle_{i+1}",
                    "highway": highway_name,
                    "highway_id": highway_data["id"],
                    "type": vehicle_type,
                    "spec": vehicle_spec,
                    "position_km": initial_position,
                    "speed": random.uniform(70, 90),
                    "cargo_weight": vehicle_spec["tonnage"] * random.uniform(0.3, 0.9) * 1000,
                    "fuel_consumed": 0,
                    "total_distance": 0,
                    "start_time": time.time(),
                    "direction": random.choice([1, -1])  # 1: 정방향, -1: 역방향
                }
                
                self.simulation_vehicles.append(vehicle)
        
        print(f"✅ {len(self.simulation_vehicles)}대 차량 생성 완료")
    
    def get_current_section(self, highway_name, position_km):
        """현재 위치의 구간 정보 반환"""
        highway = HIGHWAYS[highway_name]
        
        for section in highway["sections"]:
            if section["start_km"] <= position_km <= section["end_km"]:
                return section
        
        # 범위 벗어난 경우 첫/마지막 구간 반환
        if position_km < 0:
            return highway["sections"][0]
        else:
            return highway["sections"][-1]
    
    def is_in_accident_zone(self, highway_name, position_km):
        """사고 다발 지역 여부 확인"""
        highway = HIGHWAYS[highway_name]
        
        for zone_start, zone_end in highway.get("accident_zones", []):
            if zone_start <= position_km <= zone_end:
                return True
        return False
    
    def get_traffic_factor(self, highway_name):
        """현재 시간대의 교통량 계수"""
        highway = HIGHWAYS[highway_name]
        patterns = highway.get("traffic_patterns", {})
        
        current_hour = datetime.now().hour
        current_time = f"{current_hour:02d}:00"
        
        # 시간대별 패턴 확인
        for pattern_name, times in patterns.items():
            if pattern_name in ["morning_rush", "evening_rush"]:
                for time_range, factor in times.items():
                    start, end = time_range.split("-")
                    start_hour = int(start.split(":")[0])
                    end_hour = int(end.split(":")[0])
                    
                    if start_hour <= current_hour < end_hour:
                        return factor
        
        return patterns.get("normal", {}).get("default", 0.9)
    
    def calculate_vehicle_physics(self, vehicle, dt=1.0):
        """차량 물리 계산"""
        current_section = self.get_current_section(vehicle["highway"], vehicle["position_km"])
        weather = random.choice(list(WEATHER_CONDITIONS.keys()))
        weather_data = WEATHER_CONDITIONS[weather]
        
        # 제한속도와 교통량 고려
        traffic_factor = self.get_traffic_factor(vehicle["highway"])
        base_speed_limit = current_section["speed_limit"]
        effective_speed_limit = base_speed_limit * traffic_factor * weather_data["speed_factor"]
        
        # 목표 속도 설정
        target_speed = min(
            effective_speed_limit,
            vehicle["spec"]["max_speed"]
        )
        
        # 사고 다발 지역에서는 속도 감소
        if self.is_in_accident_zone(vehicle["highway"], vehicle["position_km"]):
            target_speed *= 0.8
        
        # 속도 조정
        speed_diff = target_speed - vehicle["speed"]
        acceleration = np.clip(speed_diff * 0.3, -3.0, 2.0)
        vehicle["speed"] = max(0, vehicle["speed"] + acceleration * dt)
        
        # 위치 업데이트
        distance_delta = (vehicle["speed"] / 3600) * dt * vehicle["direction"]
        vehicle["position_km"] += distance_delta
        
        # 경계 처리
        highway = HIGHWAYS[vehicle["highway"]]
        if vehicle["position_km"] >= highway["total_distance"]:
            vehicle["position_km"] = highway["total_distance"] - 1
            vehicle["direction"] = -1
        elif vehicle["position_km"] <= 0:
            vehicle["position_km"] = 1
            vehicle["direction"] = 1
        
        # 연료 소비 계산
        load_factor = vehicle["cargo_weight"] / (vehicle["spec"]["tonnage"] * 1000)
        fuel_efficiency = vehicle["spec"]["fuel_efficiency"] * (1 - load_factor * 0.2)
        fuel_rate = vehicle["speed"] / fuel_efficiency if fuel_efficiency > 0 else 0
        vehicle["fuel_consumed"] += (fuel_rate / 3600) * dt
        
        # CO2 배출량
        co2_emission = (fuel_rate / 3600) * vehicle["spec"]["co2_factor"] * 60
        
        # 안전 점수 계산
        safety_score = 100
        if vehicle["speed"] > base_speed_limit:
            safety_score -= 20
        if abs(acceleration) > 2.5:
            safety_score -= 10
        safety_score -= weather_data["safety_penalty"]
        safety_score = max(0, safety_score)
        
        return {
            "acceleration": acceleration,
            "fuel_rate": fuel_rate,
            "fuel_efficiency": fuel_efficiency,
            "co2_emission": co2_emission,
            "safety_score": safety_score,
            "weather": weather,
            "section_name": current_section["name"],
            "traffic_factor": traffic_factor
        }
    
    def run_simulation(self):
        """시뮬레이션 실행"""
        print("\n🚀 고속도로별 시뮬레이션 시작...")
        
        # 차량 초기화
        self.initialize_vehicles()
        
        self.is_running = True
        iteration = 0
        
        while self.is_running:
            try:
                current_time = datetime.now(timezone.utc)
                
                # 모든 차량 업데이트
                for vehicle in self.simulation_vehicles:
                    # 물리 계산
                    physics = self.calculate_vehicle_physics(vehicle)
                    
                    # 긴급도 수준 계산
                    if physics["safety_score"] < 60:
                        urgency = "CRITICAL"
                    elif physics["safety_score"] < 75:
                        urgency = "HIGH"
                    elif physics["safety_score"] < 85:
                        urgency = "MEDIUM"
                    else:
                        urgency = "NORMAL"
                    
                    # InfluxDB로 데이터 전송
                    point = Point("dtg_metrics") \
                        .tag("vehicle_id", vehicle["id"]) \
                        .tag("vehicle_type", vehicle["type"]) \
                        .tag("highway", vehicle["highway"]) \
                        .tag("highway_id", vehicle["highway_id"]) \
                        .tag("section", physics["section_name"]) \
                        .tag("weather", physics["weather"]) \
                        .tag("urgency_level", urgency) \
                        .field("vehicle_speed", float(vehicle["speed"])) \
                        .field("position_km", float(vehicle["position_km"])) \
                        .field("acceleration", float(physics["acceleration"])) \
                        .field("fuel_rate", float(physics["fuel_rate"])) \
                        .field("fuel_efficiency_kmpl", float(physics["fuel_efficiency"])) \
                        .field("co2_emission", float(physics["co2_emission"])) \
                        .field("safety_score", float(physics["safety_score"])) \
                        .field("cargo_weight", float(vehicle["cargo_weight"])) \
                        .field("traffic_factor", float(physics["traffic_factor"])) \
                        .field("total_weight", float(vehicle["spec"]["empty_weight"] + vehicle["cargo_weight"])) \
                        .time(current_time, WritePrecision.NS)
                    
                    self.write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, point)
                
                # 상태 출력 (10초마다)
                if iteration % 10 == 0:
                    print(f"\n📊 시뮬레이션 상태 ({datetime.now().strftime('%H:%M:%S')})")
                    
                    # 고속도로별 차량 수 집계
                    highway_counts = {}
                    for vehicle in self.simulation_vehicles:
                        highway = vehicle["highway"]
                        if highway not in highway_counts:
                            highway_counts[highway] = 0
                        highway_counts[highway] += 1
                    
                    for highway, count in highway_counts.items():
                        print(f"  {highway}: {count}대 운행 중")
                
                iteration += 1
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n\n⚠️ 사용자 중단")
                break
            except Exception as e:
                print(f"⚠️ 시뮬레이션 오류: {e}")
                continue
        
        self.stop()
    
    def stop(self):
        """시뮬레이터 정지"""
        self.is_running = False
        self.influx_client.close()
        print("🛑 시뮬레이터 정지")


def main():
    """메인 실행 함수"""
    simulator = HighwaySimulator()
    
    try:
        simulator.run_simulation()
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        simulator.stop()


if __name__ == "__main__":
    print("🚛 한국 고속도로별 DTG 시뮬레이터")
    print("=" * 50)
    print("시뮬레이션 대상:")
    for highway in HIGHWAYS.keys():
        print(f"  - {highway}")
    print("=" * 50)
    main()