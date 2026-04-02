/*
 * ============================================================================
 * Robot Hand - 5 Fingers
 * ============================================================================
 * Architecture: Layer 3 (Execution)
 * Description: Arduino firmware for 5-finger robotic hand control
 * Hardware: Arduino Uno + 5x SG90 Servos
 * 
 * Pin Configuration:
 *   D3  → Thumb servo
 *   D5  → Index servo
 *   D6  → Middle servo
 *   D9  → Ring servo
 *   D10 → Pinky servo
 * 
 * Communication: Serial (9600 baud)
 * Protocol: Text commands (OPEN, GRIP, HOME, SET:a,b,c,d,e, STATUS)
 * 
 * Safety:
 *   - Servo angles constrained to 0-180°
 *   - Smooth movement to prevent jitter
 *   - Timeout protection for serial commands
 * ============================================================================
 */

#include <Servo.h>

// ============================================================================
// Constants
// ============================================================================

constexpr int NUM_FINGERS = 5;
constexpr int DEFAULT_ANGLE = 90;
constexpr int MIN_ANGLE = 0;
constexpr int MAX_ANGLE = 180;
constexpr unsigned long BAUD_RATE = 9600;
constexpr unsigned long COMMAND_TIMEOUT = 1000;  // ms

// Servo pin assignments
const uint8_t SERVO_PINS[NUM_FINGERS] = {3, 5, 6, 9, 10};

// Finger names for debugging
const char* FINGER_NAMES[NUM_FINGERS] = {
    "Thumb", "Index", "Middle", "Ring", "Pinky"
};

// ============================================================================
// Global State
// ============================================================================

Servo servos[NUM_FINGERS];
int positions[NUM_FINGERS];
bool initialized = false;

// ============================================================================
// Function Declarations
// ============================================================================

void initSystem();
void processCommand(const String& cmd);
void parseSetCommand(const String& data);
void moveTo(const int targets[NUM_FINGERS], int duration);
void moveToAll(int angle);
void openHand();
void grip();
void testServos();
void printStatus();
void printHelp();

// ============================================================================
// Setup
// ============================================================================

void setup() {
    Serial.begin(BAUD_RATE);
    
    // Wait for serial connection
    delay(1000);
    
    initSystem();
}

// ============================================================================
// Main Loop
// ============================================================================

void loop() {
    static unsigned long lastCommandTime = 0;
    
    if (Serial.available() > 0) {
        lastCommandTime = millis();
        
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();
        
        if (cmd.length() > 0) {
            processCommand(cmd);
        }
    }
    
    // Timeout protection (optional - reset to home after inactivity)
    // if (millis() - lastCommandTime > COMMAND_TIMEOUT) {
    //     moveToAll(DEFAULT_ANGLE);
    //     lastCommandTime = millis();
    // }
}

// ============================================================================
// Initialization
// ============================================================================

void initSystem() {
    Serial.println(F("=== Robot Hand - 5 Fingers ==="));
    Serial.println(F("Initializing servos..."));
    
    // Initialize all servos
    for (int i = 0; i < NUM_FINGERS; i++) {
        positions[i] = DEFAULT_ANGLE;
        servos[i].attach(SERVO_PINS[i]);
        servos[i].write(positions[i]);
        delay(100);
        
        Serial.print(F("  "));
        Serial.print(FINGER_NAMES[i]);
        Serial.println(F(" OK"));
    }
    
    initialized = true;
    
    Serial.println(F("\n✓ READY!"));
    Serial.println(F("\nCommands: OPEN, GRIP, HOME, SET:a,b,c,d,e, STATUS, TEST, HELP"));
}

// ============================================================================
// Command Processing
// ============================================================================

void processCommand(const String& cmd) {
    if (cmd == F("OPEN")) {
        openHand();
        Serial.println(F("OPEN_OK"));
    }
    else if (cmd == F("GRIP")) {
        grip();
        Serial.println(F("GRIP_OK"));
    }
    else if (cmd == F("HOME")) {
        moveToAll(DEFAULT_ANGLE);
        Serial.println(F("HOME_OK"));
    }
    else if (cmd == F("STATUS")) {
        printStatus();
    }
    else if (cmd == F("TEST")) {
        testServos();
    }
    else if (cmd == F("HELP")) {
        printHelp();
    }
    else if (cmd.startsWith(F("SET:"))) {
        parseSetCommand(cmd.substring(4));
    }
    else {
        Serial.println(F("ERROR: Unknown command. Send HELP for list."));
    }
}

