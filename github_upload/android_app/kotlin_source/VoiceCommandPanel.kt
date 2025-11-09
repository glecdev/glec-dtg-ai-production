// src/components/voice/VoiceCommandPanel.kt
package com.glec.dtg.dashboard.components.voice

import androidx.compose.animation.*
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.*
import androidx.compose.ui.draw.*
import androidx.compose.ui.graphics.*
import androidx.compose.ui.text.*
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.*

/**
 * Tesla + BYD 스타일 음성 명령 패널
 * 화물차 운전자를 위한 명령어 가이드 및 히스토리
 */
@Composable
fun VoiceCommandPanel(
    commandHistory: List<VoiceCommandEntry>,
    availableCommands: Map<CommandCategory, List<VoiceCommand>>,
    modifier: Modifier = Modifier,
    onCommandSelect: (VoiceCommand) -> Unit = {},
    onClearHistory: () -> Unit = {},
    showQuickActions: Boolean = true
) {
    var selectedCategory by remember { mutableStateOf<CommandCategory?>(null) }
    
    Column(
        modifier = modifier
            .width(360.dp)
            .background(
                brush = Brush.verticalGradient(
                    colors = listOf(
                        Color(0xFF1E3A8A),
                        Color(0xFF1E293B)
                    )
                ),
                shape = RoundedCornerShape(24.dp)
            )
            .border(
                width = 1.dp,
                color = Color(0xFF3B82F6).copy(alpha = 0.5f),
                shape = RoundedCornerShape(24.dp)
            )
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // 헤더
        CommandPanelHeader(
            historyCount = commandHistory.size,
            onClearHistory = onClearHistory
        )
        
        // 빠른 실행 버튼
        if (showQuickActions) {
            QuickActionButtons(
                onCommandSelect = onCommandSelect
            )
        }
        
        // 카테고리 탭
        CategoryTabs(
            categories = availableCommands.keys.toList(),
            selectedCategory = selectedCategory,
            onCategorySelect = { selectedCategory = it }
        )
        
        // 명령어 목록 또는 히스토리
        if (selectedCategory != null) {
            CommandList(
                commands = availableCommands[selectedCategory] ?: emptyList(),
                category = selectedCategory!!,
                onCommandSelect = onCommandSelect
            )
        } else {
            CommandHistory(
                history = commandHistory.take(10)
            )
        }
    }
}

/**
 * 명령 패널 헤더
 */
@Composable
private fun CommandPanelHeader(
    historyCount: Int,
    onClearHistory: () -> Unit
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Row(
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "🎯",
                style = TextStyle(fontSize = 20.sp)
            )
            
            Column {
                Text(
                    text = "음성 명령",
                    style = TextStyle(
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                )
                
                Text(
                    text = "최근 $historyCount개 명령",
                    style = TextStyle(
                        fontSize = 11.sp,
                        color = Color.Gray
                    )
                )
            }
        }
        
        if (historyCount > 0) {
            TextButton(
                onClick = onClearHistory,
                colors = ButtonDefaults.textButtonColors(
                    contentColor = Color(0xFFFF6B35)
                )
            ) {
                Text(
                    text = "기록 삭제",
                    style = TextStyle(fontSize = 12.sp)
                )
            }
        }
    }
}

/**
 * 빠른 실행 버튼
 */
@Composable
private fun QuickActionButtons(
    onCommandSelect: (VoiceCommand) -> Unit
) {
    val quickCommands = listOf(
        VoiceCommand("nav_home", "집으로 안내", CommandCategory.NAVIGATION, "🏠"),
        VoiceCommand("call_emergency", "긴급 전화", CommandCategory.EMERGENCY, "🚨"),
        VoiceCommand("radio_on", "라디오 켜기", CommandCategory.MEDIA, "📻"),
        VoiceCommand("rest_area", "휴게소 찾기", CommandCategory.NAVIGATION, "⛽")
    )
    
    LazyRow(
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(quickCommands) { command ->
            QuickActionButton(
                command = command,
                onClick = { onCommandSelect(command) }
            )
        }
    }
}

/**
 * 빠른 실행 버튼 아이템
 */
