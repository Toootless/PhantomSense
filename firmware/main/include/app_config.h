#ifndef APP_CONFIG_H
#define APP_CONFIG_H

#include <stdint.h>

// ==================== Unit Configuration ====================
// Unit identifiers for multi-unit deployment
typedef enum {
    UNIT_ID_1 = 1,
    UNIT_ID_2 = 2,
    // Add more units as needed
    MAX_UNITS = 2
} unit_id_t;

// Current unit - set this per firmware build
#define CURRENT_UNIT_ID UNIT_ID_1

// ==================== WiFi Configuration ====================
typedef struct {
    const char *ssid;
    const char *password;
    uint32_t max_retry;
} wifi_config_t;

// ==================== MQTT Configuration ====================
typedef struct {
    const char *broker_uri;      // e.g., "mqtt://192.168.1.100:1883"
    const char *username;
    const char *password;
    const char *topic_prefix;    // e.g., "/phantomsense/unit1"
    uint32_t keepalive;
} mqtt_config_t;

// ==================== CSI Configuration ====================
typedef struct {
    uint32_t sampling_rate_hz;   // 250Hz typical
    uint32_t buffer_size;         // Number of CSI frames to buffer
    uint8_t enable_filter;        // Enable noise filtering
} csi_config_t;

// ==================== Unit Configuration Struct ====================
typedef struct {
    unit_id_t unit_id;
    const char *unit_name;
    wifi_config_t wifi;
    mqtt_config_t mqtt;
    csi_config_t csi;
    uint32_t display_refresh_rate_ms;
} unit_config_t;

// Function to get configuration for current unit
unit_config_t* app_config_get_current(void);

// Function to initialize configuration
void app_config_init(void);

// Logging macro
#define APP_LOG_LEVEL ESP_LOG_INFO

#endif // APP_CONFIG_H
