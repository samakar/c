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

// ----- Class LogisticsItem -----
class LogisticsItem {
    public:
        String itemID;
        String itemName;
        int quantity;
        unsigned long entryTime;
        unsigned long exitTime;
        String location;
        bool inStock;

        LogisticsItem() {
            itemID = "";
            itemName = "";
            quantity = 0;
            entryTime = 0;
            exitTime = 0;
            location = "";
            inStock = false;
        }

        String toJSON() {
            char buffer[256];
            sprintf(buffer, "{\"id\":\"%s\",\"name\":\"%s\",\"qty\":%d,\"entry\":%lu,\"exit\":%lu,\"loc\":\"%s\",\"status\":%d}",
                    itemID.c_str(), itemName.c_str(), quantity, entryTime, exitTime, location.c_str(), inStock);
            return String(buffer);
        }
};

// ----- Class LogisticsModel -----
class LogisticsModel {
    public:
        LogisticsModel();
        void init();

        // Core logistics functions
        bool addItem(String itemID, String itemName, int quantity, String location);
        bool removeItem(String itemID, int quantity);
        bool updateLocation(String itemID, String newLocation);
        int getStockLevel(String itemID);
        String getItemStatus(String itemID);
        String getAllInventory();

        // Sensor integration
        void checkEntry();
        void checkExit();
        void scanBarcode(String barcode);

        // Reporting
        String generateReport();
        int getTotalItems();

    private:
        static const int MAX_ITEMS = 50;
        LogisticsItem inventory[MAX_ITEMS];
        int itemCount;

        int findItemIndex(String itemID);
        String bsonDate(unsigned long timestamp);

        // Sensor pins
        int entrySensorPin;
        int exitSensorPin;
        int ledIndicatorPin;
};

LogisticsModel::LogisticsModel() {
    itemCount = 0;
    entrySensorPin = D1;
    exitSensorPin = D2;
    ledIndicatorPin = D7;
}

void LogisticsModel::init() {
    pinMode(entrySensorPin, INPUT_PULLUP);
    pinMode(exitSensorPin, INPUT_PULLUP);
    pinMode(ledIndicatorPin, OUTPUT);
    digitalWrite(ledIndicatorPin, LOW);

    // Initialize inventory array
    for(int i = 0; i < MAX_ITEMS; i++) {
        inventory[i] = LogisticsItem();
    }

    Serial.println("LogisticsModel >>> Initialized");
}

int LogisticsModel::findItemIndex(String itemID) {
    for(int i = 0; i < itemCount; i++) {
        if(inventory[i].itemID == itemID) {
            return i;
        }
    }
    return -1;
}

bool LogisticsModel::addItem(String itemID, String itemName, int quantity, String location) {
    int index = findItemIndex(itemID);

    if(index >= 0) {
        // Item exists, update quantity
        inventory[index].quantity += quantity;
        inventory[index].inStock = (inventory[index].quantity > 0);
        Serial.println("LogisticsModel >>> Updated item: " + itemID);
        return true;
    } else {
        // Add new item
        if(itemCount >= MAX_ITEMS) {
            Serial.println("LogisticsModel >>> ERROR: Inventory full!");
            return false;
        }

        inventory[itemCount].itemID = itemID;
        inventory[itemCount].itemName = itemName;
        inventory[itemCount].quantity = quantity;
        inventory[itemCount].location = location;
        inventory[itemCount].entryTime = millis();
        inventory[itemCount].exitTime = 0;
        inventory[itemCount].inStock = true;

        itemCount++;
        digitalWrite(ledIndicatorPin, HIGH);
        delay(100);
        digitalWrite(ledIndicatorPin, LOW);

        Serial.println("LogisticsModel >>> Added new item: " + itemID);
        return true;
    }
}

bool LogisticsModel::removeItem(String itemID, int quantity) {
    int index = findItemIndex(itemID);

    if(index < 0) {
        Serial.println("LogisticsModel >>> ERROR: Item not found: " + itemID);
        return false;
    }

    if(inventory[index].quantity < quantity) {
        Serial.println("LogisticsModel >>> ERROR: Insufficient quantity!");
        return false;
    }

    inventory[index].quantity -= quantity;
    inventory[index].exitTime = millis();

    if(inventory[index].quantity == 0) {
        inventory[index].inStock = false;
    }

    Serial.println("LogisticsModel >>> Removed " + String(quantity) + " of item: " + itemID);
    return true;
}

