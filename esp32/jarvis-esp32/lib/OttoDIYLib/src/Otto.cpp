#if defined(ARDUINO) && ARDUINO >= 100
  #include "Arduino.h"
#else
  #include "WProgram.h"
  #include <pins_arduino.h>
#endif
#include "Otto.h"

Otto::Otto()
    : final_time(0),
      partial_time(0),
      isOttoResting(true)
{
    for (int i = 0; i < OTTO_SERVO_COUNT; i++) {
        servo_pins[i] = -1;
        servo_trim[i] = 0;
        increment[i] = 0.0f;
    }
}

void Otto::init(int pinYL, int pinYR, int pinRL, int pinRR, bool load_calibration)
{
    servo_pins[0] = pinYL;
    servo_pins[1] = pinYR;
    servo_pins[2] = pinRL;
    servo_pins[3] = pinRR;

    attachServos();
    isOttoResting = false;

    for (int i = 0; i < OTTO_SERVO_COUNT; i++) {
        servo[i].SetTrim(servo_trim[i]);
    }
}

void Otto::attachServos()
{
    for (int i = 0; i < OTTO_SERVO_COUNT; i++) {
        if (servo_pins[i] >= 0 && servo_pins[i] < 40 && !servo[i].isAttached()) {
            servo[i].attach(servo_pins[i]);
        }
    }
}

void Otto::detachServos()
{
    for (int i = 0; i < OTTO_SERVO_COUNT; i++) {
        servo[i].detach();
    }
}

void Otto::setTrims(int trimYL, int trimYR, int trimRL, int trimRR)
{
    servo_trim[0] = trimYL;
    servo_trim[1] = trimYR;
    servo_trim[2] = trimRL;
    servo_trim[3] = trimRR;

    for (int i = 0; i < OTTO_SERVO_COUNT; i++) {
        servo[i].SetTrim(servo_trim[i]);
    }
}

void Otto::setTrim(int index, int trim)
{
    if (index >= 0 && index < OTTO_SERVO_COUNT) {
        servo_trim[index] = trim;
        servo[index].SetTrim(trim);
    }
}

void Otto::enableServoLimit(int speed_limit_degree_per_sec)
{
    for (int i = 0; i < OTTO_SERVO_COUNT; i++) {
        servo[i].SetLimiter(speed_limit_degree_per_sec);
    }
}

void Otto::disableServoLimit()
{
    for (int i = 0; i < OTTO_SERVO_COUNT; i++) {
        servo[i].DisableLimiter();
    }
}

void Otto::_moveServos(int time, const int servo_target[OTTO_SERVO_COUNT])
{
    attachServos();
    if (getRestState()) {
        setRestState(false);
    }

    if (time <= 10) {
        for (int i = 0; i < OTTO_SERVO_COUNT; i++) {
            servo[i].SetPosition(servo_target[i]);
        }
        return;
    }

    for (int i = 0; i < OTTO_SERVO_COUNT; i++) {
        increment[i] = ((float)(servo_target[i] - servo[i].getPosition())) / ((float)time / 10.0f);
    }

    final_time = millis() + time;
    while (millis() < final_time) {
        partial_time = millis() + 10;
        for (int i = 0; i < OTTO_SERVO_COUNT; i++) {
            servo[i].SetPosition(round(servo[i].getPosition() + increment[i]));
        }
        while (millis() < partial_time) {
            delay(1);
        }
    }

    for (int i = 0; i < OTTO_SERVO_COUNT; i++) {
        servo[i].SetPosition(servo_target[i]);
    }
}

void Otto::_moveSingle(int position, int servo_number)
{
    if (servo_number < 0 || servo_number >= OTTO_SERVO_COUNT) {
        return;
    }
    attachServos();
    if (getRestState()) {
        setRestState(false);
    }
    servo[servo_number].SetPosition(position);
}

void Otto::oscillateServos(const int A[OTTO_SERVO_COUNT], const int O[OTTO_SERVO_COUNT], int T, const double phase_diff[OTTO_SERVO_COUNT], float cycle)
{
    attachServos();
    if (getRestState()) {
        setRestState(false);
    }

    for (int i = 0; i < OTTO_SERVO_COUNT; i++) {
        servo[i].SetO(O[i]);
        servo[i].SetA(A[i]);
        servo[i].SetT(T);
        servo[i].SetPh(phase_diff[i]);
    }

    double ref = millis();
    for (double x = ref; x <= ref + T * cycle; x = millis()) {
        for (int i = 0; i < OTTO_SERVO_COUNT; i++) {
            servo[i].refresh();
        }
        delay(1);
    }
}

