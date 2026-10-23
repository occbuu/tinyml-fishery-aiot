/* Generated from training/validation only; feature order below. */
#pragma once
#include <math.h>
#define MODEL_INPUTS 10
/* y_lag0, y_lag1, y_lag2, y_lag3, y_lag6, y_mean6, y_delta, clock_sin, clock_cos, salinity */
static const float model_median[10] = {1.258215046e+01f,1.258069992e+01f,1.257999992e+01f,1.257935047e+01f,1.257845020e+01f,1.257924175e+01f,-2.649999922e-03f,1.224646853e-16f,-1.836970147e-16f,3.437099838e+01f};
static const float model_center[10] = {1.257852077e+01f,1.257702065e+01f,1.257550144e+01f,1.257400036e+01f,1.256950760e+01f,1.257476139e+01f,1.499825274e-03f,1.586523023e-03f,-4.673746414e-03f,3.433474731e+01f};
static const float model_scale[10] = {1.053473711e+00f,1.052617311e+00f,1.051739454e+00f,1.050870180e+00f,1.048007965e+00f,1.048825622e+00f,6.575035304e-02f,7.076357603e-01f,7.065601945e-01f,2.501059175e-01f};
static const float model_w[10] = {4.321000576e-01f,4.294652939e-01f,1.720057102e-03f,-6.421895325e-02f,9.636276215e-02f,1.513762772e-01f,4.780874401e-02f,1.034642803e-03f,-2.607058734e-02f,7.809943985e-03f};
static inline float model_predict(const float *raw) { float x[MODEL_INPUTS]; for(int i=0;i<MODEL_INPUTS;i++) x[i]=((isfinite(raw[i])?raw[i]:model_median[i])-model_center[i])/model_scale[i];
float out=1.258149776e+01f; for(int i=0;i<MODEL_INPUTS;i++) out+=x[i]*model_w[i]; return out; }
static inline void model_reset(void) {}