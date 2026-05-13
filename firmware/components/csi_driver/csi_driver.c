#include "csi_driver.h"
#include "esp_log.h"
#include "esp_wifi.h"
#include "esp_timer.h"
#include "freertos/FreeRTOS.h"
#include "freertos/queue.h"
#include <string.h>
#include <stdlib.h>

static const char *TAG = "CSI_DRIVER";

// CSI driver state
typedef struct {
    QueueHandle_t frame_queue;
    csi_callback_t callback;
    csi_driver_config_t config;
    uint32_t total_frames;
    uint32_t dropped_frames;
    bool initialized;
    bool running;
} csi_driver_state_t;

static csi_driver_state_t driver_state = {0};

/**
 * WiFi CSI event handler (called by WiFi driver)
 */
static void wifi_csi_event_handler(void *ctx, wifi_csi_info_t *data) {
    if (!driver_state.running) {
        return;
    }

    // Allocate memory for CSI frame
    csi_frame_t *frame = malloc(sizeof(csi_frame_t));
    if (!frame) {
        driver_state.dropped_frames++;
        return;
    }

    // Populate frame structure
    frame->timestamp_ms = esp_timer_get_time() / 1000;
    frame->rssi = data->rx_ctrl.rssi;
    frame->noise_floor = data->rx_ctrl.noise_floor;

    // data->buf contains interleaved (I, Q) int8 pairs; each pair = one subcarrier
    uint16_t num_subcarriers = (data->len > 0) ? (data->len / 2) : 0;
    frame->len = num_subcarriers;

    // Copy MAC address
    memcpy(frame->mac, data->mac, 6);

    // Allocate arrays sized for subcarrier count
    frame->amplitude = malloc(num_subcarriers * sizeof(int8_t));
    frame->phase = malloc(num_subcarriers * sizeof(int8_t));

    if (!frame->amplitude || !frame->phase) {
        free(frame->amplitude);
        free(frame->phase);
        free(frame);
        driver_state.dropped_frames++;
        return;
    }

    // Extract amplitude (|I| + |Q| approximation) and phase from I/Q pairs
    for (int i = 0; i < num_subcarriers; i++) {
        int8_t I = (int8_t)data->buf[i * 2];
        int8_t Q = (int8_t)data->buf[i * 2 + 1];
        // Amplitude approximation: |I| + |Q| (avoids sqrt, fits int8_t range)
        int16_t amp = (I < 0 ? -I : I) + (Q < 0 ? -Q : Q);
        frame->amplitude[i] = (int8_t)(amp > 127 ? 127 : amp);
        frame->phase[i] = Q;  // Store Q as phase proxy
    }

    // Send to queue
    if (xQueueSend(driver_state.frame_queue, &frame, 0) != pdPASS) {
        // Queue full, drop frame
        free(frame->amplitude);
        free(frame->phase);
        free(frame);
        driver_state.dropped_frames++;
    } else {
        driver_state.total_frames++;
        
        // Call callback if registered
        if (driver_state.callback) {
            driver_state.callback(frame);
        }
    }
}

esp_err_t csi_driver_init(const csi_driver_config_t *config) {
    if (driver_state.initialized) {
        ESP_LOGW(TAG, "Driver already initialized");
        return ESP_OK;
    }

    if (!config) {
        return ESP_ERR_INVALID_ARG;
    }

    // Store configuration
    memcpy(&driver_state.config, config, sizeof(csi_driver_config_t));

    // Create queue for CSI frames
    driver_state.frame_queue = xQueueCreate(config->buffer_size, sizeof(csi_frame_t *));
    if (!driver_state.frame_queue) {
        ESP_LOGE(TAG, "Failed to create frame queue");
        return ESP_ERR_NO_MEM;
    }

    // Initialize driver state
    driver_state.total_frames = 0;
    driver_state.dropped_frames = 0;
    driver_state.initialized = true;
    driver_state.running = false;

    ESP_LOGI(TAG, "CSI Driver initialized: buffer_size=%d, sampling_rate=%ldHz",
            config->buffer_size, config->sampling_rate_hz);

    return ESP_OK;
}

esp_err_t csi_driver_start(void) {
    if (!driver_state.initialized) {
        ESP_LOGE(TAG, "Driver not initialized");
        return ESP_ERR_INVALID_STATE;
    }

    if (driver_state.running) {
        ESP_LOGW(TAG, "Driver already running");
        return ESP_OK;
    }

    // Configure WiFi to capture CSI
    wifi_csi_config_t csi_config = {
        .lltf_en = true,           // Enable LLTF data capture
        .htltf_en = true,          // Enable HTLTF data capture
        .stbc_htltf2_en = true,    // Enable STBC HTLTF2 data
        .ltf_merge_en = true,      // Enable LTF merge
        .channel_filter_en = true, // Enable channel filter
        .manu_scale = false,       // Use automatic scaling
        .shift = 0,
        .dump_ack_en = false,      // Don't dump ACK frames
    };

    esp_err_t ret = esp_wifi_set_csi_config(&csi_config);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to configure WiFi CSI: %s", esp_err_to_name(ret));
        return ret;
    }

    // Enable CSI capture
    ret = esp_wifi_set_csi(true);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to enable WiFi CSI: %s", esp_err_to_name(ret));
        return ret;
    }

    // Register CSI callback
    ret = esp_wifi_set_csi_rx_cb(&wifi_csi_event_handler, NULL);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to register CSI callback: %s", esp_err_to_name(ret));
        return ret;
    }

    driver_state.running = true;
    ESP_LOGI(TAG, "CSI data acquisition started");

    return ESP_OK;
}

esp_err_t csi_driver_stop(void) {
    if (!driver_state.running) {
        return ESP_OK;
    }

    driver_state.running = false;
    esp_wifi_set_csi_rx_cb(NULL, NULL);

    ESP_LOGI(TAG, "CSI data acquisition stopped");
    return ESP_OK;
}

esp_err_t csi_driver_register_callback(csi_callback_t callback) {
    driver_state.callback = callback;
    return ESP_OK;
}

esp_err_t csi_driver_get_latest_frame(csi_frame_t *frame) {
    if (!frame) {
        return ESP_ERR_INVALID_ARG;
    }

    csi_frame_t *queued_frame = NULL;
    if (xQueueReceive(driver_state.frame_queue, &queued_frame, 0) != pdPASS) {
        return ESP_ERR_INVALID_STATE;
    }

    memcpy(frame, queued_frame, sizeof(csi_frame_t));
    free(queued_frame->amplitude);
    free(queued_frame->phase);
    free(queued_frame);

    return ESP_OK;
}

uint32_t csi_driver_get_buffer_count(void) {
    return uxQueueMessagesWaiting(driver_state.frame_queue);
}

esp_err_t csi_driver_get_stats(uint32_t *total_frames, uint32_t *dropped_frames) {
    if (!total_frames || !dropped_frames) {
        return ESP_ERR_INVALID_ARG;
    }

    *total_frames = driver_state.total_frames;
    *dropped_frames = driver_state.dropped_frames;

    return ESP_OK;
}

esp_err_t csi_driver_deinit(void) {
    if (!driver_state.initialized) {
        return ESP_OK;
    }

    csi_driver_stop();

    if (driver_state.frame_queue) {
        vQueueDelete(driver_state.frame_queue);
    }

    memset(&driver_state, 0, sizeof(csi_driver_state_t));
    ESP_LOGI(TAG, "CSI Driver deinitialized");

    return ESP_OK;
}
