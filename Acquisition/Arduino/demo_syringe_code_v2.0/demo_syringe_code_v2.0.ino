//Declare Arduino to stepper PCB pinout
#define stp 2
#define dir 3
#define MS1 4
#define MS2 5
#define MS3 6
#define EN  7
#define EOT_1 11
#define EOT_2 12
#define ledPin 14
#define gndledPin 15
unsigned int timeout = 60000;
int incomingByte;
String str2Print;
String str;
long timeNow;
bool parseChar;
unsigned int nSteps = 10; //default step size
unsigned int resolution = 8; //default resolution, 1 2 3 or 4;
bool thisDir = 1; //default direction
String helpString = "HELP MENU\n f = Move forward\n b = Move Backwards\n o = HomeOut\n i = HomeIn\n r = Set Resolution\n s = Set Number of Steps\n p = Print diagnosis\n h = Help\n";
unsigned int ipi = 1000;

void setup() {
  Serial.begin(9600);
  //Initialize pins
  pinMode(stp, OUTPUT);
  pinMode(dir, OUTPUT);
  pinMode(MS1, OUTPUT);
  pinMode(MS2, OUTPUT);
  pinMode(MS3, OUTPUT);
  pinMode(EN, OUTPUT);
  pinMode(ledPin, OUTPUT);
  pinMode(gndledPin, OUTPUT);
  digitalWrite(ledPin, 0);
  
  digitalWrite(gndledPin,0);
  pinMode(EOT_1, INPUT);
  pinMode(EOT_2, INPUT);

  resetEDPins(); //Set step, direction, microstep and enable pins to default states

  printDiagnosis();

}

void loop() {
  if (Serial.available() > 0) {
    incomingByte = Serial.read();
    parseSerial(incomingByte);
    serialFlush(); //Discard all other bytes jic;
    printDiagnosis();

  }


}


void resetEDPins()
{
  digitalWrite(stp, LOW);
  digitalWrite(dir, LOW);
  digitalWrite(MS1, LOW);
  digitalWrite(MS2, LOW);
  digitalWrite(MS3, LOW);
  digitalWrite(EN, LOW);//HIGH
}


void parseSerial(int parsing_character) {

  switch (parsing_character)
  {

    case 'i': //SUCK EVERYTTHING
      str2Print = "SUCKING EVERYTHING IN";
      Serial.print(str2Print);
      thisDir = 0;
      HomeFunction();
      break;

    case 'o': //PUSH EVERYTTHING
      str2Print = "EVERYTHING OUT";
      Serial.print(str2Print);
      thisDir = 1;
      HomeFunction();

    case 'f': //Forward
      str2Print = "Moving Forward with settings: ";
      str2Print += constructStringSettings();
      Serial.print(str2Print);
      thisDir = 1;
      digitalWrite(ledPin, 1);
      doTheStep();
      delay(200);
      digitalWrite(ledPin, 0);
      break;

    case 'b': //Backwards
      str2Print = "Moving backwards with settings: ";
      str2Print += constructStringSettings();
      Serial.print(str2Print);
      thisDir = 0;
      doTheStep();
      break;

    case 'r':
      parseChar = false;
      Serial.println("Input new resolution (1-4): ");
      timeNow = millis();
      serialFlush();
      while (millis() - timeNow < timeout) {
        delay(2);
        if (Serial.available() > 0) {
          parseChar = true;
          break;
        }
      }

      if (!parseChar) { //timed out
        printDiagnosis();
      }
      else {
        resolution = Serial.parseInt();
        resolution = constrain(resolution, 1, 8);
        printDiagnosis();
      }
      break;

    case 's':
      parseChar = false;
      Serial.println("Input new number of steps (int): ");
      timeNow = millis();
      serialFlush;
      while (millis() - timeNow < timeout) {
        delay(2);
        if (Serial.available() > 0) {
          parseChar = true;
          break;
        }
      }

      if (!parseChar) { //timed out
        printDiagnosis();
      }
      else {
        nSteps = Serial.parseInt();
        if (nSteps <= 0) {
          nSteps = 1;
        }
        printDiagnosis();
      }
      break;

    case 'p':
      printDiagnosis();
      break;

    case 'h':
      Serial.print(helpString);
      serialFlush();
      break;

    case 'l': //PUSH EVERYTTHING
      str2Print = "toggle led";
      Serial.print(str2Print);
      digitalWrite(ledPin, !digitalRead(ledPin));
      break;

    case 'z':
      resetEDPins();
      Protocol();
      break;

    default:
      Serial.println("N/R");
      break;
  }
}


void printDiagnosis() {
  str2Print = "Waiting for input.... Current settings are :  ";
  str2Print += constructStringSettings();
  Serial.print(str2Print);
}

String constructStringSettings() {
  String tempstr = "resolution = " +
                   '\t' +  String(resolution) +
                   '\t' + " nSteps = " + String(nSteps) + '\n';
  return String(tempstr);
}

void serialFlush() {
  while (Serial.available() > 0) {
    char t = Serial.read();
  }
}

