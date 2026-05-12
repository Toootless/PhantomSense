#include "app_config.h"
#include "esp_log.h"
#include <stddef.h>

static const char *TAG = "APP_CONFIG";

// ==================== Unit 1 Configuration ====================
static unit_config_t unit_1_config = {
    .unit_id = UNIT_ID_1,
    .unit_name = "PhantomSense-Unit-1",
    .wifi = {
        .ssid = "DrWho",
        .password = "Mollymay2212",
        .max_retry = 5,
    },
    .http = {
        .hub_url = "http://10.0.0.84:5000",
        .update_endpoint = "/update",
    },
    .csi = {
        .sampling_rate_hz = 250,
        .buffer_size = 2048,
        .enable_filter = 1,
    },
    .display_refresh_rate_ms = 100,
};

// ==================== Unit 2 Configuration ====================
static unit_config_t unit_2_config = {
    .unit_id = UNIT_ID_2,
    .unit_name = "PhantomSense-Unit-2",
    .wifi = {
        .ssid = "DrWho",
        .password = "Mollymay2212",
        .max_retry = 5,
    },
    .http = {
        .hub_url = "http://10.0.0.84:5000",
        .update_endpoint = "/update",
    },
    .csi = {
        .sampling_rate_hz = 250,
        .buffer_size = 2048,
        .enable_filter = 1,
    },
    .display_refresh_rate_ms = 100,
};

// ==================== Configuration Management ====================
static unit_config_t *current_config = NULL;

unit_config_t* app_config_get_current(void) {
    return current_config;
}

void app_config_init(void) {
    // Select configuration based on CURRENT_UNIT_ID
    switch (CURRENT_UNIT_ID) {
        case UNIT_ID_1:
            current_config = &unit_1_config;
            ESP_LOGI(TAG, "Using Unit 1 configuration");
            break;
        case UNIT_ID_2:
            current_config = &unit_2_config;
            ESP_LOGI(TAG, "Using Unit 2 configuration");
            break;
        default:
            ESP_LOGE(TAG, "Unknown unit ID: %d", CURRENT_UNIT_ID);
            current_config = &unit_1_config;  // Fallback
            break;
    }
    
    ESP_LOGI(TAG, "Unit Name: %s", current_config->unit_name);
    ESP_LOGI(TAG, "Hub URL: %s", current_config->http.hub_url);
    ESP_LOGI(TAG, "CSI Sampling Rate: %ld Hz", current_config->csi.sampling_rate_hz);
}
