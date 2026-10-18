<?php
/**
 * FocusLens - Get Dashboard Telemetry API
 * Supplies real-time telemetry, session metrics, and timeline for index.html.
 */

require_once __DIR__ . '/db_config.php';

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store, no-cache, must-revalidate');

$sessionId = 1;

try {
    // 1. Fetch latest telemetry entry for session
    $stmt = $pdo->prepare("
        SELECT focus_score, fatigue_index, gaze_direction, is_distracted, created_at
        FROM telemetry_logs
        WHERE session_id = :sessionId
        ORDER BY id DESC
        LIMIT 1
    ");
    $stmt->execute(['sessionId' => $sessionId]);
    $latest = $stmt->fetch();

    if (!$latest) {
        // Fallback default state if simulator has just started
        echo json_encode([
            'focus_score' => 85,
            'fatigue' => 15,
            'focus_seconds' => 0,
            'distractions' => 0,
            'timeline' => []
        ]);
        exit;
    }

    // 2. Fetch last 40 rows for the timeline chart
    $timelineStmt = $pdo->prepare("
        SELECT created_at, focus_score, fatigue_index
        FROM telemetry_logs
        WHERE session_id = :sessionId
        ORDER BY id DESC
        LIMIT 40
    ");
    $timelineStmt->execute(['sessionId' => $sessionId]);
    $timelineRows = array_reverse($timelineStmt->fetchAll());

    $timeline = [];
    foreach ($timelineRows as $row) {
        $timeline[] = [
            'time' => date('H:i:s', strtotime($row['created_at'])),
            'score' => (int)$row['focus_score'],
            'fatigue' => (int)$row['fatigue_index']
        ];
    }

    // 3. Aggregate session stats:
    // Focus seconds: samples where score >= 50, each sample represents 3 seconds
    $focusCountStmt = $pdo->prepare("
        SELECT COUNT(*) AS focus_samples
        FROM telemetry_logs
        WHERE session_id = :sessionId AND focus_score >= 50
    ");
    $focusCountStmt->execute(['sessionId' => $sessionId]);
    $focusSamples = (int)$focusCountStmt->fetchColumn();
    $focusSeconds = $focusSamples * 3;

    // Distractions count: total samples where is_distracted = 1 (or score < 40)
    $distractStmt = $pdo->prepare("
        SELECT COUNT(*) AS distract_count
        FROM telemetry_logs
        WHERE session_id = :sessionId AND is_distracted = 1
    ");
    $distractStmt->execute(['sessionId' => $sessionId]);
    $distractions = (int)$distractStmt->fetchColumn();

    // 4. Return formatted response matching index.html API contract
    echo json_encode([
        'focus_score' => (int)$latest['focus_score'],
        'fatigue' => (int)$latest['fatigue_index'],
        'focus_seconds' => $focusSeconds,
        'distractions' => $distractions,
        'timeline' => $timeline
    ], JSON_PRETTY_PRINT);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'error' => 'Query execution error',
        'details' => $e->getMessage()
    ]);
}
