#ifndef Otto_h
#define Otto_h

#include <Arduino.h>
#include "Oscillator.h"
#include "Otto_gestures.h"

// 4 physical servos for standard Otto DIY (2 legs + 2 feet)
#define OTTO_SERVO_COUNT 4

// Servo index conventions:
// 0: Left Leg (YL - Yaw Left)
// 1: Right Leg (YR - Yaw Right)
// 2: Left Foot (RL - Roll Left)
// 3: Right Foot (RR - Roll Right)

// Motion direction constants
#define FORWARD     1
#define BACKWARD   -1
#define LEFT        1
#define RIGHT      -1

// Servo speed delta limit default (deg / sec)
#define SERVO_LIMIT_DEFAULT 240

class Otto
{
  public:
    Otto();

    // Otto initialization (4 servos: YL, YR, RL, RR)
    void init(int pinYL, int pinYR, int pinRL, int pinRR, bool load_calibration = false);

    // Attach & Detach
    void attachServos();
    void detachServos();

    // Oscillator Trims
    void setTrims(int trimYL, int trimYR, int trimRL, int trimRR);
    void setTrim(int index, int trim);

    // Motion Primitives
    void _moveServos(int time, const int servo_target[OTTO_SERVO_COUNT]);
    void _moveSingle(int position, int servo_number);
    void oscillateServos(const int A[OTTO_SERVO_COUNT], const int O[OTTO_SERVO_COUNT], int T, const double phase_diff[OTTO_SERVO_COUNT], float cycle = 1.0f);

    // Rest State
    void home();
    bool getRestState() const { return isOttoResting; }
    void setRestState(bool state) { isOttoResting = state; }

    // 4-Servo Standard Otto DIY Gaits & Motions
    void walk(float steps = 4, int T = 1000, int dir = FORWARD);
    void turn(float steps = 4, int T = 2000, int dir = LEFT);
    void bend(int steps = 1, int T = 1400, int dir = LEFT);
    void shakeLeg(int steps = 1, int T = 2000, int dir = RIGHT);
    void jump(float steps = 1, int T = 1000);
    void updown(float steps = 1, int T = 1000, int h = 20);
    void swing(float steps = 1, int T = 1000, int h = 20);
    void tiptoeSwing(float steps = 1, int T = 900, int h = 20);
    void jitter(float steps = 1, int T = 500, int h = 20);
    void ascendingTurn(float steps = 1, int T = 900, int h = 20);
    void moonwalker(float steps = 1, int T = 900, int h = 20, int dir = LEFT);
    void crusaito(float steps = 1, int T = 900, int h = 20, int dir = FORWARD);
    void flapping(float steps = 1, int T = 1000, int h = 20, int dir = FORWARD);

    // Jarvis Expressive Motions
    void nod(int steps = 2, int T = 800);
    void shake(int steps = 2, int T = 800);

    // Gestures (Motion-only, NO sound/matrix dependency)
    void playGesture(int gesture);

    // Servo Limiter
    void enableServoLimit(int speed_limit_degree_per_sec = SERVO_LIMIT_DEFAULT);
    void disableServoLimit();

  private:
    Oscillator servo[OTTO_SERVO_COUNT];
    int servo_pins[OTTO_SERVO_COUNT];
    int servo_trim[OTTO_SERVO_COUNT];

    unsigned long final_time;
    unsigned long partial_time;
    float increment[OTTO_SERVO_COUNT];
    bool isOttoResting;

    void _execute(const int A[OTTO_SERVO_COUNT], const int O[OTTO_SERVO_COUNT], int T, const double phase_diff[OTTO_SERVO_COUNT], float steps = 1.0f);
};

#endif
