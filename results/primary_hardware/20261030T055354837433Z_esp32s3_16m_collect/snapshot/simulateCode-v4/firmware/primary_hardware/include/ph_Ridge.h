/* Generated from training/validation only; feature order below. */
#pragma once
#include <math.h>
#define MODEL_INPUTS 9
/* y_lag0, y_lag1, y_lag2, y_lag3, y_lag6, y_mean6, y_delta, clock_sin, clock_cos */
static const float model_median[9] = {7.900000095e+00f,7.900000095e+00f,7.900000095e+00f,7.900000095e+00f,7.900000095e+00f,7.833333492e+00f,0.000000000e+00f,0.000000000e+00f,1.000000000e+00f};
static const float model_center[9] = {7.851543427e+00f,7.854321003e+00f,7.858950615e+00f,7.862654209e+00f,7.867283821e+00f,7.856101036e+00f,-1.851851819e-03f,0.000000000e+00f,1.000000000e+00f};
static const float model_scale[9] = {5.328968763e-01f,5.315477848e-01f,5.275263786e-01f,5.259269476e-01f,5.212556124e-01f,3.293143213e-01f,6.378951073e-01f,1.000000000e+00f,1.000000000e+00f};
static const float model_w[9] = {2.921572514e-02f,9.076514281e-03f,9.391824715e-03f,9.343309328e-03f,3.585672006e-02f,1.670909822e-01f,2.997126896e-03f,0.000000000e+00f,0.000000000e+00f};
static inline float model_predict(const float *raw) { float x[MODEL_INPUTS]; for(int i=0;i<MODEL_INPUTS;i++) x[i]=((isfinite(raw[i])?raw[i]:model_median[i])-model_center[i])/model_scale[i];
float out=7.851543210e+00f; for(int i=0;i<MODEL_INPUTS;i++) out+=x[i]*model_w[i]; return out; }
static inline void model_reset(void) {}