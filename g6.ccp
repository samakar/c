// ----- Class Timer -----

class TimerObj {
    public:
         void init(int duration)    {_duration = duration;}
         void turnOn()  { _doneTime = millis() + _duration; _off = false; }
         void turnOff() { _doneTime = 0; _off = true; }
         bool isDone()  { return (millis() >= _doneTime); }
         bool isOff()   {return _off;}
    private:
         int _duration=0; //ms
         unsigned long _doneTime;
         bool _off = true;
};

// ----- Class Http -----

class HttpObj {
    public:
        HttpObj();
        void get(String value);
        char * extractJSON(char * chars);
        void run();
    private:
        void _sendRequest();
        char * _request();
        String  _path;
        static const int _maxBuffer = 1024;
        const char * _success = "{\"result\":\"pass\"}";
        const char * _hostname ="www.hello-169940.usw1-2.nitrousbox.com"; // "zealinx.meteor.com"
        TCPClient _client;
        char _buffer[_maxBuffer];
        char _part[_maxBuffer];
        TimerObj _timer;
};

HttpObj::HttpObj(){
   _timer.init(1000);
}

void HttpObj::get(String value) {
    _path = "/api?msg=" + value; // change state into msg
    _sendRequest();
}

char * HttpObj::_request() {
  Serial.println("resolving host...");
  if (_client.connected()) {
         Serial.println("connected still!");
  }else {
      if (_client.connect(_hostname, 80)) {
        Serial.println("connected!");
      } else {
        Serial.println("\r\n\r\nConnection Failed!");
        _client.stop();
        return NULL;
      }
  }
  _client.print("GET " + _path + " HTTP/1.1\r\n" + "HOST: " + _hostname + "\r\n\r\n\r\n");


  Serial.println("\r\nReading Data......");
  _buffer[0] = '\0'; // empty buffer
  bool breakFlag = false;
  int i,k = 0;
  uint32_t lastRead = millis();
  while ((millis() - lastRead) < 1000) {
    SPARK_WLAN_Loop();
    while (_client.available()) {
      char c = _client.read();
      Serial.print(c);
      if(i++ > 100) {
        delay(100);
        i = 0;
      }
      if (c == -1) break;
  	  _buffer[k++] = c;
  	  if( (k == _maxBuffer-2) || (c=='}') ){
            // protocol: json response doesn't contain an array
        _buffer[k++] = '\0';
        breakFlag = true;
        break;
      }
      lastRead = millis();
    }
    if (breakFlag) break;
  }
  Serial.println("\r\nData Read......");
  _client.flush();
  _client.stop();
  return _buffer;
};

char * HttpObj::extractJSON(char * chars) {
    char *ptrStrf;
    char *ptrStrl;
    ptrStrf = strstr(chars, "{");    
    ptrStrl =strstr(chars,"}");
    if (ptrStrf != NULL && ptrStrl != NULL){
        // if successfull then show what is between {}
        int len = ptrStrl-ptrStrf+1;
        memcpy(_part, ptrStrf, len);
        _part[len] = 0; /* Add terminator */   
        return _part;
    }else {
        return NULL;
    }
}

void HttpObj::_sendRequest(){
    char * response = _request();
    //char * reply = extractJSON(response); not used because we don't use a json object
    Serial.println(strstr(response, _success));
    if ( strstr(response, _success) == NULL) {
        // stop client because sometimes _client.connected() is true but connection is lost.
        _client.stop();
        _timer.turnOn();
    } else {
        _timer.turnOff();
    }
};

void HttpObj::run() {
    SPARK_WLAN_Loop();
   if (!_timer.isOff()) {
    if (_timer.isDone()) {
        _sendRequest();
    }
   }
}

// ----- Base Class -----

class baseDriver {
    public:
        const int MAX_COMMAND_LIST = 10;
        virtual void init( String* objList);
        virtual String getState() =0;
        virtual String getClassID();
        int pinMap ( int origin, int xy[2] );
        int find00(String* objList);
 };
 
int baseDriver::pinMap ( int origin, int xy[2] ) {
    const int map[2][7] = { {A7, A6, A5, A4, A2, A1, A0} , {D7, D6, D5, D4, D2, D1, D0} };
    return map[ xy[0] + origin ][ xy[1] ];
 }

void baseDriver::init ( String* objList) {}

String baseDriver::getClassID () {return "0000";}

int baseDriver::find00(String* objList) {
    for (int i=1; i<MAX_COMMAND_LIST; i++){
        if ( objList[i]==getClassID() ) {
            objList[i]=="";
            return (i-1);
        }
    }
}

