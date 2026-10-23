/* Generated from training/validation only; feature order below. */
#pragma once
#include <math.h>
#define MODEL_INPUTS 12
/* y_lag0, y_lag1, y_lag2, y_lag3, y_lag6, y_mean6, y_delta, clock_sin, clock_cos, temperature, turbidity, bottom_temperature */
static const float model_median[12] = {7.800000191e+00f,7.800000191e+00f,7.800000191e+00f,7.800000191e+00f,7.800000191e+00f,7.800000191e+00f,0.000000000e+00f,-6.540312618e-02f,1.736481786e-01f,2.002000046e+01f,2.080000000e+02f,2.162000084e+01f};
static const float model_center[12] = {7.810773849e+00f,7.811249256e+00f,7.811889172e+00f,7.812647343e+00f,7.814929485e+00f,7.811528683e+00f,-2.945797460e-04f,-4.079594091e-02f,7.802145183e-02f,2.021142960e+01f,2.074395142e+02f,2.180347252e+01f};
static const float model_scale[12] = {4.152210653e-01f,4.143498838e-01f,4.137651920e-01f,4.131744206e-01f,4.114876688e-01f,4.141126275e-01f,1.253007445e-02f,7.046040893e-01f,7.041174769e-01f,1.850394011e+00f,9.438823700e+00f,1.431905866e+00f};
static const float model_w[12] = {3.269522190e-01f,1.001373157e-01f,1.644352078e-02f,-2.236489765e-02f,-3.851173073e-02f,2.338919789e-02f,6.093552709e-02f,-7.255603094e-03f,4.442457575e-03f,4.602742381e-03f,-1.828713925e-03f,-5.655395333e-03f};
static inline float model_predict(const float *raw) { float x[MODEL_INPUTS]; for(int i=0;i<MODEL_INPUTS;i++) x[i]=((isfinite(raw[i])?raw[i]:model_median[i])-model_center[i])/model_scale[i];
float out=7.809021995e+00f; for(int i=0;i<MODEL_INPUTS;i++) out+=x[i]*model_w[i]; return out; }
static inline void model_reset(void) {}