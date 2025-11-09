// src/components/voice/VoiceAssistantInterface.kt
package com.glec.dtg.dashboard.components.voice

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.*
import androidx.compose.ui.draw.*
import androidx.compose.ui.geometry.*
import androidx.compose.ui.graphics.*
import androidx.compose.ui.graphics.drawscope.*
import androidx.compose.ui.text.*
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.*
import kotlin.math.*

/**
 * Tesla + BYD 스타일 음성 AI 어시스턴트 인터페이스
 * 화물차 운전자를 위한 음성 명령 시스템
 */
@Composable
fun VoiceAssistantInterface(
    voiceState: VoiceAssistantState,
    modifier: Modifier = Modifier,
    onActivate: () -> Unit = {},
    onDeactivate: () -> Unit = {},
    onCommandExecute: (VoiceCommand) -> Unit = {},
    expandedMode: Boolean = false
) {
    val pulseAnimation = rememberInfiniteTransition(label = "voice_pulse")
    val pulseMagnitude by pulseAnimation.animateFloat(
        initialValue = 1f,
        targetValue = 1.2f,
        animationSpec = infiniteRepeatable(
            animation = tween(
                durationMillis = if (voiceState.isListening) 800 else 1500,
                easing = FastOutSlowInEasing
            ),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulse_magnitude"
    )
    
    val waveAnimation = rememberInfiniteTransition(label = "voice_wave")
    val waveProgress by waveAnimation.animateFloat(
        initialValue = 0f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(2000, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "wave_progress"
    )
    
    if (expandedMode) {
        // 전체 화면 모드
        FullScreenVoiceAssistant(
            voiceState = voiceState,
            pulseMagnitude = if (voiceState.isActive) pulseMagnitude else 1f,
            waveProgress = if (voiceState.isListening) waveProgress else 0f,
            onActivate = onActivate,
            onDeactivate = onDeactivate,
            onCommandExecute = onCommandExecute,
            modifier = modifier
        )
    } else {
        // 컴팩트 플로팅 버튼 모드
        CompactVoiceAssistant(
            voiceState = voiceState,
            pulseMagnitude = if (voiceState.isActive) pulseMagnitude else 1f,
            onActivate = onActivate,
            onDeactivate = onDeactivate,
            modifier = modifier
        )
    }
}

/**
 * 전체 화면 음성 어시스턴트
 */
@Composable
private fun FullScreenVoiceAssistant(
    voiceState: VoiceAssistantState,
    pulseMagnitude: Float,
    waveProgress: Float,
    onActivate: () -> Unit,
    onDeactivate: () -> Unit,
    onCommandExecute: (VoiceCommand) -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier
            .width(400.dp)
            .background(
                brush = Brush.verticalGradient(
                    colors = listOf(
                        Color(0xFF1A237E).copy(alpha = 0.95f),
                        Color(0xFF0D47A1).copy(alpha = 0.9f)
                    )
                ),
                shape = RoundedCornerShape(28.dp)
            )
            .border(
                width = 2.dp,
                brush = Brush.verticalGradient(
                    colors = listOf(
                        Color(0xFF2196F3),
                        Color(0xFF1976D2).copy(alpha = 0.5f)
                    )
                ),
                shape = RoundedCornerShape(28.dp)
            )
            .padding(28.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(24.dp)
    ) {
        // 헤더
        VoiceAssistantHeader(
            isActive = voiceState.isActive,
            isListening = voiceState.isListening
        )
        
        // 메인 음성 시각화
        VoiceVisualization(
            isActive = voiceState.isActive,
            isListening = voiceState.isListening,
            voiceLevel = voiceState.voiceLevel,
            pulseMagnitude = pulseMagnitude,
            waveProgress = waveProgress,
            onActivate = onActivate,
            onDeactivate = onDeactivate
        )
        
        // 현재 인식 텍스트
        if (voiceState.currentTranscript.isNotEmpty()) {
            TranscriptDisplay(
                transcript = voiceState.currentTranscript,
                confidence = voiceState.confidence
            )
        }
        
        // AI 응답
        voiceState.lastResponse?.let { response ->
            AIResponseDisplay(response = response)
        }
        
        // 명령 추천
        if (!voiceState.isListening && voiceState.suggestedCommands.isNotEmpty()) {
            SuggestedCommands(
                commands = voiceState.suggestedCommands,
                onCommandSelect = onCommandExecute
            )
        }
        
        // 상태 인디케이터
        VoiceStatusIndicator(voiceState = voiceState)
    }
}

/**
 * 컴팩트 음성 어시스턴트 (플로팅 버튼)
 */
@Composable
private fun CompactVoiceAssistant(
    voiceState: VoiceAssistantState,
    pulseMagnitude: Float,
    onActivate: () -> Unit,
    onDeactivate: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .size(80.dp)
            .scale(pulseMagnitude)
            .background(
                brush = Brush.radialGradient(
                    colors = when {
                        voiceState.isListening -> listOf(
                            Color(0xFFFF6B35),
                            Color(0xFFFF6B35).copy(alpha = 0.3f)
                        )
                        voiceState.isActive -> listOf(
                            Color(0xFF4CAF50),
                            Color(0xFF4CAF50).copy(alpha = 0.3f)
                        )
                        else -> listOf(
                            Color(0xFF2196F3),
                            Color(0xFF2196F3).copy(alpha = 0.3f)
                        )
                    }
                ),
                shape = CircleShape
            )
            .border(
                width = 3.dp,
                color = when {
                    voiceState.isListening -> Color(0xFFFF6B35)
                    voiceState.isActive -> Color(0xFF4CAF50)
                    else -> Color(0xFF2196F3)
                },
                shape = CircleShape
            )
            .clickable {
                if (voiceState.isActive) onDeactivate() else onActivate()
            },
        contentAlignment = Alignment.Center
    ) {
        // 마이크 아이콘
        Text(
            text = when {
                voiceState.isListening -> "🎤"
                voiceState.isActive -> "🗣️"
                else -> "🎙️"
            },
            style = TextStyle(fontSize = 32.sp)
        )
        
        // 음성 레벨 링
        if (voiceState.isListening) {
            Canvas(
                modifier = Modifier
                    .fillMaxSize()
                    .alpha(0.6f)
            ) {
                drawVoiceLevelRing(voiceState.voiceLevel)
            }
        }
    }
}

/**
 * 음성 어시스턴트 헤더
 */
@Composable
private fun VoiceAssistantHeader(
    isActive: Boolean,
    isListening: Boolean
) {
    Row(
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = "🤖",
            style = TextStyle(fontSize = 28.sp)
        )
        
        Column {
            Text(
                text = "GLEC AI 어시스턴트",
                style = TextStyle(
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
            )
            
            Text(
                text = when {
                    isListening -> "듣고 있습니다..."
                    isActive -> "준비됨"
                    else -> "대기 중"
                },
                style = TextStyle(
                    fontSize = 12.sp,
                    color = when {
                        isListening -> Color(0xFFFF6B35)
                        isActive -> Color(0xFF4CAF50)
                        else -> Color.Gray
                    }
                )
            )
        }
    }
}

/**
 * 음성 시각화
 */
@Composable
private fun VoiceVisualization(
    isActive: Boolean,
    isListening: Boolean,
    voiceLevel: Float,
    pulseMagnitude: Float,
    waveProgress: Float,
    onActivate: () -> Unit,
    onDeactivate: () -> Unit
) {
    Box(
        modifier = Modifier
            .size(180.dp)
            .clickable {
                if (isActive) onDeactivate() else onActivate()
            },
        contentAlignment = Alignment.Center
    ) {
        // 배경 원
        Canvas(modifier = Modifier.fillMaxSize()) {
            drawVoiceVisualizationBackground(
                isActive = isActive,
                isListening = isListening,
                pulseMagnitude = pulseMagnitude
            )
        }
        
        // 음성 웨이브폼
        if (isListening) {
            Canvas(
                modifier = Modifier
                    .fillMaxSize()
                    .alpha(0.8f)
            ) {
                drawVoiceWaveform(voiceLevel, waveProgress)
            }
        }
        
        // 중앙 마이크 버튼
        Box(
            modifier = Modifier
                .size(80.dp)
                .background(
                    color = when {
                        isListening -> Color(0xFFFF6B35)
                        isActive -> Color(0xFF4CAF50)
                        else -> Color(0xFF2196F3)
                    },
                    shape = CircleShape
                ),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = when {
                    isListening -> "🎤"
                    isActive -> "🗣️"
                    else -> "🎙️"
                },
                style = TextStyle(fontSize = 36.sp)
            )
        }
    }
}