void Otto::_execute(const int A[OTTO_SERVO_COUNT], const int O[OTTO_SERVO_COUNT], int T, const double phase_diff[OTTO_SERVO_COUNT], float steps)
{
    attachServos();
    if (getRestState()) {
        setRestState(false);
    }

    int cycles = (int)steps;
    if (cycles >= 1) {
        for (int i = 0; i < cycles; i++) {
            oscillateServos(A, O, T, phase_diff, 1.0f);
        }
    }
    float remaining = steps - (float)cycles;
    if (remaining > 0.0f) {
        oscillateServos(A, O, T, phase_diff, remaining);
    }
}

void Otto::home()
{
    int homes[OTTO_SERVO_COUNT] = {90, 90, 90, 90};
    _moveServos(400, homes);
    detachServos();
    isOttoResting = true;
}

void Otto::walk(float steps, int T, int dir)
{
    // A[0], A[1]: Legs (YL, YR); A[2], A[3]: Feet (RL, RR)
    int A[OTTO_SERVO_COUNT] = {30, 30, 20, 20};
    int O[OTTO_SERVO_COUNT] = {0, 0, 0, 0};
    double phase_diff[OTTO_SERVO_COUNT] = {0.0, 0.0, DEG2RAD(dir * -90), DEG2RAD(dir * -90)};
    _execute(A, O, T, phase_diff, steps);
    home();
}

void Otto::turn(float steps, int T, int dir)
{
    int A[OTTO_SERVO_COUNT] = {30, 30, 20, 20};
    int O[OTTO_SERVO_COUNT] = {0, 0, 0, 0};
    double phase_diff[OTTO_SERVO_COUNT];
    if (dir == LEFT) {
        phase_diff[0] = 0.0;
        phase_diff[1] = DEG2RAD(180);
        phase_diff[2] = DEG2RAD(90);
        phase_diff[3] = DEG2RAD(90);
    } else {
        phase_diff[0] = DEG2RAD(180);
        phase_diff[1] = 0.0;
        phase_diff[2] = DEG2RAD(-90);
        phase_diff[3] = DEG2RAD(-90);
    }
    _execute(A, O, T, phase_diff, steps);
    home();
}

void Otto::bend(int steps, int T, int dir)
{
    int bend1[OTTO_SERVO_COUNT] = {90, 90, 62, 35};
    int homes[OTTO_SERVO_COUNT] = {90, 90, 90, 90};
    for (int i = 0; i < steps; i++) {
        if (dir == RIGHT) {
            _moveServos(T / 2, bend1);
            _moveServos(T / 2, homes);
        } else {
            int bendLeft[OTTO_SERVO_COUNT] = {90, 90, 180 - 35, 180 - 62};
            _moveServos(T / 2, bendLeft);
            _moveServos(T / 2, homes);
        }
    }
    home();
}

void Otto::shakeLeg(int steps, int T, int dir)
{
    int numberLeg = (dir == RIGHT) ? 3 : 2;
    for (int i = 0; i < steps; i++) {
        _moveSingle(120, numberLeg);
        delay(T / 4);
        _moveSingle(60, numberLeg);
        delay(T / 2);
        _moveSingle(90, numberLeg);
        delay(T / 4);
    }
    home();
}

void Otto::updown(float steps, int T, int h)
{
    int A[OTTO_SERVO_COUNT] = {0, 0, h, h};
    int O[OTTO_SERVO_COUNT] = {0, 0, 0, 0};
    double phase_diff[OTTO_SERVO_COUNT] = {0.0, 0.0, DEG2RAD(-90), DEG2RAD(90)};
    _execute(A, O, T, phase_diff, steps);
    home();
}

void Otto::swing(float steps, int T, int h)
{
    int A[OTTO_SERVO_COUNT] = {0, 0, h, h};
    int O[OTTO_SERVO_COUNT] = {0, 0, 0, 0};
    double phase_diff[OTTO_SERVO_COUNT] = {0.0, 0.0, 0.0, 0.0};
    _execute(A, O, T, phase_diff, steps);
    home();
}

void Otto::tiptoeSwing(float steps, int T, int h)
{
    int A[OTTO_SERVO_COUNT] = {0, 0, h, h};
    int O[OTTO_SERVO_COUNT] = {0, 0, 0, 0};
    double phase_diff[OTTO_SERVO_COUNT] = {0.0, 0.0, DEG2RAD(180), 0.0};
    _execute(A, O, T, phase_diff, steps);
    home();
}

void Otto::jitter(float steps, int T, int h)
{
    int A[OTTO_SERVO_COUNT] = {h, h, 0, 0};
    int O[OTTO_SERVO_COUNT] = {0, 0, 0, 0};
    double phase_diff[OTTO_SERVO_COUNT] = {0.0, DEG2RAD(180), 0.0, 0.0};
    _execute(A, O, T, phase_diff, steps);
    home();
}

