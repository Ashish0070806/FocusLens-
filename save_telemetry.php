<?php
/**
 * FocusLens - Save Telemetry Event API
 * Receives frontend telemetry actions (break start, breach acknowledgment, samples).
 */

require_once __DIR__ . '/db_config.php';

header('Content-Type: application/json; charset=utf-8');

$rawInput = file_get_contents('php://input');
$data = json_decode($rawInput, true);

if (!$data) {
    echo json_encode(['status' => 'ignored', 'message' => 'Empty or non-JSON payload']);
    exit;
}

$sessionId = 1;
$score = isset($data['focus_score']) ? (int)$data['focus_score'] : 70;
$fatigue = isset($data['fatigue']) ? (int)$data['fatigue'] : 20;
$event = isset($data['event']) ? $data['event'] : 'sample';
$isDistracted = ($event === 'breach' || $score < 40) ? 1 : 0;
$gaze = ($isDistracted) ? 'Away' : 'Screen';

try {
    // Optionally record specific frontend events if needed
    if ($event === 'breach' || $event === 'break_start' || $event === 'break_end') {
        $stmt = $pdo->prepare("
            INSERT INTO telemetry_logs (session_id, focus_score, fatigue_index, gaze_direction, is_distracted)
            VALUES (:session_id, :focus_score, :fatigue_index, :gaze_direction, :is_distracted)
        ");
        $stmt->execute([
            'session_id' => $sessionId,
            'focus_score' => $score,
            'fatigue_index' => $fatigue,
            'gaze_direction' => $gaze,
            'is_distracted' => $isDistracted
        ]);
    }

    echo json_encode(['status' => 'success', 'event' => $event]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
}