// ============================================================================
// Movement Functions
// ============================================================================

void moveTo(const int targets[NUM_FINGERS], int duration) {
    const int steps = 20;
    const int delayMs = max(1, duration / steps);
    
    // Smooth interpolation
    for (int step = 0; step < steps; step++) {
        for (int i = 0; i < NUM_FINGERS; i++) {
            int diff = targets[i] - positions[i];
            if (abs(diff) > 0) {
                positions[i] += diff / steps;
                positions[i] = constrain(positions[i], MIN_ANGLE, MAX_ANGLE);
                servos[i].write(positions[i]);
            }
        }
        delay(delayMs);
    }
    
    // Final position
    for (int i = 0; i < NUM_FINGERS; i++) {
        positions[i] = constrain(targets[i], MIN_ANGLE, MAX_ANGLE);
        servos[i].write(positions[i]);
    }
    delay(50);
}

void moveToAll(int angle) {
    int targets[NUM_FINGERS];
    for (int i = 0; i < NUM_FINGERS; i++) {
        targets[i] = angle;
    }
    moveTo(targets, 800);
}

void openHand() {
    int open[NUM_FINGERS] = {90, 90, 90, 90, 90};
    moveTo(open, 500);
}

void grip() {
    int grip[NUM_FINGERS] = {45, 20, 20, 20, 20};
    moveTo(grip, 800);
}

// ============================================================================
// Command Handlers
// ============================================================================

void parseSetCommand(const String& data) {
    int values[NUM_FINGERS];
    int idx = 0;
    int start = 0;
    
    for (int i = 0; i <= data.length() && idx < NUM_FINGERS; i++) {
        if (i == data.length() || data.charAt(i) == ',') {
            String val = data.substring(start, i);
            values[idx++] = constrain(val.toInt(), MIN_ANGLE, MAX_ANGLE);
            start = i + 1;
        }
    }
    
    if (idx == NUM_FINGERS) {
        moveTo(values, 800);
        Serial.println(F("SET_OK"));
    } else {
        Serial.print(F("ERROR: Expected "));
        Serial.print(NUM_FINGERS);
        Serial.print(F(" values, got "));
        Serial.println(idx);
    }
}

void printStatus() {
    Serial.print(F("POS:"));
    for (int i = 0; i < NUM_FINGERS; i++) {
        Serial.print(positions[i]);
        if (i < NUM_FINGERS - 1) Serial.print(F(","));
    }
    Serial.println();
}

void testServos() {
    Serial.println(F("\n=== Servo Test ==="));
    
    Serial.println(F("Moving to 0°..."));
    int zero[NUM_FINGERS] = {0, 0, 0, 0, 0};
    moveTo(zero, 1500);
    delay(1000);
    
    Serial.println(F("Moving to 90°..."));
    int center[NUM_FINGERS] = {90, 90, 90, 90, 90};
    moveTo(center, 1500);
    delay(1000);
    
    Serial.println(F("Moving to 180°..."));
    int maxPos[NUM_FINGERS] = {180, 180, 180, 180, 180};
    moveTo(maxPos, 1500);
    delay(1000);
    
    Serial.println(F("Moving to 90°..."));
    moveTo(center, 1500);
    
    Serial.println(F("\nTest complete!"));
}

void printHelp() {
    Serial.println(F("\n=== Commands ==="));
    Serial.println(F("OPEN        - Open hand (all 90°)"));
    Serial.println(F("GRIP        - Close grip"));
    Serial.println(F("HOME        - All to 90°"));
    Serial.println(F("STATUS      - Show current positions"));
    Serial.println(F("SET:a,b,c,d,e - Set angles (0-180)"));
    Serial.println(F("TEST        - Test all servos"));
    Serial.println(F("HELP        - Show this help"));
    Serial.println(F("\n=== Pin Map ==="));
    for (int i = 0; i < NUM_FINGERS; i++) {
        Serial.print(F("  D"));
        Serial.print(SERVO_PINS[i]);
        Serial.print(F(" → "));
        Serial.println(FINGER_NAMES[i]);
    }
    Serial.println();
}
