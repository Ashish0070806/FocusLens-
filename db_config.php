<?php
/**
 * FocusLens - Database Configuration
 * Connects to local MariaDB/MySQL server.
 */

if (!headers_sent()) {
    header('Access-Control-Allow-Origin: *');
    header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type, Accept');
}

if (isset($_SERVER['REQUEST_METHOD']) && $_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

$host = '127.0.0.1';
$ports = [3306, 3308];
$user = 'root';
$password = '';
$database = 'focuslens_db';

$pdo = null;

foreach ($ports as $port) {
    try {
        $dsn = "mysql:host=$host;port=$port;dbname=$database;charset=utf8mb4";
        $pdo = new PDO($dsn, $user, $password, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_TIMEOUT => 2
        ]);
        break; // Connected successfully
    } catch (PDOException $e) {
        // Try next candidate port
        continue;
    }
}

if (!$pdo) {
    http_response_code(503);
    header('Content-Type: application/json');
    echo json_encode([
        'error' => 'Database connection failed',
        'details' => 'Could not connect to MariaDB on 127.0.0.1 (ports 3306, 3308). Please ensure MariaDB/MySQL is running.'
    ]);
    exit;
}
