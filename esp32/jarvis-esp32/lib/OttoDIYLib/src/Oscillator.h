#ifndef Oscillator_h
#define Oscillator_h

#include <Arduino.h>
#ifdef ARDUINO_ARCH_ESP32
#include <ESP32Servo.h>
#else
#include <Servo.h>
#endif
#include <math.h>

#ifndef DEG2RAD
  #define DEG2RAD(g) (((g) * M_PI) / 180.0)
#endif

class Oscillator
{
  public:
    Oscillator(int trim = 0);
    void attach(int pin, bool rev = false);
    void detach();

    void SetA(unsigned int amplitude) { _amplitude = amplitude; }
    void SetO(int offset) { _offset = offset; }
    void SetPh(double Ph) { _phase0 = Ph; }
    void SetT(unsigned int period);
    void SetTrim(int trim) { _trim = trim; }
    void SetLimiter(int diff_limit) { _diff_limit = diff_limit; }
    void DisableLimiter() { _diff_limit = 0; }
    int getTrim() const { return _trim; }
    void SetPosition(int position);
    void Stop() { _stop = true; }
    void Play() { _stop = false; }
    void Reset() { _phase = 0; }
    void refresh();
    int getPosition() const { return _pos; }
    bool isAttached() const;

  private:
    bool next_sample();
    void write(int position);

  private:
    Servo _servo;

    unsigned int _amplitude;
    int _offset;
    unsigned int _period;
    double _phase0;

    int _pos;
    int _trim;
    double _phase;
    double _inc;
    double _numberSamples;
    unsigned int _samplingPeriod;

    unsigned long _previousMillis;
    unsigned long _currentMillis;

    bool _stop;
    bool _rev;

    int _diff_limit;
    unsigned long _previousServoCommandMillis;
};

#endif