@Composable
private fun QuickActionButton(
    command: VoiceCommand,
    onClick: () -> Unit
) {
    Card(
        onClick = onClick,
        modifier = Modifier.size(width = 80.dp, height = 60.dp),
        colors = CardDefaults.cardColors(
            containerColor = getCategoryColor(command.category).copy(alpha = 0.2f)
        ),
        shape = RoundedCornerShape(12.dp),
        border = BorderStroke(
            width = 1.dp,
            color = getCategoryColor(command.category).copy(alpha = 0.5f)
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(8.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = command.icon,
                style = TextStyle(fontSize = 20.sp)
            )
            
            Text(
                text = command.phrase.take(6),
                style = TextStyle(
                    fontSize = 10.sp,
                    color = Color.White
                ),
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
        }
    }
}

/**
 * 카테고리 탭
 */
@Composable
private fun CategoryTabs(
    categories: List<CommandCategory>,
    selectedCategory: CommandCategory?,
    onCategorySelect: (CommandCategory?) -> Unit
) {
    ScrollableTabRow(
        selectedTabIndex = selectedCategory?.let { categories.indexOf(it) } ?: -1,
        containerColor = Color.Transparent,
        contentColor = Color.White,
        edgePadding = 0.dp,
        indicator = { tabPositions ->
            if (selectedCategory != null) {
                val index = categories.indexOf(selectedCategory)
                if (index >= 0) {
                    TabRowDefaults.Indicator(
                        modifier = Modifier.tabIndicatorOffset(tabPositions[index]),
                        color = getCategoryColor(selectedCategory)
                    )
                }
            }
        }
    ) {
        // 히스토리 탭
        Tab(
            selected = selectedCategory == null,
            onClick = { onCategorySelect(null) },
            text = {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(4.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("📜", style = TextStyle(fontSize = 12.sp))
                    Text("기록", style = TextStyle(fontSize = 11.sp))
                }
            }
        )
        
        // 카테고리 탭들
        categories.forEach { category ->
            Tab(
                selected = selectedCategory == category,
                onClick = { onCategorySelect(category) },
                text = {
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(4.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = getCategoryEmoji(category),
                            style = TextStyle(fontSize = 12.sp)
                        )
                        Text(
                            text = getCategoryName(category),
                            style = TextStyle(fontSize = 11.sp)
                        )
                    }
                }
            )
        }
    }
}

/**
 * 명령어 목록
 */
@Composable
private fun CommandList(
    commands: List<VoiceCommand>,
    category: CommandCategory,
    onCommandSelect: (VoiceCommand) -> Unit
) {
    LazyColumn(
        verticalArrangement = Arrangement.spacedBy(8.dp),
        modifier = Modifier.heightIn(max = 300.dp)
    ) {
        items(commands) { command ->
            CommandItem(
                command = command,
                onClick = { onCommandSelect(command) }
            )
        }
    }
}

/**
 * 명령어 아이템
 */
@Composable
private fun CommandItem(
    command: VoiceCommand,
    onClick: () -> Unit
) {
    Card(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = Color.Black.copy(alpha = 0.3f)
        ),
        shape = RoundedCornerShape(8.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // 아이콘
            Box(
                modifier = Modifier
                    .size(32.dp)
                    .background(
                        color = getCategoryColor(command.category).copy(alpha = 0.2f),
                        shape = RoundedCornerShape(8.dp)
                    ),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = command.icon,
                    style = TextStyle(fontSize = 16.sp)
                )
            }
            
            // 명령어 텍스트
            Column(
                modifier = Modifier.weight(1f)
            ) {
                Text(
                    text = "\"${command.phrase}\"",
                    style = TextStyle(
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Medium,
                        color = Color.White
                    )
                )
                
                Text(
                    text = getCategoryName(command.category),
                    style = TextStyle(
                        fontSize = 10.sp,
                        color = getCategoryColor(command.category)
                    )
                )
            }
            
            // 음성 아이콘
            Text(
                text = "🎤",
                style = TextStyle(
                    fontSize = 14.sp,
                    color = Color.Gray
                )
            )
        }
    }
}

/**
 * 명령 히스토리
 */
