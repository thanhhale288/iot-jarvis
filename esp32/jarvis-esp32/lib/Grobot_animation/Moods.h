#ifndef MOODS_H
#define MOODS_H

struct MoodData {
    float topH;
    float botH;
    float tilt;
    float pR;
    float radius;
};

// Preset Moods
const MoodData MOOD_NEUTRAL     = {0, 0, 0, 30, 45};
const MoodData MOOD_HAPPY       = {0, 50, 0, 30, 45};
const MoodData MOOD_ANGRY       = {0, 0, 60, 30, 45};
const MoodData MOOD_SAD         = {0, 0, -60, 27, 45};
const MoodData MOOD_WINK        = {0, 35, 25, 0, 45};

// Additional Jarvis Application Mappings
const MoodData MOOD_QUESTIONING = {0, 25, 30, 32, 45}; // Listening / curious
const MoodData MOOD_THINKING    = {15, 0, -25, 25, 45}; // Thinking
const MoodData MOOD_EXCITED     = {0, 45, 10, 35, 48};  // Speaking / active
const MoodData MOOD_ALERT       = {0, 0, 55, 32, 45};   // Alert / warning

#endif