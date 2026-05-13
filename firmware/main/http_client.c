#include "http_client.h"
#include "esp_log.h"
#include "esp_http_client.h"
#include "esp_timer.h"
#include <string.h>
#include <stddef.h>

static const char *TAG = "HTTP_CLIENT";

// Global HTTP client and state
static esp_http_client_handle_t http_client = NULL;
static bool http_ready = false;
static const http_config_t *current_config = NULL;

/**
 * HTTP event handler for esp_http_client
 */
static esp_err_t http_event_handler(esp_http_client_event_t *evt) {
    switch (evt->event_id) {
        case HTTP_EVENT_ERROR:
            ESP_LOGE(TAG, "HTTP_EVENT_ERROR");
            break;
            
        case HTTP_EVENT_ON_CONNECTED:
            ESP_LOGD(TAG, "HTTP_EVENT_ON_CONNECTED");
            break;
            
        case HTTP_EVENT_HEADER_SENT:
            ESP_LOGD(TAG, "HTTP_EVENT_HEADER_SENT");
            break;
            
        case HTTP_EVENT_ON_HEADER:
            ESP_LOGD(TAG, "HTTP_EVENT_ON_HEADER");
            break;
            
        case HTTP_EVENT_ON_DATA:
            ESP_LOGD(TAG, "HTTP_EVENT_ON_DATA, len=%d", evt->data_len);
            break;
            
        case HTTP_EVENT_ON_FINISH:
            ESP_LOGD(TAG, "HTTP_EVENT_ON_FINISH");
            break;
            
        case HTTP_EVENT_DISCONNECTED:
            ESP_LOGD(TAG, "HTTP_EVENT_DISCONNECTED");
            break;
            
        case HTTP_EVENT_REDIRECT:
            ESP_LOGD(TAG, "HTTP_EVENT_REDIRECT");
            break;
    }
    return ESP_OK;
}

/**
 * Initialize HTTP client
 */
esp_err_t http_client_init(const http_config_t *config) {
    if (!config || !config->hub_url) {
        ESP_LOGE(TAG, "Invalid config");
        return ESP_ERR_INVALID_ARG;
    }
    
    current_config = config;
    
    ESP_LOGI(TAG, "Initializing HTTP client");
    ESP_LOGI(TAG, "  Hub URL: %s", config->hub_url);
    ESP_LOGI(TAG, "  Update endpoint: %s", config->update_endpoint);
    
    // Build full URL: hub_url + endpoint
    char full_url[512];
    snprintf(full_url, sizeof(full_url), "%s%s", config->hub_url, config->update_endpoint);
    
    esp_http_client_config_t http_config = {
        .url = full_url,
        .event_handler = http_event_handler,
        .timeout_ms = 5000,
        .method = HTTP_METHOD_POST,
    };
    
    http_client = esp_http_client_init(&http_config);
    if (!http_client) {
        ESP_LOGE(TAG, "Failed to initialize HTTP client");
        return ESP_FAIL;
    }
    
    http_ready = true;
    ESP_LOGI(TAG, "HTTP client initialized and ready");
    return ESP_OK;
}

/**
 * Publish device status/data via HTTP POST (simplified JSON)
 */
esp_err_t http_publish_device_update(uint32_t unit_id, const char *unit_name, 
                                     int rssi, const char *ip_address,
                                     float csi_amplitude, float csi_noise_floor) {
    if (!http_client || !http_ready) {
        ESP_LOGW(TAG, "HTTP client not ready");
        return ESP_FAIL;
    }
    
    // Build JSON payload
    static char json_buffer[512];
    uint64_t timestamp_ms = esp_timer_get_time() / 1000;
    snprintf(json_buffer, sizeof(json_buffer),
             "{\"unit_id\":%lu,\"unit_name\":\"%s\",\"rssi\":%d,\"ip_address\":\"%s\","
             "\"csi_amplitude\":%.2f,\"csi_noise_floor\":%.2f,\"timestamp_ms\":%llu}",
             (unsigned long)unit_id, unit_name, rssi, ip_address ? ip_address : "N/A",
             csi_amplitude, csi_noise_floor, timestamp_ms);
    
    return http_publish_json(json_buffer);
}

/**
 * Publish JSON data via HTTP POST
 */
esp_err_t http_publish_json(const char *json_data) {
    if (!http_client || !http_ready) {
        ESP_LOGW(TAG, "HTTP client not ready");
        return ESP_FAIL;
    }
    
    if (!json_data) {
        ESP_LOGE(TAG, "NULL JSON data");
        return ESP_ERR_INVALID_ARG;
    }
    
    // Set the URL
    char full_url[512];
    snprintf(full_url, sizeof(full_url), "%s%s", current_config->hub_url, current_config->update_endpoint);
    esp_http_client_set_url(http_client, full_url);
    
    // Set method and headers
    esp_http_client_set_method(http_client, HTTP_METHOD_POST);
    esp_http_client_set_header(http_client, "Content-Type", "application/json");
    
    // Set post data
    esp_http_client_set_post_field(http_client, json_data, strlen(json_data));
    
    // Perform the request
    esp_err_t err = esp_http_client_perform(http_client);
    
    if (err == ESP_OK) {
        int status_code = esp_http_client_get_status_code(http_client);
        ESP_LOGI(TAG, "HTTP POST successful (status=%d, len=%zu)", status_code, strlen(json_data));
        esp_http_client_close(http_client);
        return ESP_OK;
    } else {
        ESP_LOGE(TAG, "HTTP POST failed: %s", esp_err_to_name(err));
        esp_http_client_close(http_client);
        return err;
    }
}

/**
 * Check if HTTP client is ready
 */
bool http_is_ready(void) {
    return http_ready && http_client != NULL;
}

/**
 * Get HTTP client handle
 */
esp_http_client_handle_t http_get_handle(void) {
    return http_client;
}

/**
 * Cleanup HTTP client
 */
esp_err_t http_client_deinit(void) {
    if (http_client) {
        esp_http_client_cleanup(http_client);
        http_client = NULL;
    }
    http_ready = false;
    ESP_LOGI(TAG, "HTTP client cleaned up");
    return ESP_OK;
}
