/* Generated from training/validation only; feature order below. */
#pragma once
#include <math.h>
#define MODEL_INPUTS 11
/* y_lag0, y_lag1, y_lag2, y_lag3, y_lag6, y_mean6, y_delta, clock_sin, clock_cos, temperature, tds */
static const float model_median[11] = {8.039999962e+00f,8.050000191e+00f,8.050000191e+00f,8.045000076e+00f,8.034999847e+00f,8.018333435e+00f,0.000000000e+00f,2.164396197e-01f,2.164396197e-01f,2.425000000e+01f,3.400000000e+02f};
static const float model_center[11] = {8.152433395e+00f,8.148400307e+00f,8.148384094e+00f,8.140103340e+00f,8.135348320e+00f,8.149225235e+00f,2.767044585e-03f,1.076178029e-01f,1.326395571e-01f,2.410674667e+01f,3.416668701e+02f};
static const float model_scale[11] = {1.411459208e+00f,1.389611244e+00f,1.382085323e+00f,1.371185422e+00f,1.366844535e+00f,1.388835907e+00f,3.978717625e-01f,7.096473575e-01f,6.835391521e-01f,9.313215613e-01f,4.612086487e+01f};
static const float model_w[11] = {2.773977816e-01f,-6.439767778e-03f,4.426972941e-02f,5.219235644e-02f,4.861490428e-02f,9.357314110e-01f,-2.569310926e-02f,-8.411204442e-03f,1.909038238e-02f,-9.706718847e-03f,1.943914779e-02f};
static inline float model_predict(const float *raw) { float x[MODEL_INPUTS]; for(int i=0;i<MODEL_INPUTS;i++) x[i]=((isfinite(raw[i])?raw[i]:model_median[i])-model_center[i])/model_scale[i];
float out=8.163870923e+00f; for(int i=0;i<MODEL_INPUTS;i++) out+=x[i]*model_w[i]; return out; }
static inline void model_reset(void) {}