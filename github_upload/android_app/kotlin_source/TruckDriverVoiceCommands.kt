// src/components/voice/TruckDriverVoiceCommands.kt
package com.glec.dtg.dashboard.components.voice

/**
 * 화물차 운전자 전용 음성 명령 정의
 * 한국 화물차 운전 환경에 최적화된 명령어 세트
 */
object TruckDriverVoiceCommands {
    
    /**
     * 내비게이션 관련 명령어
     */
    val navigationCommands = listOf(
        VoiceCommand("nav_rest_area", "가장 가까운 휴게소", CommandCategory.NAVIGATION, "⛽"),
        VoiceCommand("nav_truck_parking", "화물차 주차 가능한 곳", CommandCategory.NAVIGATION, "🅿️"),
        VoiceCommand("nav_loading_dock", "물류센터 안내", CommandCategory.NAVIGATION, "📦"),
        VoiceCommand("nav_weight_station", "계근대 위치", CommandCategory.NAVIGATION, "⚖️"),
        VoiceCommand("nav_repair_shop", "정비소 찾기", CommandCategory.NAVIGATION, "🔧"),
        VoiceCommand("nav_gas_station", "주유소 안내", CommandCategory.NAVIGATION, "⛽"),
        VoiceCommand("nav_avoid_traffic", "정체 구간 우회", CommandCategory.NAVIGATION, "🚦"),
        VoiceCommand("nav_highway_info", "고속도로 정보", CommandCategory.NAVIGATION, "🛣️"),
        VoiceCommand("nav_tunnel_height", "터널 높이 확인", CommandCategory.NAVIGATION, "🚇"),
        VoiceCommand("nav_bridge_weight", "교량 하중 제한", CommandCategory.NAVIGATION, "🌉"),
        VoiceCommand("nav_restricted_area", "화물차 통행 제한 구역", CommandCategory.NAVIGATION, "⛔"),
        VoiceCommand("nav_delivery_address", "배송지 주소 안내", CommandCategory.NAVIGATION, "📍"),
        VoiceCommand("nav_return_route", "회차 경로 안내", CommandCategory.NAVIGATION, "↩️"),
        VoiceCommand("nav_rest_mandatory", "의무 휴식 시간 알림", CommandCategory.NAVIGATION, "⏰"),
        VoiceCommand("nav_weather_route", "날씨 고려 경로", CommandCategory.NAVIGATION, "🌦️")
    )
    
    /**
     * 미디어/통신 관련 명령어
     */
    val mediaCommands = listOf(
        VoiceCommand("media_radio_traffic", "교통방송 켜기", CommandCategory.MEDIA, "📻"),
        VoiceCommand("media_bluetooth_connect", "블루투스 연결", CommandCategory.MEDIA, "🔵"),
        VoiceCommand("media_volume_up", "볼륨 올려", CommandCategory.MEDIA, "🔊"),
        VoiceCommand("media_volume_down", "볼륨 내려", CommandCategory.MEDIA, "🔉"),
        VoiceCommand("media_mute", "음소거", CommandCategory.MEDIA, "🔇"),
        VoiceCommand("media_next_track", "다음 곡", CommandCategory.MEDIA, "⏭️"),
        VoiceCommand("media_previous_track", "이전 곡", CommandCategory.MEDIA, "⏮️"),
        VoiceCommand("media_pause", "일시 정지", CommandCategory.MEDIA, "⏸️"),
        VoiceCommand("media_play", "재생", CommandCategory.MEDIA, "▶️"),
        VoiceCommand("media_podcast", "팟캐스트 재생", CommandCategory.MEDIA, "🎙️")
    )
    
