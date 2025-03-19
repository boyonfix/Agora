// Dial encoder pins
#define CLK 2
#define DT 4
#define SW 7

// Button pins
#define BUTTON_A 15 // Adjusted to avoid conflict
#define BUTTON_B 14

// Switch pins
#define SWITCH_PIN1 48 // One state of the switch
#define SWITCH_PIN2 50 // Other state of the switch

// Rotary encoder variables
int counter = 0; // Counter to track rotation
int lastStateCLK;
bool buttonALastState = HIGH;
bool buttonBLastState = HIGH;

// Debounce variables
unsigned long lastDebounceTimeA = 0;
unsigned long lastDebounceTimeB = 0;
unsigned long debounceDelay = 50; // milliseconds

// State tracking for the switch
String lastMode = ""; // Keeps track of the last switch state

void setup() {
  // Initialize Serial communication
  Serial.begin(9600);

  // Pins as inputs
  pinMode(CLK, INPUT);
  pinMode(DT, INPUT);
  pinMode(SW, INPUT_PULLUP); // Use internal pull-up for the button
  pinMode(BUTTON_A, INPUT_PULLUP);
  pinMode(BUTTON_B, INPUT_PULLUP);
  pinMode(SWITCH_PIN1, INPUT_PULLUP);
  pinMode(SWITCH_PIN2, INPUT_PULLUP);

  // Read the initial state of the CLK pin
  lastStateCLK = digitalRead(CLK);

  Serial.println("Arduino with Switch, Rotary Encoder, and Buttons Ready!");
}

void loop() {
  // Handle switch state
  int state1 = digitalRead(SWITCH_PIN1);
  int state2 = digitalRead(SWITCH_PIN2);
  String currentMode;

  if (state1 == LOW && state2 == HIGH) {
    currentMode = "topic";
  } else if (state1 == HIGH && state2 == LOW) {
    currentMode = "time";
  } else {
    currentMode = ""; // Invalid state or switch in neutral position
  }

  // Output the mode only when it changes
  if (currentMode != lastMode) {
    lastMode = currentMode;
    if (currentMode.length() > 0) { // Check if the string is not empty
      Serial.println(currentMode);
    }
  }

  // Read the current state of the CLK pin
  int currentStateCLK = digitalRead(CLK);

  // If the state has changed, check the direction
  if (currentStateCLK != lastStateCLK) {
    if (currentStateCLK == HIGH) { // Only act on rising edge
      if (digitalRead(DT) != currentStateCLK) {
        counter++; // Clockwise
      } else {
        counter--; // Counterclockwise
      }

      // Restrict counter to not go below zero
      if (counter < 0) {
        counter = 0; // Reset to zero if it goes negative
      }

      // Print the counter value
      Serial.print("Rotation Count: ");
      Serial.println(counter);
    }
  }

  lastStateCLK = currentStateCLK; // Update lastStateCLK

  // Read button A state and check if it has just been pressed and released (debounced)
  int buttonAState = digitalRead(BUTTON_A);
  if (buttonAState == LOW && buttonALastState == HIGH && (millis() - lastDebounceTimeA > debounceDelay)) {
    Serial.println("next");
    lastDebounceTimeA = millis(); // Update debounce timer for button A
  }
  buttonALastState = buttonAState; // Store the last state of button A

  // Read button B state and check if it has just been pressed and released (debounced)
  int buttonBState = digitalRead(BUTTON_B);
  if (buttonBState == LOW && buttonBLastState == HIGH && (millis() - lastDebounceTimeB > debounceDelay)) {
    Serial.println("previous");
    lastDebounceTimeB = millis(); // Update debounce timer for button B
  }
  buttonBLastState = buttonBState; // Store the last state of button B

  delay(10); // Small delay for stability
}