void Otto::ascendingTurn(float steps, int T, int h)
{
    int A[OTTO_SERVO_COUNT] = {h, h, h, h};
    int O[OTTO_SERVO_COUNT] = {0, 0, 0, 0};
    double phase_diff[OTTO_SERVO_COUNT] = {0.0, DEG2RAD(180), DEG2RAD(90), DEG2RAD(90)};
    _execute(A, O, T, phase_diff, steps);
    home();
}

void Otto::moonwalker(float steps, int T, int h, int dir)
{
    int A[OTTO_SERVO_COUNT] = {0, 0, h, h};
    int O[OTTO_SERVO_COUNT] = {0, 0, 0, 0};
    double phase_diff[OTTO_SERVO_COUNT] = {0.0, 0.0, 0.0, DEG2RAD(180 * dir)};
    _execute(A, O, T, phase_diff, steps);
    home();
}

void Otto::crusaito(float steps, int T, int h, int dir)
{
    int A[OTTO_SERVO_COUNT] = {25, 25, h, h};
    int O[OTTO_SERVO_COUNT] = {0, 0, 0, 0};
    double phase_diff[OTTO_SERVO_COUNT] = {DEG2RAD(90 * dir), DEG2RAD(90 * dir), 0.0, 0.0};
    _execute(A, O, T, phase_diff, steps);
    home();
}

void Otto::flapping(float steps, int T, int h, int dir)
{
    int A[OTTO_SERVO_COUNT] = {12, 12, h, h};
    int O[OTTO_SERVO_COUNT] = {0, 0, 0, 0};
    double phase_diff[OTTO_SERVO_COUNT] = {0.0, DEG2RAD(180), DEG2RAD(90 * dir), DEG2RAD(90 * dir)};
    _execute(A, O, T, phase_diff, steps);
    home();
}

void Otto::jump(float steps, int T)
{
    int crouch[OTTO_SERVO_COUNT] = {90, 90, 115, 65};
    int up[OTTO_SERVO_COUNT] = {90, 90, 90, 90};
    for (int i = 0; i < (int)steps; i++) {
        _moveServos(T / 2, crouch);
        _moveServos(T / 2, up);
    }
    home();
}

void Otto::nod(int steps, int T)
{
    int A[OTTO_SERVO_COUNT] = {0, 0, 20, 20};
    int O[OTTO_SERVO_COUNT] = {0, 0, 0, 0};
    double phase_diff[OTTO_SERVO_COUNT] = {0.0, 0.0, DEG2RAD(-90), DEG2RAD(90)};
    _execute(A, O, T, phase_diff, (float)steps);
    home();
}

void Otto::shake(int steps, int T)
{
    int A[OTTO_SERVO_COUNT] = {25, 25, 0, 0};
    int O[OTTO_SERVO_COUNT] = {0, 0, 0, 0};
    double phase_diff[OTTO_SERVO_COUNT] = {0.0, DEG2RAD(180), 0.0, 0.0};
    _execute(A, O, T, phase_diff, (float)steps);
    home();
}

void Otto::playGesture(int gesture)
{
    switch (gesture) {
        case OttoHappy:
            swing(2, 600, 25);
            updown(2, 500, 20);
            home();
            break;

        case OttoSuperHappy:
            crusaito(2, 600, 20, FORWARD);
            jump(1, 600);
            home();
            break;

        case OttoSad:
            bend(1, 1400, LEFT);
            bend(1, 1400, RIGHT);
            home();
            break;

        case OttoSleeping: {
            int sleepPose[OTTO_SERVO_COUNT] = {90, 90, 75, 105};
            _moveServos(1000, sleepPose);
            delay(500);
            home();
            break;
        }

        case OttoFart:
            bend(1, 800, RIGHT);
            jitter(2, 300, 15);
            home();
            break;

        case OttoConfused:
            bend(1, 1000, LEFT);
            shake(2, 600);
            home();
            break;

        case OttoLove:
            swing(3, 800, 25);
            home();
            break;

        case OttoAngry:
            jitter(3, 300, 20);
            bend(1, 600, RIGHT);
            home();
            break;

        case OttoFretful:
            jitter(3, 350, 15);
            home();
            break;

        case OttoMagic:
            flapping(2, 700, 20, FORWARD);
            home();
            break;

        case OttoWave:
            shakeLeg(2, 800, RIGHT);
            home();
            break;

        case OttoVictory:
            crusaito(2, 700, 20, FORWARD);
            jump(2, 600);
            home();
            break;

        case OttoFail:
            bend(1, 1200, RIGHT);
            shake(2, 800);
            home();
            break;

        default:
            home();
            break;
    }
}
