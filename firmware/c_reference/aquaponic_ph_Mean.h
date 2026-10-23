/* Generated from training/validation only; feature order below. */
#pragma once
#include <math.h>
#define MODEL_INPUTS 11
/* y_lag0, y_lag1, y_lag2, y_lag3, y_lag6, y_mean6, y_delta, clock_sin, clock_cos, temperature, tds */
static inline void model_reset(void) {}
static inline float model_predict(const float *raw) { (void)raw; return 8.163870923e+00f; }