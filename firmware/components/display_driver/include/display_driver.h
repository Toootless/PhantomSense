#pragma once

#include "esp_err.h"

typedef enum {
    DISPLAY_STATUS_IDLE,           // No connection
    DISPLAY_STATUS_CONNECTING,     // Attempting to connect
    DISPLAY_STATUS_CONNECTED,      // Connected to basestation (GREEN)
    DISPLAY_STATUS_ERROR,          // Error state (RED)
    DISPLAY_STATUS_TRANSMITTING,   // Actively transmitting data (GREEN + BLINK)
} display_status_t;

/**
 * @brief Initialize the display driver
 * Uses a simple GPIO-based indicator (can be LED, relay, or simple display)
 */
esp_err_t display_init(void);

/**
 * @brief Set the display status
 * @param status The current status to display
 */
esp_err_t display_set_status(display_status_t status);

/**
 * @brief Get current display status
 */
display_status_t display_get_status(void);

/**
 * @brief Cleanup display
 */
esp_err_t display_deinit(void);