    /**
     * 차량 제어 관련 명령어
     */
    val vehicleCommands = listOf(
        VoiceCommand("vehicle_cruise_on", "크루즈 켜기", CommandCategory.VEHICLE, "🚗"),
        VoiceCommand("vehicle_cruise_speed", "크루즈 속도 설정", CommandCategory.VEHICLE, "⏱️"),
        VoiceCommand("vehicle_exhaust_brake", "배기 브레이크", CommandCategory.VEHICLE, "💨"),
        VoiceCommand("vehicle_retarder", "리타더 작동", CommandCategory.VEHICLE, "🔄"),
        VoiceCommand("vehicle_tire_pressure", "타이어 공기압 확인", CommandCategory.VEHICLE, "🛞"),
        VoiceCommand("vehicle_fuel_status", "연료 상태", CommandCategory.VEHICLE, "⛽"),
        VoiceCommand("vehicle_engine_temp", "엔진 온도 확인", CommandCategory.VEHICLE, "🌡️"),
        VoiceCommand("vehicle_brake_temp", "브레이크 온도", CommandCategory.VEHICLE, "🔥"),
        VoiceCommand("vehicle_load_weight", "적재 중량 확인", CommandCategory.VEHICLE, "📊"),
        VoiceCommand("vehicle_maintenance", "정비 일정 확인", CommandCategory.VEHICLE, "🔧"),
        VoiceCommand("vehicle_dtg_save", "DTG 데이터 저장", CommandCategory.VEHICLE, "💾"),
        VoiceCommand("vehicle_camera_rear", "후방 카메라", CommandCategory.VEHICLE, "📷"),
        VoiceCommand("vehicle_camera_blind", "사각지대 카메라", CommandCategory.VEHICLE, "👁️"),
        VoiceCommand("vehicle_lights_check", "전조등 점검", CommandCategory.VEHICLE, "💡"),
        VoiceCommand("vehicle_warning_lights", "경고등 확인", CommandCategory.VEHICLE, "⚠️")
    )
    
    /**
     * 통신/연락 관련 명령어
     */
    val communicationCommands = listOf(
        VoiceCommand("comm_call_dispatch", "배차실 전화", CommandCategory.COMMUNICATION, "📞"),
        VoiceCommand("comm_call_customer", "화주 연락", CommandCategory.COMMUNICATION, "👤"),
        VoiceCommand("comm_call_home", "집에 전화", CommandCategory.COMMUNICATION, "🏠"),
        VoiceCommand("comm_send_location", "현재 위치 전송", CommandCategory.COMMUNICATION, "📍"),
        VoiceCommand("comm_arrival_notice", "도착 예정 알림", CommandCategory.COMMUNICATION, "📢"),
        VoiceCommand("comm_delay_report", "지연 보고", CommandCategory.COMMUNICATION, "⏰"),
        VoiceCommand("comm_loading_complete", "상차 완료 보고", CommandCategory.COMMUNICATION, "✅"),
        VoiceCommand("comm_unloading_complete", "하차 완료 보고", CommandCategory.COMMUNICATION, "✅"),
        VoiceCommand("comm_break_report", "휴식 시작 알림", CommandCategory.COMMUNICATION, "☕"),
        VoiceCommand("comm_walkie_talkie", "무전기 연결", CommandCategory.COMMUNICATION, "📡")
    )
    
    /**
     * 긴급/안전 관련 명령어
     */
    val emergencyCommands = listOf(
        VoiceCommand("emergency_112", "긴급 신고 112", CommandCategory.EMERGENCY, "🚨"),
        VoiceCommand("emergency_insurance", "보험사 연결", CommandCategory.EMERGENCY, "🏥"),
        VoiceCommand("emergency_breakdown", "긴급 출동 서비스", CommandCategory.EMERGENCY, "🚑"),
        VoiceCommand("emergency_accident_report", "사고 신고", CommandCategory.EMERGENCY, "⚠️"),
        VoiceCommand("emergency_fire_report", "화재 신고", CommandCategory.EMERGENCY, "🔥"),
        VoiceCommand("emergency_medical", "의료 긴급 상황", CommandCategory.EMERGENCY, "🏥"),
        VoiceCommand("emergency_road_hazard", "도로 위험 신고", CommandCategory.EMERGENCY, "⚠️"),
        VoiceCommand("emergency_weather_alert", "기상 특보 확인", CommandCategory.EMERGENCY, "🌪️"),
        VoiceCommand("emergency_drowsy_alert", "졸음 운전 경고", CommandCategory.EMERGENCY, "😴"),
        VoiceCommand("emergency_sos_location", "SOS 위치 발송", CommandCategory.EMERGENCY, "🆘")
    )
    
