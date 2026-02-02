# CLAUDE.md - AI Assistant Guide for IoT Firmware Codebase

## Project Overview

This repository contains firmware code for **Particle/Spark microcontrollers** implementing a smart garage and home automation system. The project features sensor integration, relay control, HTTP cloud communication, and a state machine architecture for device management.

## Codebase Structure

```
/home/user/c/
├── fw              # Main firmware with state machine architecture (Bootloader + Program SM)
├── g6.ccp          # Application-layer firmware (GarageApp, Configurator)
├── garage          # Simplified controller firmware (ControllerObj)
└── README.md       # Project readme (minimal)
```

### File Descriptions

| File | Purpose | Key Classes |
|------|---------|-------------|
| `fw` | Core firmware with bootloader and program state machines | `Timer`, `HttpObj`, `BlockDriver`, `StateMachine`, `BootloaderSM`, `ProgramSM` |
| `g6.ccp` | Application firmware with garage app and device configuration | `TimerObj`, `HttpObj`, `RelayObj`, `LightSensorDriver`, `SwitchDriver`, `PowerWallDriver`, `GarageApp`, `Configurator` |
| `garage` | Simplified controller implementation | `TimerObj`, `HttpObj`, `LightSensorObj`, `PushButtonObj`, `RelayObj`, `PowerWallObj`, `ControllerObj` |

## Architecture

### State Machine Design (fw)

The firmware uses a two-phase state machine approach:

1. **BootloaderSM** - Handles device initialization:
   - Checks hardware configuration against saved config
   - Validates firmware versions across connected blocks
   - Manages program loading from EEPROM or cloud

2. **ProgramSM** - Executes the loaded program:
   - Parses and runs state transition tables
   - Manages block drivers for hardware interaction
   - Publishes status to cloud

### Application Layer (g6.ccp)

- **BaseApp** - Abstract base class with HTTP publishing, EEPROM read/write, and reset handling
- **GarageApp** - Main application controlling light sensors, switches, and power relays
- **Configurator** - Device configuration and block scanning utility

### Hardware Abstraction

Block drivers abstract hardware communication:
- `BlockDriver` - Base driver class
- `BlockDriverHW` - Hardware-specific implementation
- `PhotonDriver` - Photon microcontroller driver
- `BlockDriverBook` - Factory for driver instantiation

## Key Conventions

### Code Style

- **Class naming**: PascalCase (e.g., `HttpObj`, `BlockDriver`)
- **Method naming**: camelCase (e.g., `getState()`, `humanDetected()`)
- **Private members**: Prefixed with underscore (e.g., `_duration`, `_client`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_BUFFER`, `CONFIG_ADDRESS`)

### Common Patterns

1. **Timer Pattern**: Non-blocking delays using `millis()` comparison
   ```cpp
   bool isDone() { return (millis() >= _doneTime); }
   ```

2. **State Publishing**: JSON-formatted messages sent via HTTP
   ```cpp
   "{\"deviceID\":\"" + deviceID + "\",\"date\":" + bsonDate + ",\"content\":" + content + "}"
   ```

3. **EEPROM Storage**: Configuration and program data persisted to EEPROM
   - Config: Address 0, Length 500
   - Program: Address 600, Length 1400

### Hardware Pin Mapping

The code uses a pin mapping system for flexible hardware configuration:
```cpp
const int map[2][7] = { {A7, A6, A5, A4, A2, A1, A0}, {D7, D6, D5, D4, D2, D1, D0} };
```

## Development Guidelines

### Building and Deploying

This is Particle/Spark firmware. To build and flash:

1. Use Particle CLI or Particle Web IDE
2. Target device: Particle Photon/Spark Core
3. Flash via USB or OTA (Over-The-Air)

### HTTP Communication

- Default endpoint: `demo4462435.mockable.io` (fw) or `www.hello-169940.usw1-2.nitrousbox.com` (g6.ccp/garage)
- Port: 80 (HTTP)
- API path format: `/api?msg=<json_payload>`

### Serial Debugging

All files use serial output for debugging:
```cpp
Serial.begin(9600);  // or 115200 in garage
Serial.println("debug message");
```

### Cloud Functions

Particle cloud functions are exposed for remote control:
- `webReq` / `webRequest` - Handle cloud commands
- `pinControl` - Direct relay control (garage)

## Important Notes for AI Assistants

1. **Platform-Specific**: This code runs on Particle IoT devices, not standard Arduino or desktop environments

2. **Dependencies**: Uses Particle-specific APIs:
   - `Particle.process()` / `SPARK_WLAN_Loop()`
   - `Particle.function()` / `Spark.function()`
   - `Particle.deviceID()` / `Spark.deviceID()`
   - `TCPClient` for HTTP
   - `EEPROM` for persistence

3. **Non-blocking Design**: All code must be non-blocking to allow the main loop and Particle cloud to run continuously

4. **Memory Constraints**: Embedded system with limited RAM - buffer sizes are constrained (typically 1024 bytes max)

5. **State Machine Flow**:
   ```
   setup() -> BootloaderSM.run() [until program loaded] -> ProgramSM.run() [main loop]
   ```

## Testing

- Use Particle serial monitor for debugging output
- Test cloud functions via Particle Console or CLI:
  ```bash
  particle call <device_id> webReq "command"
  ```

## File Extensions

- `.ccp` files are C++ source files (note: unconventional extension, typically `.cpp`)
- `fw` and `garage` have no extension but contain C++ code