// ----- Class Relay -----

class RelayObj {
    public:
        void init(int, int);
        void activate();
        void deactivate();
        int state();
        uint32_t getUsage();
    protected:
        uint32_t _usage = 0;
        int _outputPin;
        int _outputState;
        TimerObj _delayTimer;
};

void RelayObj::init(int outputPin, int offDelay) {
    _outputPin = outputPin;
    pinMode(_outputPin, OUTPUT);
    digitalWrite(_outputPin,LOW);
    _outputState = LOW;
    _delayTimer.init(offDelay);
}

void RelayObj::activate() {
    digitalWrite(_outputPin,HIGH);
    _outputState = HIGH;
    _delayTimer.turnOff();
    _usage++;
}

void RelayObj::deactivate() {
    // deactivate musr be called continuosly to check its timer
    if (_delayTimer.isOff()) {
        _delayTimer.turnOn();
    } else if (_delayTimer.isDone()) {
        digitalWrite(_outputPin, LOW);
        _outputState = LOW;
        _delayTimer.turnOff();
    }
}

int RelayObj::state() {
    return _outputState;
}

uint32_t RelayObj::getUsage() {
    return _usage;
}

// ----- Class LightSensor -----

class LightSensorDriver: public baseDriver {
    public:
        void init( String* objList);
        bool humanDetected();
        String getState();
        String getClassID();
    private:
        int _pirPinXY[2] = {0,0}; //D7;
        int _ldrPinXY[2] = {0,1}; //A7;
        int _ledPinXY[2] = {-1,1}; //A6;
        int _pirPin;
        int _ldrPin;
        int _ledPin;
};

String LightSensorDriver::getClassID () {return "LS01";}

void LightSensorDriver::init( String* objList) {
    int OO = find00(objList);
    _pirPin = pinMap(OO,_pirPinXY);
    _ldrPin = pinMap(OO,_ldrPinXY);
    _ledPin = pinMap(OO,_ledPinXY);
    pinMode( _pirPin , INPUT_PULLUP);
    pinMode( _ldrPin, INPUT);
    pinMode( _ledPin, OUTPUT);
    digitalWrite( _ledPin, LOW);
}

bool LightSensorDriver::humanDetected() {
    if (digitalRead(_pirPin)==HIGH) {
        digitalWrite(_ledPin,HIGH);
        return true;
    }else {
        digitalWrite(_ledPin,LOW);
        return false;
    }
}

String LightSensorDriver::getState() {
    char state[128];
    int ldrValue = ((int)analogRead(_ldrPin) / 100) * 100;
    sprintf(state,"{\"name\":\"%s\",\"pir\":%u,\"ldr\":%u}", getClassID().c_str(), digitalRead(_pirPin), ldrValue );
    String strState(state);
    return strState;
}

// ----- Class push-button -----

class SwitchDriver: public baseDriver {
    public:
        void init(String* objList);
        bool isPushed();
        String getState();
        String getClassID();
    protected:
        int _inputPinXY[2] = {0,0}; //D7;
        int _inputPin;
};

String SwitchDriver::getClassID () {return "SW01";}

void SwitchDriver::init(String* objList) {
    int OO = find00(objList);
    _inputPin = pinMap(OO,_inputPinXY);
    pinMode(_inputPin, INPUT_PULLDOWN);
}

bool SwitchDriver::isPushed() {
    return (digitalRead(_inputPin)==HIGH);
}

String SwitchDriver::getState() {
    char state[128];
    sprintf(state,"{\"name\":\"%s\",\"btn\":%u}", getClassID().c_str(), digitalRead(_inputPin));
    String strState(state);
    return strState;
}

// ----- Class PowerWall -----

class PowerWallDriver: public baseDriver {
    public:
        void init();
        RelayObj relayShort;
        RelayObj relayPower;
        String getState();
        String getClassID();
};

String PowerWallDriver::getClassID () {return "PW01";}

void PowerWallDriver::init() {
    relayPower.init(D3, 20000);
    relayShort.init(A3, 200);
}

String PowerWallDriver::getState() {
    char state[128];
    sprintf(state,"{\"name\":\"%s\",\"relaySht\":%u,\"relayPwr\":%u,\"usage\":%u}", 
        getClassID().c_str(), relayShort.state(), relayPower.state(), relayShort.getUsage() );
    String strState(state);
    return strState;
}

// ----- Base BaseApp Class -----