    /**
     * 모든 명령어 맵
     */
    val allCommands: Map<CommandCategory, List<VoiceCommand>> = mapOf(
        CommandCategory.NAVIGATION to navigationCommands,
        CommandCategory.MEDIA to mediaCommands,
        CommandCategory.VEHICLE to vehicleCommands,
        CommandCategory.COMMUNICATION to communicationCommands,
        CommandCategory.EMERGENCY to emergencyCommands
    )
    
    /**
     * 자주 사용하는 명령어 (상위 10개)
     */
    val frequentCommands = listOf(
        navigationCommands[0],  // 가장 가까운 휴게소
        navigationCommands[1],  // 화물차 주차 가능한 곳
        vehicleCommands[0],     // 크루즈 켜기
        mediaCommands[0],       // 교통방송 켜기
        communicationCommands[0], // 배차실 전화
        navigationCommands[13], // 의무 휴식 시간 알림
        vehicleCommands[5],     // 연료 상태
        emergencyCommands[8],   // 졸음 운전 경고
        navigationCommands[6],  // 정체 구간 우회
        vehicleCommands[4]      // 타이어 공기압 확인
    )
    
    /**
     * 음성 명령어 검색
     */
    fun searchCommands(query: String): List<VoiceCommand> {
        val lowerQuery = query.lowercase()
        return allCommands.values.flatten().filter { command ->
            command.phrase.lowercase().contains(lowerQuery) ||
            command.id.lowercase().contains(lowerQuery)
        }
    }
    
    /**
     * 카테고리별 명령어 가져오기
     */
    fun getCommandsByCategory(category: CommandCategory): List<VoiceCommand> {
        return allCommands[category] ?: emptyList()
    }
    
    /**
     * 명령어 ID로 찾기
     */
    fun findCommandById(id: String): VoiceCommand? {
        return allCommands.values.flatten().find { it.id == id }
    }
    
    /**
     * 유사 명령어 추천
     */
    fun getSimilarCommands(command: VoiceCommand, limit: Int = 3): List<VoiceCommand> {
        return allCommands[command.category]
            ?.filter { it.id != command.id }
            ?.take(limit)
            ?: emptyList()
    }
    
    /**
     * 컨텍스트 기반 명령어 추천
     */
    fun getContextualCommands(
        isDriving: Boolean,
        isHighway: Boolean,
        timeOfDay: TimeOfDay,
        weatherCondition: WeatherCondition
    ): List<VoiceCommand> {
        val recommendations = mutableListOf<VoiceCommand>()
        
        // 운전 중 추천
        if (isDriving) {
            if (isHighway) {
                recommendations.add(navigationCommands[0]) // 휴게소
                recommendations.add(navigationCommands[13]) // 의무 휴식
            }
            recommendations.add(vehicleCommands[0]) // 크루즈
            recommendations.add(mediaCommands[0]) // 교통방송
        }
        
        // 시간대별 추천
        when (timeOfDay) {
            TimeOfDay.NIGHT, TimeOfDay.DAWN -> {
                recommendations.add(emergencyCommands[8]) // 졸음 경고
                recommendations.add(vehicleCommands[13]) // 전조등 점검
            }
            TimeOfDay.MORNING, TimeOfDay.EVENING -> {
                recommendations.add(navigationCommands[6]) // 정체 우회
            }
            else -> {}
        }
        
        // 날씨별 추천
        when (weatherCondition) {
            WeatherCondition.RAIN, WeatherCondition.SNOW -> {
                recommendations.add(navigationCommands[14]) // 날씨 경로
                recommendations.add(emergencyCommands[7]) // 기상 특보
            }
            WeatherCondition.FOG -> {
                recommendations.add(vehicleCommands[13]) // 전조등
                recommendations.add(emergencyCommands[6]) // 도로 위험
            }
            else -> {}
        }
        
        return recommendations.distinct().take(5)
    }
}

// 보조 열거형
enum class TimeOfDay {
    DAWN, MORNING, AFTERNOON, EVENING, NIGHT
}

enum class WeatherCondition {
    CLEAR, CLOUDY, RAIN, SNOW, FOG, STORM
}