/**
 * 음성 시각화 배경 그리기
 */
private fun DrawScope.drawVoiceVisualizationBackground(
    isActive: Boolean,
    isListening: Boolean,
    pulseMagnitude: Float
) {
    val center = Offset(size.width / 2, size.height / 2)
    val baseRadius = size.minDimension / 2
    
    // 펄스 링들
    repeat(3) { ring ->
        val radius = baseRadius * (0.5f + ring * 0.2f) * pulseMagnitude
        val alpha = 0.3f - ring * 0.1f
        
        drawCircle(
            color = when {
                isListening -> Color(0xFFFF6B35)
                isActive -> Color(0xFF4CAF50)
                else -> Color(0xFF2196F3)
            },
            radius = radius,
            center = center,
            style = Stroke(width = 2.dp.toPx()),
            alpha = alpha
        )
    }
}

/**
 * 음성 웨이브폼 그리기
 */
private fun DrawScope.drawVoiceWaveform(voiceLevel: Float, progress: Float) {
    val center = Offset(size.width / 2, size.height / 2)
    val maxRadius = size.minDimension / 2 * 0.8f
    
    val segments = 36
    val angleStep = 360f / segments
    
    for (i in 0 until segments) {
        val angle = angleStep * i
        val angleRad = Math.toRadians(angle.toDouble())
        
        // 웨이브 변형
        val waveOffset = sin((angle / 60f + progress * PI * 2).toFloat()) * voiceLevel * 20f
        val radius = maxRadius * 0.6f + waveOffset
        
        val startX = center.x + cos(angleRad).toFloat() * (radius - 10)
        val startY = center.y + sin(angleRad).toFloat() * (radius - 10)
        val endX = center.x + cos(angleRad).toFloat() * radius
        val endY = center.y + sin(angleRad).toFloat() * radius
        
        drawLine(
            color = Color(0xFFFF6B35),
            start = Offset(startX, startY),
            end = Offset(endX, endY),
            strokeWidth = 3.dp.toPx(),
            cap = StrokeCap.Round,
            alpha = 0.7f + voiceLevel * 0.3f
        )
    }
}

