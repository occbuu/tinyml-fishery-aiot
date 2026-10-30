#include <Arduino.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include "models.h"

static char line[640];
static size_t used=0;
static volatile float sink;
static const int dims[]={9,9,9,10,10};

void process(char* text) {
  if(!strcmp(text,"INFO")) {
    Serial.printf("INFO,PRIMARY_V4,20261030,%u,%u\n",ESP.getCpuFreqMHz(),ESP.getFreeHeap());return;
  }
  if(!strcmp(text,"RESET")){reset_models();Serial.println("RESET,OK");return;}
  char* state=nullptr;
  char* token=strtok_r(text,",",&state);
  if(!token||strcmp(token,"P")){Serial.println("ERROR,COMMAND");return;}
  token=strtok_r(nullptr,",",&state);if(!token){Serial.println("ERROR,ID");return;}int id=atoi(token);
  token=strtok_r(nullptr,",",&state);if(!token){Serial.println("ERROR,MODEL");return;}int model=atoi(token);
  if(model<0||model>=5){Serial.println("ERROR,MODEL");return;}
  double x[10]={0};
  for(int i=0;i<dims[model];i++){
    token=strtok_r(nullptr,",",&state);if(!token){Serial.println("ERROR,INPUTS");return;}
    char* end=nullptr;x[i]=strtod(token,&end);
    if(end==token||*end){Serial.println("ERROR,NUMBER");return;}
  }
  if(strtok_r(nullptr,",",&state)){Serial.println("ERROR,EXTRA");return;}
  float value=dispatch(model,x); // warm-up, parity value outside timing
  uint32_t heap_before=ESP.getFreeHeap();
  uint32_t start=micros();
  for(int i=0;i<64;i++){
    asm volatile("" ::: "memory"); // prevent hoisting invariant-input inference
    sink=dispatch(model,x);
  }
  uint32_t elapsed=micros()-start;
  uint32_t heap_after=ESP.getFreeHeap();
  Serial.printf("R,%d,%d,%.9g,%lu,%u,%u\n",id,model,(double)value,(unsigned long)elapsed,heap_before,heap_after);
}
void setup(){Serial.begin(115200);reset_models();}
void loop(){
  while(Serial.available()){
    char ch=(char)Serial.read();if(ch=='\r')continue;
    if(ch=='\n'){line[used]=0;process(line);used=0;}
    else if(used+1<sizeof(line))line[used++]=ch;
    else{used=0;Serial.println("ERROR,OVERFLOW");}
  }
  yield();
}
