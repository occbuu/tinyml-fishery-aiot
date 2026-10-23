/* Generated from training/validation only; feature order below. */
#pragma once
#include <math.h>
#define MODEL_INPUTS 10
/* y_lag0, y_lag1, y_lag2, y_lag3, y_lag6, y_mean6, y_delta, clock_sin, clock_cos, salinity */
static float model_last=1.258149776e+01f;
static inline void model_reset(void) { model_last=1.258149776e+01f; }
static inline float model_predict(const float *raw) { if(isfinite(raw[0])) model_last=raw[0]; return model_last; }