#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/event_groups.h"
#include "esp_system.h"
#include "esp_log.h"
#include "app_config.h"
#include "wifi_setup.h"
#include "http_client.h"
#include "display_driver.h"
#include "csi_driver.h"
#include "signal_processor.h"

static const char *TAG = "MAIN";

// Task handles
static TaskHandle_t csi_task_handle = NULL;
static TaskHandle_t signal_process_task_handle = NULL;

// Shared CSI metrics updated by csi_acquisition_task, read by hub_update_task
static volatile float g_csi_amplitude = -50.0f;
static volatile float g_csi_noise_floor = -80.0f;
static volatile uint32_t g_csi_frame_count = 0;

// FreeRTOS event group for synchronization
static EventGroupHandle_t status_event_group = NULL;
#define WIFI_CONNECTED_BIT BIT0
#define HUB_CONNECTED_BIT BIT1

/**
 * System status monitoring task
 */
static void status_monitor_task(void *pvParameter) {
    unit_config_t *config = app_config_get_current();
    
    ESP_LOGI(TAG, "=== PhantomSense Unit %d Starting ===", config->unit_id);
    ESP_LOGI(TAG, "Unit Name: %s", config->unit_name);
    ESP_LOGI(TAG, "Hub URL: %s", config->http.hub_url);
    
    while (1) {
        bool wifi_ok = wifi_is_connected();
        bool hub_ok = http_is_ready();
        
        if (wifi_ok && hub_ok) {
            xEventGroupSetBits(status_event_group, WIFI_CONNECTED_BIT | HUB_CONNECTED_BIT);
            display_set_status(DISPLAY_STATUS_CONNECTED);  // Show green
            ESP_LOGI(TAG, "System Status: ✓ WiFi Connected | ✓ Hub Ready");
        } else if (wifi_ok && !hub_ok) {
            display_set_status(DISPLAY_STATUS_CONNECTING);  // Show connecting
            xEventGroupSetBits(status_event_group, WIFI_CONNECTED_BIT);
            xEventGroupClearBits(status_event_group, HUB_CONNECTED_BIT);
            ESP_LOGW(TAG, "System Status: ✓ WiFi | ✗ Hub");
        } else {
            display_set_status(DISPLAY_STATUS_IDLE);  // Show idle
            xEventGroupClearBits(status_event_group, WIFI_CONNECTED_BIT | HUB_CONNECTED_BIT);
            ESP_LOGW(TAG, "System Status: %s WiFi | %s Hub",
                    wifi_ok ? "✓" : "✗", hub_ok ? "✓" : "✗");
        }
        
        vTaskDelay(pdMS_TO_TICKS(2000));  // Update every 2 seconds
    }
}

/**
 * CSI data acquisition task (placeholder for now)
 */