@Composable
private fun CommandHistory(
    history: List<VoiceCommandEntry>
) {
    if (history.isEmpty()) {
        EmptyHistoryMessage()
    } else {
        LazyColumn(
            verticalArrangement = Arrangement.spacedBy(8.dp),
            modifier = Modifier.heightIn(max = 300.dp)
        ) {
            items(history) { entry ->
                HistoryItem(entry = entry)
            }
        }
    }
}

/**
 * 히스토리 아이템
 */
@Composable
private fun HistoryItem(entry: VoiceCommandEntry) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(
                color = Color.Black.copy(alpha = 0.2f),
                shape = RoundedCornerShape(8.dp)
            )
            .padding(12.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // 시간
        Text(
            text = formatTime(entry.timestamp),
            style = TextStyle(
                fontSize = 10.sp,
                color = Color.Gray,
                fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace
            ),
            modifier = Modifier.width(45.dp)
        )
        
        // 명령어
        Column(
            modifier = Modifier.weight(1f)
        ) {
            Text(
                text = entry.command.phrase,
                style = TextStyle(
                    fontSize = 12.sp,
                    color = Color.White
                ),
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
            
            entry.result?.let { result ->
                Text(
                    text = result,
                    style = TextStyle(
                        fontSize = 10.sp,
                        color = if (entry.success) Color(0xFF4CAF50) else Color(0xFFFF6B35)
                    ),
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
            }
        }
        
        // 상태 인디케이터
        Box(
            modifier = Modifier
                .size(8.dp)
                .background(
                    color = if (entry.success) Color(0xFF4CAF50) else Color(0xFFFF6B35),
                    shape = androidx.compose.foundation.shape.CircleShape
                )
        )
    }
}

/**
 * 빈 히스토리 메시지
 */
@Composable
private fun EmptyHistoryMessage() {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(100.dp)
            .background(
                color = Color.Black.copy(alpha = 0.2f),
                shape = RoundedCornerShape(8.dp)
            ),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = "📝",
                style = TextStyle(
                    fontSize = 24.sp,
                    color = Color.Gray
                ),
                modifier = Modifier.alpha(0.5f)
            )
            
            Text(
                text = "아직 명령 기록이 없습니다",
                style = TextStyle(
                    fontSize = 12.sp,
                    color = Color.Gray
                )
            )
        }
    }
}

// 데이터 클래스
data class VoiceCommandEntry(
    val command: VoiceCommand,
    val timestamp: Long,
    val success: Boolean,
    val result: String? = null
)

// 유틸리티 함수
private fun getCategoryName(category: CommandCategory): String {
    return when (category) {
        CommandCategory.NAVIGATION -> "내비게이션"
        CommandCategory.MEDIA -> "미디어"
        CommandCategory.VEHICLE -> "차량"
        CommandCategory.COMMUNICATION -> "통신"
        CommandCategory.EMERGENCY -> "긴급"
    }
}

private fun getCategoryEmoji(category: CommandCategory): String {
    return when (category) {
        CommandCategory.NAVIGATION -> "🗺️"
        CommandCategory.MEDIA -> "🎵"
        CommandCategory.VEHICLE -> "🚛"
        CommandCategory.COMMUNICATION -> "📞"
        CommandCategory.EMERGENCY -> "🚨"
    }
}

private fun getCategoryColor(category: CommandCategory): Color {
    return when (category) {
        CommandCategory.NAVIGATION -> Color(0xFF2196F3)
        CommandCategory.MEDIA -> Color(0xFF9C27B0)
        CommandCategory.VEHICLE -> Color(0xFF4CAF50)
        CommandCategory.COMMUNICATION -> Color(0xFF00BCD4)
        CommandCategory.EMERGENCY -> Color(0xFFFF5252)
    }
}

private fun formatTime(timestamp: Long): String {
    val now = System.currentTimeMillis()
    val diff = now - timestamp
    
    return when {
        diff < 60000 -> "방금"
        diff < 3600000 -> "${diff / 60000}분 전"
        diff < 86400000 -> "${diff / 3600000}시간 전"
        else -> "${diff / 86400000}일 전"
    }
}