class BaseApp {
  public:
    virtual void run();
    virtual int webRequest(String command);
    String getAppID();
  protected:
    const int OK = 200;
    const int NOT_FOUND = 404;
    const int MAX_COMMAND_LIST = 10;
    const String APPID_FIRST_CHAR = "A";
    const int APPID_ADDRESS = 0;
    const int APPID_LENGTH = 6;
    const int DRIVER_LIST_ADDRESS = 10;
    const int DRIVER_LIST_LENGTH = 50;
    const String UNKNOWN = "UNKNOWN";
    bool _doReset = false;
    void publish(String field, String value);
    void checkReset();
    void writeWord( int address, String word);
    String readWord( int address, int length);
    String * parse(String csvFile);
  private:
    HttpObj _http;
    String bsonDate(int now);
};

void BaseApp::run() {}

int BaseApp::webRequest(String command) {}

void BaseApp::checkReset() {
    if (_doReset){
        writeWord( APPID_ADDRESS, UNKNOWN);
        System.reset();
    }
}

void BaseApp::writeWord( int address, String word) {
    int length = word.length()+1;
    uint8_t buffer[length];
    word.getBytes(buffer, length);
    for(int i=0; i<=length; i++ ){
        EEPROM.write(address+i, buffer[i] );
    }
}


String BaseApp::readWord( int address, int length) {
    char charWord[length];
    for(int i=0; i<length; i++ ){
        charWord[i] = EEPROM.read(address+i);
    }
    String word(charWord);
    return word;
}

String BaseApp::bsonDate(int now) {
    static unsigned long lastMillis;
    static int lastNow;
    int milli = (millis()-lastMillis) - (now-lastNow)*1000;
    if (milli>1000) milli = milli % 1000;
    if (milli<0) milli=0;
    lastMillis = milli;
    lastNow = now;
    // make BSON date
    char date[22];
    if (milli>99) sprintf(date,"%u%u", now, milli);
    else if (milli>9) sprintf(date,"%u0%u", now, milli);
    else sprintf(date,"%u00%u", now, milli);
    
    String strDate(date);
    return strDate;
}

void BaseApp::publish(String key, String value) {
    // check value change
    static uint32_t serialNumber = 0;
    static String lastValue;
    
    if (value != lastValue) {
        lastValue = value;
        String eventMessage = "{\"deviceID\":\"" + Spark.deviceID() + "\",\"date\":" + bsonDate(Time.now()) 
        + ",\"msgSerialNum\":" + serialNumber + ",\"" + key + "\":" + value + "}";
        _http.get(eventMessage);
        serialNumber++;
    }
    _http.run();
}
 
String * BaseApp::parse(String csvFile) {
    //temp was used to bypass a wierd complier error
    // parse csv file into array
    //TODO: test before use. NOT TESTED FULLY
    int i = 0;
    int start = 0;
    int end = 1;
    static String list[8];
    while (end>0){
        end = csvFile.indexOf( "," , start);
        if (end==-1) {
            String temp =  csvFile.substring( start );
            list[i] = temp;
        } else {
            String temp = csvFile.substring( start , end - start);
            list[i] = temp;
        }
        start = end + 1 ;
    	i++;
    };
    return list;
} 

String BaseApp::getAppID() {
    Serial.println("getAppID in");
    String appID = readWord( APPID_ADDRESS, APPID_LENGTH); //workaround for a quirk
    Serial.println(appID);
    if ( !((appID.length()==APPID_LENGTH) && appID.startsWith( APPID_FIRST_CHAR )) ) appID=UNKNOWN;
    return appID;
}    

// ----- Class Controller -----

class GarageApp: public BaseApp {
    public:
        GarageApp();
        void run();
        int webRequest(String command);
    protected:
        const String MSG_KEY = "state";
        String getState();
        LightSensorDriver _lightSensor;
        SwitchDriver _pushButton;
        PowerWallDriver _powerWall;
};

GarageApp::GarageApp() {
    String driverList = readWord( DRIVER_LIST_ADDRESS, DRIVER_LIST_LENGTH);
    String* objList = parse(driverList);
    _lightSensor.init(objList);
    _pushButton.init(objList);
    _powerWall.init();
    // publish state to enable control btns on user UI
    publish(MSG_KEY,getState());
}

void GarageApp::run() {
    checkReset();
    if (_lightSensor.humanDetected()) {
        _powerWall.relayPower.activate();
    }else {
        _powerWall.relayPower.deactivate();
    }

    if (_pushButton.isPushed()) {
        _powerWall.relayShort.activate();
    }else {
        _powerWall.relayShort.deactivate();
    }
    publish(MSG_KEY,getState());
}

