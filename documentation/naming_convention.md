# Signal Naming Convention

This section defines the mandatory signal naming rules for the PocketBeagle 2 Ethernet Cap project. The goal is to eliminate ambiguity, make signal direction obvious, and keep schematics readable and review friendly.

## General Principles

- Signal names must communicate electrical reality, not assumptions
- Direction must be explicit only where it is unambiguous
- Protocol behavior takes precedence over stylistic consistency
- Readability is preferred over extreme compactness



## 1. Point to Point Signals

For single driver, single receiver connections, use the following format:

`<signal-name>_<source-ic>_to_<sink-ic>`


### Examples

```
UART_TX_CPU_to_DEBUG
RMII_TXD0_SWITCH_to_PHY
CLK_25M_OSC_to_PHY
RESET_SUPERVISOR_to_SWITCH
```


This format must be used whenever the electrical direction is fixed and known.



## 2. TX / RX Communication Links

Do not rely on TX or RX alone to indicate direction. The source and sink must be encoded in the name.

### Examples

```
UART_TX_CPU_to_DEBUG
UART_RX_DEBUG_to_CPU
SPI_MOSI_CPU_to_FLASH
SPI_MISO_FLASH_to_CPU
```


This removes all ambiguity during schematic review and debugging.



## 3. Shared and Bidirectional Buses

For buses with bidirectional or multi driver signals, direction must not be encoded in the net name. Instead, list all participating devices.

### Examples

```
I2C_SCL_CPU_EEPROM
I2C_SDA_CPU_EEPROM
MDIO_MDIO_SWITCH_PHY
MDIO_MDC_SWITCH_PHY
```


Direction is defined by the protocol and must not be implied incorrectly by the net name.



## 4. Broadcast and Multi Sink Signals

For signals that drive multiple devices, avoid enumerating all sinks unless required for clarity.

### Preferred approaches

- Functional domain naming
- Logical grouping of recipients

### Examples

```
RESET_AVB_DOMAIN
RESET_PHYS
SYNC_AUDIO_DOMAIN
```


If a signal is duplicated intentionally, separate nets may still use the point to point scheme.



## 5. Clock Signals

Clock sources must always be explicitly named.

### Examples

```
CLK_25M_OSC_to_PHY
CLK_125M_SWITCH_to_PHY
CLK_24M_OSC_to_CPU
```


Clock direction must never be ambiguous.



## Summary Rules

1. Use `<signal>_<source>_to_<sink>` for point to point signals
2. Do not encode direction for bidirectional or shared buses
3. Name broadcast signals by function or domain
4. Net names must always reflect electrical reality

Consistency with these rules is mandatory across all schematics in the project.