void doTheStep() {
  resetEDPins();
  digitalWrite(EN, 0);
  delay(10);
  unsigned int nS = nSteps;
  bool dd = thisDir;
  unsigned int res = resolution;
  Serial.print("STEPPING....");
  switch (res) // define resolution
  {
    case 1: //1 microstep
      digitalWrite(MS1, 0);
      digitalWrite(MS2, 0);
      digitalWrite(MS3, 0);

      break;
    case 2: //1/2 microstep
      digitalWrite(MS1, 1);
      digitalWrite(MS2, 0);
      digitalWrite(MS3, 0);

      break;
    case 3: //1/4 microstep
      digitalWrite(MS1, 0);
      digitalWrite(MS2, 1);
      digitalWrite(MS3, 0);

      break;
    case 4: //1/8 microstep
      digitalWrite(MS1, 1);
      digitalWrite(MS2, 1);
      digitalWrite(MS3, 0);
      break;

    case 5:
      digitalWrite(MS1, 0);
      digitalWrite(MS2, 0);
      digitalWrite(MS3, 1);

      break;
    case 6:
      digitalWrite(MS1, 1);
      digitalWrite(MS2, 0);
      digitalWrite(MS3, 1);

      break;
    case 7:
      digitalWrite(MS1, 0);
      digitalWrite(MS2, 1);
      digitalWrite(MS3, 1);

      break;
    case 8: //1/16 microstep
      digitalWrite(MS1, 1);
      digitalWrite(MS2, 1);
      digitalWrite(MS3, 1);
      break;
    default:
      resolution = 1; //1 microstep
      digitalWrite(MS1, 0);
      digitalWrite(MS2, 0);
      digitalWrite(MS3, 0);

      break;
  }
  digitalWrite(dir, dd); // define direction

  for (int x = 0; x < nS; x++) //Loop the stepping enough times for motion to be visible
  {
    /*if (dd & digitalRead(EOT_1)) {
      Serial.println("EOT_1");
      break;
    }
    if (!dd & digitalRead(EOT_2)) {
      Serial.println("EOT_2");
      break;
    }*/
    digitalWrite(stp, 1); //Trigger one step
    //delay(1);
    delayMicroseconds(ipi);
    digitalWrite(stp, 0); //Pull step pin low so it can be triggered again
    delayMicroseconds(ipi);

    // delay(1);
  }
  Serial.print("Done!\n");
  delay(1);
  resetEDPins();

}

void HomeFunction() {
  resetEDPins();
  digitalWrite(MS1, 0);
  digitalWrite(MS2, 0);
  digitalWrite(MS3, 0);
  digitalWrite(EN, 0);
  digitalWrite(dir, thisDir); // define direction

  delay(1);
  if  (thisDir) {
    while (!digitalRead(EOT_1)) {
      digitalWrite(stp, 1); //Trigger one step
      delayMicroseconds(ipi);
      digitalWrite(stp, 0); //Pull step pin low so it can be triggered again
      delayMicroseconds(ipi);
    }
  }
  else {
    while (!digitalRead(EOT_2)) {
      digitalWrite(stp, 1); //Trigger one step
      delayMicroseconds(ipi);
      digitalWrite(stp, 0); //Pull step pin low so it can be triggered again
      delayMicroseconds(ipi);
    }

  }
  resetEDPins();
  Serial.print("...Done!\n");

}



void Protocol() {

  unsigned int nSteps = 30;
  unsigned int nSteps_c = 100;
  unsigned int nCycle = 10;
  //1/16 microstep
  digitalWrite(MS1, 1);
  digitalWrite(MS2, 1);
  digitalWrite(MS3, 1);

  //forward
  bool ddirection  = 1;
  digitalWrite(dir, ddirection); // define direction

  String Sstatus = "Protocol running: nCycles = " + '\t' + String(nCycle) + '\t' + "nSteps = " + String(nSteps) + '\n';
  Serial.print(Sstatus);

  for (int i = 0; i < nCycle; i++) {
    digitalWrite(EN, 0);
    delay(1);
    digitalWrite(ledPin, 1);

    digitalWrite(dir, 0); // define direction
    for (int x = 0; x < nSteps_c; x++) //Loop the stepping enough times for motion to be visible
    {
      digitalWrite(stp, 1); //Trigger one step
      delayMicroseconds(ipi);
      digitalWrite(stp, 0); //Pull step pin low so it can be triggered again
      delayMicroseconds(ipi); 
    }
    digitalWrite(dir, 1); // define direction
    for (int x = 0; x < nSteps_c; x++) //Loop the stepping enough times for motion to be visible
    {
      digitalWrite(stp, 1); //Trigger one step
      delayMicroseconds(ipi);
      digitalWrite(stp, 0); //Pull step pin low so it can be triggered again
      delayMicroseconds(ipi);   
    }



    for (int x = 0; x < nSteps; x++) //Loop the stepping enough times for motion to be visible
    {
      /*if (ddirection & digitalRead(EOT_1)) {
        Serial.println("EOT_1");
        break;
      }
      if (!ddirection & digitalRead(EOT_2)) {
        Serial.println("EOT_2");
        break;
      }*/
      digitalWrite(stp, 1); //Trigger one step
      //delay(1);
      delayMicroseconds(ipi);
      digitalWrite(stp, 0); //Pull step pin low so it can be triggered again
      delayMicroseconds(ipi);
      // delay(1);
    }
    digitalWrite(EN, 0);///1
    delay(200);
    digitalWrite(ledPin, 0);
    delay(random(20000) + 10000);
    
  }
  Serial.print("Done!\n");

}