String GarageApp::getState() {
    return "[" + _lightSensor.getState() + "," + _pushButton.getState() + "," + _powerWall.getState() + "]";
}

int GarageApp::webRequest(String command) {
    Serial.println("webRequest: " + command);
    if (command=="SHORT_ON") {
        _powerWall.relayShort.activate(); 
        return OK;
    } else if (command=="SHORT_OFF") {
        _powerWall.relayShort.deactivate();
        _powerWall.relayShort.activate(); 
            return OK;
    } else if (command=="POWER_ON") {
        _powerWall.relayPower.activate(); 
        return OK;
    } else if (command=="POWER_OFF") {
        _powerWall.relayPower.deactivate();
        return OK;
    } else if (command=="reset") {
        _doReset = true;
        return OK;
    } else
        return NOT_FOUND;
}

 
// ----- Class Config -----

class Configurator : public BaseApp {
    public:
        Configurator( String appSuiteID);
        void run();
        int webRequest(String command);
    private:
        const String MSG_KEY = "config";
        String _appSuiteID;
        String _appID = UNKNOWN;
        bool _doScan=true;
        String getConfig();
        String getBlockList();
};

Configurator::Configurator( String appSuiteID) {
    _appSuiteID = appSuiteID;
}

void Configurator::run() {
    static String config;
    checkReset();
    if (_doScan) {
        String config = "" + getConfig();
        _doScan = false;
        Serial.println(config);
    }
    publish( MSG_KEY , config );
}    

int Configurator::webRequest(String command) {
    Serial.println("webRequest: " + command);
    if (command=="reset") {
        _doReset = true;
    } else if (command=="rescan") {
        _doScan = true;
    } else {
        // if device is unknown repeat or server may reprogram device
        //int reply = parse(command);
        int firstCommaIndex = command.indexOf( "," );
        _appID = "" + command.substring( 0, firstCommaIndex-1 );
        writeWord( APPID_ADDRESS, _appID);
        String driverList =  command.substring( firstCommaIndex+1 );
        writeWord( DRIVER_LIST_ADDRESS, driverList);
        _doReset = true;
   }
    return 200;
}    

String Configurator::getConfig() {
   return "{\"appSuiteID\":\"" + _appSuiteID +  "\",\"appID\":\"" + _appID + "\",\"blockList\":" + getBlockList() + "}";
}

String Configurator::getBlockList() {
    // scan devices
    // assumption: only even rows are connected to a pin which during normal operation is an analog output
    const int thresholds[] = { 0, 40, 60, 80, 100, 120, 140, 160 };     // adc counts
    const String BLOCK_ID[] = { "NONE", "sw001", "ls001", "pb001", "sw004" };
    const int thresholdLength = sizeof(thresholds) / sizeof(thresholds[0]);
    const int maxRows = 7; // start from row 0
    const int sampleNum = 10;
    String blockID[maxRows+1];

    for(int i=0;i<=maxRows;i++)  blockID[i] = BLOCK_ID[0];
    for ( int row = 0; row <= maxRows; row = row + 2 ) {
        int pin = row + 10;
        pinMode(pin, INPUT);
        int sum=0;
        for(int i=0;i<sampleNum;i++) sum += analogRead(pin);
        int adc = sum/sampleNum;
        for (int i=1; i<thresholdLength; i++) {
            if (adc<=thresholds[i]) {
               blockID[row] = BLOCK_ID[i-1]; // thresholds[i] is upper limit of i-1 device-code
               break;
            }
        }
    }
   // make device list
   // there's many-to-one relationship between HW block codes and SW objects
   String blockList = "[";
   for( int row = 0; row <= maxRows; row++ ) {
       if (row>0) blockList += ",";
       blockList = blockList + "{\"row\":" + row + ",\"blockID\":\"" + blockID[row] + "\"}";
    }
    blockList += "]";
    return blockList;
}
// ----------

BaseApp * App;

int webRequest(String command){
    return App->webRequest(command);
}

void setup() {
    Serial.begin(9600);
    while (!Serial.available()) SPARK_WLAN_Loop();
    Spark.function("webRequest", webRequest);
    String activeAppID =  App->getAppID();
    if (activeAppID=="A00001") {
        Serial.println("activeAppID==A00001");
        App = new GarageApp();
    } else if (activeAppID=="A00002") {
        Serial.println("activeAppID==A00002");
        App = new GarageApp();
    } else {
        App = new Configurator("B00001");
    }
    Serial.println("setup end");
}

void loop() {
    App->run();
}