/**
 * 음성 레벨 링 그리기
 */
private fun DrawScope.drawVoiceLevelRing(voiceLevel: Float) {
    val center = Offset(size.width / 2, size.height / 2)
    val radius = size.minDimension / 2 * (0.8f + voiceLevel * 0.2f)
    
    drawCircle(
        color = Color(0xFFFF6B35),
        radius = radius,
        center = center,
        style = Stroke(width = (2 + voiceLevel * 3).dp.toPx()),
        alpha = 0.5f + voiceLevel * 0.5f
    )
}

/**
 * 인식 텍스트 디스플레이
 */
@Composable
private fun TranscriptDisplay(
    transcript: String,
    confidence: Float
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(
                color = Color.Black.copy(alpha = 0.4f),
                shape = RoundedCornerShape(12.dp)
            )
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Text(
            text = transcript,
            style = TextStyle(
                fontSize = 16.sp,
                color = Color.White,
                textAlign = TextAlign.Center
            )
        )
        
        // 신뢰도 표시
        Row(
            horizontalArrangement = Arrangement.spacedBy(4.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            LinearProgressIndicator(
                progress = confidence,
                modifier = Modifier
                    .width(100.dp)
                    .height(4.dp),
                color = when {
                    confidence > 0.8f -> Color(0xFF4CAF50)
                    confidence > 0.6f -> Color(0xFFFFAB00)
                    else -> Color(0xFFFF6B35)
                },
                trackColor = Color.Gray.copy(alpha = 0.3f)
            )
            
            Text(
                text = "${(confidence * 100).toInt()}%",
                style = TextStyle(
                    fontSize = 11.sp,
                    color = Color.Gray
                )
            )
        }
    }
}