static void csi_acquisition_task(void *pvParameter) {
    ESP_LOGI(TAG, "CSI Acquisition task started - waiting for WiFi...");
    
    // Wait for WiFi connection
    xEventGroupWaitBits(status_event_group, WIFI_CONNECTED_BIT,
                       pdFALSE, pdTRUE, portMAX_DELAY);
    
    ESP_LOGI(TAG, "WiFi connected, initializing CSI driver...");
    
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
    
    ESP_LOGI(TAG, "CSI driver initialized, starting acquisition...");
    
    if (csi_driver_start() != ESP_OK) {
        ESP_LOGE(TAG, "Failed to start CSI acquisition");
        csi_driver_deinit();
        vTaskDelete(NULL);
        return;
    }
    
    ESP_LOGI(TAG, "CSI acquisition started successfully");

    csi_frame_t frame;
    uint32_t frame_count = 0;

    while (1) {
        // Pull all available frames from the driver queue
        while (csi_driver_get_latest_frame(&frame) == ESP_OK) {
            // frame.rssi is stored as uint8_t but holds a signed int8_t from WiFi driver
            float amplitude = (float)(int8_t)frame.rssi;
            float noise_floor = (float)(int8_t)frame.noise_floor;

            // Compute mean subcarrier amplitude when data is present
            if (frame.len > 0 && frame.amplitude) {
                int32_t sum = 0;
                for (int i = 0; i < frame.len; i++) {
                    sum += frame.amplitude[i];
                }
                amplitude = (float)sum / (float)frame.len;
            }

            g_csi_amplitude = amplitude;
            g_csi_noise_floor = noise_floor;
            frame_count++;
            g_csi_frame_count = frame_count;

            if (frame_count % 100 == 0) {
                ESP_LOGI(TAG, "CSI frames: %lu  amp=%.1f  nf=%.1f",
                         frame_count, amplitude, noise_floor);
            }
        }

        vTaskDelay(pdMS_TO_TICKS(40));  // ~25 polls/sec
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
    
    uint32_t last_logged_count = 0;

    while (1) {
        // Wait for system to be fully initialized
        xEventGroupWaitBits(status_event_group, WIFI_CONNECTED_BIT | HUB_CONNECTED_BIT,
                           pdFALSE, pdTRUE, pdMS_TO_TICKS(100));

        // TODO: Process CSI frames and publish results
        // - Get CSI frame from driver
        // - Extract features using signal processor
        // - Classify activity using TinyML model
        // - Publish results via MQTT

        uint32_t current = g_csi_frame_count;
        if (current > 0 && current != last_logged_count && current % 100 == 0) {
            ESP_LOGI(TAG, "CSI frames acquired: %lu  amp=%.1f  nf=%.1f",
                     current, g_csi_amplitude, g_csi_noise_floor);
            last_logged_count = current;
        }

        vTaskDelay(pdMS_TO_TICKS(250));
    }
}

/**
 * Hub update task - periodically send device status to hub
 */
static void hub_update_task(void *pvParameter) {
    unit_config_t *config = app_config_get_current();
    
    ESP_LOGI(TAG, "Hub update task started");
    
    // Wait for HTTP client to be ready
    xEventGroupWaitBits(status_event_group, HUB_CONNECTED_BIT,
                       pdFALSE, pdTRUE, portMAX_DELAY);
    
    while (1) {
        // Wait for WiFi to be connected
        if (wifi_is_connected()) {
            // Send device update every 5 seconds
            esp_err_t err = http_publish_device_update(
                config->unit_id,
                config->unit_name,
                wifi_get_rssi(),
                wifi_get_ip_address(),
                g_csi_amplitude,
                g_csi_noise_floor
            );
            
            if (err == ESP_OK) {
                ESP_LOGD(TAG, "Device update sent to hub");
            } else {
                ESP_LOGW(TAG, "Failed to send device update: %s", esp_err_to_name(err));
            }
        }
        
        vTaskDelay(pdMS_TO_TICKS(5000));  // Send update every 5 seconds
    }
}

/**
 * Application entry point
 */
void app_main(void) {
    // Initialize configuration
    app_config_init();
    
    // Initialize display driver for status indication
    if (display_init() != ESP_OK) {
        ESP_LOGE(TAG, "Display driver initialization failed");
    } else {
        display_set_status(DISPLAY_STATUS_CONNECTING);
    }
    
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
    if (wifi_setup_init(&config->wifi, status_event_group) != ESP_OK) {
        ESP_LOGE(TAG, "WiFi initialization failed");
        return;
    }
    
    // Wait for WiFi connection before starting HTTP client
    xEventGroupWaitBits(status_event_group, WIFI_CONNECTED_BIT,
                       pdFALSE, pdTRUE, portMAX_DELAY);
    
    // Initialize HTTP client for hub communication
    ESP_LOGI(TAG, "About to initialize HTTP client...");
    if (http_client_init(&config->http) != ESP_OK) {
        ESP_LOGE(TAG, "HTTP client initialization failed");
        return;
    }
    ESP_LOGI(TAG, "HTTP client initialized successfully");
    
    // HTTP client is immediately ready (no connection phase needed)
    xEventGroupSetBits(status_event_group, HUB_CONNECTED_BIT);
    ESP_LOGI(TAG, "Set HUB_CONNECTED_BIT");
    
    ESP_LOGI(TAG, "Creating system monitoring task...");
    // Create task for system status monitoring
    if (xTaskCreate(status_monitor_task, "status_monitor",
               4096, NULL, tskIDLE_PRIORITY + 1, NULL) != pdPASS) {
        ESP_LOGE(TAG, "Failed to create status_monitor task");
    }
    
    ESP_LOGI(TAG, "Creating CSI acquisition task...");
    if (xTaskCreate(csi_acquisition_task, "csi_acquisition",
               8192, NULL, tskIDLE_PRIORITY + 3, &csi_task_handle) != pdPASS) {
        ESP_LOGE(TAG, "Failed to create csi_acquisition task");
    }
    
    ESP_LOGI(TAG, "Creating signal processing task...");
    // Create task for signal processing
    if (xTaskCreate(signal_processing_task, "signal_processing",
               8192, NULL, tskIDLE_PRIORITY + 2, &signal_process_task_handle) != pdPASS) {
        ESP_LOGE(TAG, "Failed to create signal_processing task");
    }
    
    ESP_LOGI(TAG, "Creating hub update task...");
    // Create task for sending device updates to hub
    if (xTaskCreate(hub_update_task, "hub_update",
               4096, NULL, tskIDLE_PRIORITY + 1, NULL) != pdPASS) {
        ESP_LOGE(TAG, "Failed to create hub_update task");
    }
    
    ESP_LOGI(TAG, "All tasks created successfully");
}

