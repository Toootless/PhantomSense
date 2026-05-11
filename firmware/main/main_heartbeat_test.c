#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_psram.h"

static const char *TAG = "PhantomSense_Test";

void app_main(void)
{
    ESP_LOGI(TAG, "==========================================");
    ESP_LOGI(TAG, "PhantomSense Sensor Unit - Heartbeat Test");
    ESP_LOGI(TAG, "==========================================");
    
    // Check PSRAM - critical for WiFi CSI tracking (8MB)
    size_t psram_size = esp_psram_get_size();
    if (psram_size > 0) {
        ESP_LOGI(TAG, "✓ PSRAM Found: %d MB", psram_size / (1024 * 1024));
    } else {
        ESP_LOGW(TAG, "✗ PSRAM NOT FOUND! Check Octal RAM settings in menuconfig.");
    }
    
    // Test PSRAM allocation
    uint32_t *test_buffer = heap_caps_malloc(1024 * 1024, MALLOC_CAP_SPIRAM);
    if (test_buffer) {
        ESP_LOGI(TAG, "✓ PSRAM allocation successful");
        
        // Simple write/read test
        for (int i = 0; i < 256; i++) {
            test_buffer[i] = 0xDEADBEEF + i;
        }
        
        bool psram_ok = true;
        for (int i = 0; i < 256; i++) {
            if (test_buffer[i] != 0xDEADBEEF + i) {
                psram_ok = false;
                break;
            }
        }
        
        if (psram_ok) {
            ESP_LOGI(TAG, "✓ PSRAM write/read test passed");
        } else {
            ESP_LOGE(TAG, "✗ PSRAM write/read test failed");
        }
        
        free(test_buffer);
    } else {
        ESP_LOGW(TAG, "✗ PSRAM allocation failed");
    }
    
    // System info
    ESP_LOGI(TAG, "");
    ESP_LOGI(TAG, "System Status:");
    ESP_LOGI(TAG, "  Chip: ESP32-S3-R8");
    ESP_LOGI(TAG, "  CPU Cores: 2");
    ESP_LOGI(TAG, "  CPU Frequency: 240 MHz");
    
    // Get free heap
    esp_chip_info_t chip_info;
    esp_chip_info(&chip_info);
    ESP_LOGI(TAG, "  Revision: %d", chip_info.revision);
    
    ESP_LOGI(TAG, "");
    ESP_LOGI(TAG, "Starting heartbeat loop...");
    ESP_LOGI(TAG, "");
    
    // Heartbeat loop
    int heartbeat = 0;
    while (1) {
        ESP_LOGI(TAG, "Heartbeat [%d] - System Ready ✓", heartbeat++);
        vTaskDelay(pdMS_TO_TICKS(2000));  // 2 second interval
    }
}