/**
 * AI 응답 디스플레이
 */
@Composable
private fun AIResponseDisplay(response: String) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = Color(0xFF2196F3).copy(alpha = 0.2f)
        ),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Text(
                text = "💬",
                style = TextStyle(fontSize = 20.sp)
            )
            
            Text(
                text = response,
                style = TextStyle(
                    fontSize = 14.sp,
                    color = Color.White,
                    lineHeight = 20.sp
                ),
                modifier = Modifier.weight(1f)
            )
        }
    }
}

/**
 * 추천 명령어
 */
@Composable
private fun SuggestedCommands(
    commands: List<VoiceCommand>,
    onCommandSelect: (VoiceCommand) -> Unit
) {
    Column(
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        Text(
            text = "추천 명령어",
            style = TextStyle(
                fontSize = 12.sp,
                color = Color.Gray
            )
        )
        
        LazyRow(
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(commands) { command ->
                CommandChip(
                    command = command,
                    onClick = { onCommandSelect(command) }
                )
            }
        }
    }
}

/**
 * 명령어 칩
 */
@Composable
private fun CommandChip(
    command: VoiceCommand,
    onClick: () -> Unit
) {
    Chip(
        onClick = onClick,
        colors = ChipDefaults.chipColors(
            containerColor = Color(0xFF2196F3).copy(alpha = 0.3f)
        ),
        border = BorderStroke(
            width = 1.dp,
            color = Color(0xFF2196F3).copy(alpha = 0.5f)
        )
    ) {
        Row(
            horizontalArrangement = Arrangement.spacedBy(4.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = command.icon,
                style = TextStyle(fontSize = 12.sp)
            )
            
            Text(
                text = command.phrase,
                style = TextStyle(
                    fontSize = 11.sp,
                    color = Color.White
                )
            )
        }
    }
}

/**
 * 음성 상태 인디케이터
 */
@Composable
private fun VoiceStatusIndicator(voiceState: VoiceAssistantState) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(
                color = Color.Black.copy(alpha = 0.3f),
                shape = RoundedCornerShape(8.dp)
            )
            .padding(12.dp),
        horizontalArrangement = Arrangement.SpaceEvenly
    ) {
        StatusItem(
            label = "마이크",
            value = if (voiceState.isMicrophoneEnabled) "활성" else "비활성",
            isActive = voiceState.isMicrophoneEnabled
        )
        
        StatusItem(
            label = "노이즈 제거",
            value = "${(voiceState.noiseSuppressionLevel * 100).toInt()}%",
            isActive = voiceState.noiseSuppressionLevel > 0.5f
        )
        
        StatusItem(
            label = "네트워크",
            value = if (voiceState.isOnline) "온라인" else "오프라인",
            isActive = voiceState.isOnline
        )
    }
}

/**
 * 상태 아이템
 */
@Composable
private fun StatusItem(
    label: String,
    value: String,
    isActive: Boolean
) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        Text(
            text = label,
            style = TextStyle(
                fontSize = 10.sp,
                color = Color.Gray
            )
        )
        
        Text(
            text = value,
            style = TextStyle(
                fontSize = 11.sp,
                fontWeight = FontWeight.Medium,
                color = if (isActive) Color(0xFF4CAF50) else Color(0xFFFF6B35)
            )
        )
    }
}

// 데이터 클래스
data class VoiceAssistantState(
    val isActive: Boolean = false,
    val isListening: Boolean = false,
    val voiceLevel: Float = 0f,
    val currentTranscript: String = "",
    val confidence: Float = 0f,
    val lastResponse: String? = null,
    val suggestedCommands: List<VoiceCommand> = emptyList(),
    val isMicrophoneEnabled: Boolean = true,
    val noiseSuppressionLevel: Float = 0.7f,
    val isOnline: Boolean = true
)

data class VoiceCommand(
    val id: String,
    val phrase: String,
    val category: CommandCategory,
    val icon: String = "🎯"
)

enum class CommandCategory {
    NAVIGATION, MEDIA, VEHICLE, COMMUNICATION, EMERGENCY
}