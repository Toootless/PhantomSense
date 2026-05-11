#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_log.h"
#include "cjson/cJSON.h"
#include "app_config.h"
#include "wifi_setup.h"
#include "mqtt_setup.h"
#include "csi_driver.h"
#include "signal_processor.h"

static const char *TAG = "MAIN";

// Task handles
static TaskHandle_t csi_task_handle = NULL;
static TaskHandle_t signal_process_task_handle = NULL;

// FreeRTOS event group for synchronization
static EventGroupHandle_t status_event_group = NULL;
#define WIFI_CONNECTED_BIT BIT0
#define MQTT_CONNECTED_BIT BIT1

/**
 * System status monitoring task
 */
static void status_monitor_task(void *pvParameter) {
    unit_config_t *config = app_config_get_current();
    
    ESP_LOGI(TAG, "=== PhantomSense Unit %d Starting ===", config->unit_id);
    ESP_LOGI(TAG, "Unit Name: %s", config->unit_name);
    ESP_LOGI(TAG, "MQTT Topic: %s", config->mqtt.topic_prefix);
    
    while (1) {
        bool wifi_ok = wifi_is_connected();
        bool mqtt_ok = mqtt_is_connected();
        
        if (wifi_ok && mqtt_ok) {
            xEventGroupSetBits(status_event_group, WIFI_CONNECTED_BIT | MQTT_CONNECTED_BIT);
            ESP_LOGI(TAG, "System Status: ✓ WiFi Connected | ✓ MQTT Connected");
        } else {
            xEventGroupClearBits(status_event_group, WIFI_CONNECTED_BIT | MQTT_CONNECTED_BIT);
            ESP_LOGW(TAG, "System Status: %s WiFi | %s MQTT",
                    wifi_ok ? "✓" : "✗", mqtt_ok ? "✓" : "✗");
        }
        
        vTaskDelay(pdMS_TO_TICKS(2000));  // Update every 2 seconds
    }
}

/**
 * CSI data acquisition task (placeholder for now)
 */
static void csi_acquisition_task(void *pvParameter) {
    ESP_LOGI(TAG, "CSI Acquisition task started");
    
    // Wait for WiFi connection
    xEventGroupWaitBits(status_event_group, WIFI_CONNECTED_BIT,
                       pdFALSE, pdTRUE, portMAX_DELAY);
    
    ESP_LOGI(TAG, "WiFi connected, initializing CSI driver");
    
    // Initialize CSI driver
    csi_driver_config_t csi_config = {
        .sampling_rate_hz = 250,
        .buffer_size = 256,
        .apply_filtering = 1,
        .rx_only_mode = 1,
    };
    
    if (csi_driver_init(&csi_config) != ESP_OK) {
        ESP_LOGE(TAG, "Failed to initialize CSI driver");
        vTaskDelete(NULL);
        return;
    }
    
    if (csi_driver_start() != ESP_OK) {
        ESP_LOGE(TAG, "Failed to start CSI acquisition");
        csi_driver_deinit();
        vTaskDelete(NULL);
        return;
    }
    
    ESP_LOGI(TAG, "CSI acquisition started");
    
    while (1) {
        // Get buffered CSI frames (if any)
        uint32_t buffer_count = csi_driver_get_buffer_count();
        if (buffer_count > 0) {
            ESP_LOGD(TAG, "CSI frames buffered: %ld", buffer_count);
        }
        
        vTaskDelay(pdMS_TO_TICKS(1000));
    }
}

/**
 * Signal processing and inference task (placeholder for now)
 */
static void signal_processing_task(void *pvParameter) {
    ESP_LOGI(TAG, "Signal processing task started");
    
    // Initialize signal processor
    signal_processor_config_t proc_config = {
        .buffer_size = 256,
        .apply_median_filter = 1,
        .apply_phase_calibration = 1,
        .noise_threshold = -80.0f,
    };
    
    if (signal_processor_init(&proc_config) != ESP_OK) {
        ESP_LOGE(TAG, "Failed to initialize signal processor");
        vTaskDelete(NULL);
        return;
    }
    
    ESP_LOGI(TAG, "Signal processor initialized");
    
    uint32_t frames_processed = 0;
    
    while (1) {
        // Wait for system to be fully initialized
        xEventGroupWaitBits(status_event_group, WIFI_CONNECTED_BIT | MQTT_CONNECTED_BIT,
                           pdFALSE, pdTRUE, pdMS_TO_TICKS(100));
        
        // TODO: Process CSI frames and publish results
        // - Get CSI frame from driver
        // - Extract features using signal processor
        // - Classify activity using TinyML model
        // - Publish results via MQTT
        
        signal_processor_get_stats(&frames_processed);
        if (frames_processed % 100 == 0) {
            ESP_LOGI(TAG, "Processed %ld frames", frames_processed);
        }
        
        vTaskDelay(pdMS_TO_TICKS(250));
    }
}

/**
 * Application entry point
 */
void app_main(void) {
    // Initialize configuration
    app_config_init();
    
    // Create event group for status synchronization
    status_event_group = xEventGroupCreate();
    if (!status_event_group) {
        ESP_LOGE(TAG, "Failed to create event group");
        return;
    }
    
    // Get current unit configuration
    unit_config_t *config = app_config_get_current();
    
    // Initialize WiFi
    ESP_LOGI(TAG, "Initializing WiFi...");
    if (wifi_setup_init(&config->wifi) != ESP_OK) {
        ESP_LOGE(TAG, "WiFi initialization failed");
        return;
    }
    
    // Wait for WiFi connection before starting MQTT
    xEventGroupWaitBits(status_event_group, WIFI_CONNECTED_BIT,
                       pdFALSE, pdTRUE, portMAX_DELAY);
    
    // Initialize MQTT
    ESP_LOGI(TAG, "Initializing MQTT...");
    if (mqtt_setup_init(&config->mqtt) != ESP_OK) {
        ESP_LOGE(TAG, "MQTT initialization failed");
        return;
    }
    
    // Wait for MQTT connection
    xEventGroupWaitBits(status_event_group, MQTT_CONNECTED_BIT,
                       pdFALSE, pdTRUE, 10000 / portTICK_PERIOD_MS);
    
    // Create task for system status monitoring
    xTaskCreate(status_monitor_task, "status_monitor",
               4096, NULL, tskIDLE_PRIORITY + 1, NULL);
    
    // Create task for CSI data acquisition
    xTaskCreate(csi_acquisition_task, "csi_acquisition",
               8192, NULL, tskIDLE_PRIORITY + 2, &csi_task_handle);
    
    // Create task for signal processing
    xTaskCreate(signal_processing_task, "signal_processing",
               8192, NULL, tskIDLE_PRIORITY + 2, &signal_process_task_handle);
    
    ESP_LOGI(TAG, "All tasks created successfully");
}