bool LogisticsModel::updateLocation(String itemID, String newLocation) {
    int index = findItemIndex(itemID);

    if(index < 0) {
        Serial.println("LogisticsModel >>> ERROR: Item not found: " + itemID);
        return false;
    }

    inventory[index].location = newLocation;
    Serial.println("LogisticsModel >>> Updated location for " + itemID + " to " + newLocation);
    return true;
}

int LogisticsModel::getStockLevel(String itemID) {
    int index = findItemIndex(itemID);

    if(index < 0) {
        return -1;
    }

    return inventory[index].quantity;
}

String LogisticsModel::getItemStatus(String itemID) {
    int index = findItemIndex(itemID);

    if(index < 0) {
        return "{\"error\":\"Item not found\"}";
    }

    return inventory[index].toJSON();
}

String LogisticsModel::getAllInventory() {
    String result = "[";

    for(int i = 0; i < itemCount; i++) {
        if(i > 0) result += ",";
        result += inventory[i].toJSON();
    }

    result += "]";
    return result;
}

void LogisticsModel::checkEntry() {
    if(digitalRead(entrySensorPin) == LOW) {
        digitalWrite(ledIndicatorPin, HIGH);
        Serial.println("LogisticsModel >>> Entry detected!");
        delay(200);
        digitalWrite(ledIndicatorPin, LOW);
    }
}

void LogisticsModel::checkExit() {
    if(digitalRead(exitSensorPin) == LOW) {
        digitalWrite(ledIndicatorPin, HIGH);
        Serial.println("LogisticsModel >>> Exit detected!");
        delay(200);
        digitalWrite(ledIndicatorPin, LOW);
    }
}

void LogisticsModel::scanBarcode(String barcode) {
    Serial.println("LogisticsModel >>> Barcode scanned: " + barcode);

    // Parse barcode format: "ADD:ID:NAME:QTY:LOC" or "REM:ID:QTY"
    int firstColon = barcode.indexOf(":");
    String operation = barcode.substring(0, firstColon);

    if(operation == "ADD") {
        String remaining = barcode.substring(firstColon + 1);
        int c1 = remaining.indexOf(":");
        String id = remaining.substring(0, c1);

        remaining = remaining.substring(c1 + 1);
        int c2 = remaining.indexOf(":");
        String name = remaining.substring(0, c2);

        remaining = remaining.substring(c2 + 1);
        int c3 = remaining.indexOf(":");
        int qty = remaining.substring(0, c3).toInt();

        String loc = remaining.substring(c3 + 1);

        addItem(id, name, qty, loc);

    } else if(operation == "REM") {
        String remaining = barcode.substring(firstColon + 1);
        int c1 = remaining.indexOf(":");
        String id = remaining.substring(0, c1);
        int qty = remaining.substring(c1 + 1).toInt();

        removeItem(id, qty);
    }
}

String LogisticsModel::generateReport() {
    char buffer[512];
    int totalQty = 0;
    int inStockCount = 0;

    for(int i = 0; i < itemCount; i++) {
        totalQty += inventory[i].quantity;
        if(inventory[i].inStock) {
            inStockCount++;
        }
    }

    sprintf(buffer, "{\"totalItems\":%d,\"inStock\":%d,\"totalQuantity\":%d,\"timestamp\":%lu}",
            itemCount, inStockCount, totalQty, millis());

    return String(buffer);
}

int LogisticsModel::getTotalItems() {
    return itemCount;
}

String LogisticsModel::bsonDate(unsigned long timestamp) {
    char date[22];
    sprintf(date, "%lu", timestamp);
    return String(date);
}

// ----- Main Application Integration -----

LogisticsModel logistics;

// Cloud function handlers
int handleLogisticsCommand(String command) {
    Serial.println("LogisticsModel >>> Command: " + command);

    if(command.startsWith("ADD:")) {
        logistics.scanBarcode(command);
        return 200;
    } else if(command.startsWith("REM:")) {
        logistics.scanBarcode(command);
        return 200;
    } else if(command.startsWith("STATUS:")) {
        String itemID = command.substring(7);
        String status = logistics.getItemStatus(itemID);
        Serial.println(status);
        return 200;
    } else if(command == "REPORT") {
        String report = logistics.generateReport();
        Serial.println(report);
        return 200;
    } else if(command == "INVENTORY") {
        String inv = logistics.getAllInventory();
        Serial.println(inv);
        return 200;
    }

    return 404;
}

void setup() {
    Serial.begin(9600);
    while (!Serial.available()) Particle.process();

    logistics.init();

    Particle.function("logistics", handleLogisticsCommand);

    Serial.println("Logistics System Ready");
}

void loop() {
    logistics.checkEntry();
    logistics.checkExit();

    delay(100);
}
