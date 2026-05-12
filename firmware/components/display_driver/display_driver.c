#include "display_driver.h"
#include "esp_log.h"
#include "driver/gpio.h"
#include "driver/ledc.h"
#include "driver/spi_master.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include <string.h>

static const char *TAG = "DISPLAY";

// ============= RGB LED Configuration =============
// WS2812B Addressable RGB LED (Waveshare ESP32-S3-LCD-1.47)
// NOTE: This is NOT a simple RGB LED - it's a WS2812B that requires RMT (or Bitbang)
//       Simple GPIO HIGH/LOW will NOT work. Implement RMT peripheral support.
// 
// Hardware Location: Tiny white square component near USB-C port
// Data Pin: GPIO 38 (requires RMT peripheral for timing-critical protocol)
#define RGB_LED_DATA_PIN   GPIO_NUM_38

// RMT configuration (to be implemented)
#define RMT_LED_RESOLUTION_HZ  10000000  // 10MHz for WS2812B timing
#define RMT_LED_CHANNEL        RMT_CHANNEL_0

// Legacy LEDC defines (kept for reference, not used for RGB)
#define LEDC_TIMER      LEDC_TIMER_0
#define LEDC_MODE       LEDC_LOW_SPEED_MODE
#define LEDC_FREQUENCY  5000
#define LEDC_RESOLUTION LEDC_TIMER_8_BIT

// ============= LCD Configuration (ST7789) =============
// SPI pins for LCD (Waveshare ESP32-S3-LCD-1.47)
// Verified against official Waveshare schematic
#define LCD_SPI_HOST       SPI2_HOST
#define LCD_PIN_MOSI       GPIO_NUM_11     // SPI MOSI
#define LCD_PIN_SCLK       GPIO_NUM_10     // SPI Clock
#define LCD_PIN_CS         GPIO_NUM_12     // Chip Select
#define LCD_PIN_DC         GPIO_NUM_14     // Data/Command
#define LCD_PIN_RST        GPIO_NUM_13     // Display Reset
#define LCD_PIN_BACKLIGHT  GPIO_NUM_15     // Backlight control (MUST be HIGH to see display)

#define LCD_SPI_FREQ_HZ    (80 * 1000 * 1000)  // 80 MHz
#define LCD_WIDTH          172
#define LCD_HEIGHT         320

// LCD color definitions (RGB565 format)
#define LCD_COLOR_RED      0xF800   // 11111 00000 00000
#define LCD_COLOR_GREEN    0x07E0   // 00000 11111 00000
#define LCD_COLOR_BLUE     0x001F   // 00000 00000 11111
#define LCD_COLOR_YELLOW   0xFFE0   // 11111 11111 00000 (RED + GREEN)
#define LCD_COLOR_BLACK    0x0000
#define LCD_COLOR_WHITE    0xFFFF

// SPI device handle
static spi_device_handle_t lcd_spi = NULL;

// Current status
static display_status_t current_status = DISPLAY_STATUS_IDLE;
static display_status_t previous_status = DISPLAY_STATUS_IDLE;

// Task handle for blink animation
static TaskHandle_t blink_task_handle = NULL;

// RGB color values (0-255 for each channel)
typedef struct {
    uint8_t red;
    uint8_t green;
    uint8_t blue;
} rgb_color_t;

// ============= RGB LED Functions =============
// NOTE: RGB LED (GPIO 38, WS2812B) requires RMT implementation (not ready yet)
// For now, we'll use LCD display to show status colors
static void set_rgb_color(rgb_color_t color) {
    // Placeholder - RMT implementation pending
    // This would send timing-critical data to GPIO 38 for WS2812B
    ESP_LOGV(TAG, "RGB color request: R=%d G=%d B=%d (pending RMT impl)", 
             color.red, color.green, color.blue);
}

// ============= LCD Functions (defined later) =============
// Forward declarations for LCD color functions
static void lcd_fill_color(uint16_t color);
static void lcd_fill_yellow(void);
static void lcd_fill_white(void);
static void lcd_fill_red(void);
static void lcd_fill_green(void);
static void lcd_fill_blue(void);
static void lcd_fill_black(void);

// ============= LCD Functions =============
// Initialize SPI for LCD
static esp_err_t lcd_spi_init(void) {
    ESP_LOGI(TAG, "Initializing LCD SPI interface");
    
    spi_bus_config_t buscfg = {
        .mosi_io_num = LCD_PIN_MOSI,
        .miso_io_num = -1,
        .sclk_io_num = LCD_PIN_SCLK,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = LCD_WIDTH * LCD_HEIGHT * 2 + 8,
    };
    
    spi_device_interface_config_t devcfg = {
        .clock_speed_hz = LCD_SPI_FREQ_HZ,
        .mode = 0,
        .spics_io_num = LCD_PIN_CS,
        .queue_size = 7,
        .flags = SPI_DEVICE_NO_DUMMY,
    };
    
    ESP_ERROR_CHECK(spi_bus_initialize(LCD_SPI_HOST, &buscfg, SPI_DMA_CH_AUTO));
    ESP_ERROR_CHECK(spi_bus_add_device(LCD_SPI_HOST, &devcfg, &lcd_spi));
    
    return ESP_OK;
}

// Send command to LCD
static void lcd_send_cmd(uint8_t cmd) {
    gpio_set_level(LCD_PIN_DC, 0);  // Set DC low for command
    
    spi_transaction_t t = {
        .length = 8,
        .tx_buffer = &cmd,
    };
    
    ESP_ERROR_CHECK(spi_device_transmit(lcd_spi, &t));
}

// Send data to LCD
static void lcd_send_data(const uint8_t *data, uint32_t len) {
    gpio_set_level(LCD_PIN_DC, 1);  // Set DC high for data
    
    spi_transaction_t t = {
        .length = len * 8,
        .tx_buffer = data,
    };
    
    ESP_ERROR_CHECK(spi_device_transmit(lcd_spi, &t));
}

// Initialize ST7789 display
static esp_err_t lcd_st7789_init(void) {
    ESP_LOGI(TAG, "Initializing ST7789 display");
    
    // Reset display
    gpio_set_level(LCD_PIN_RST, 0);
    vTaskDelay(pdMS_TO_TICKS(10));
    gpio_set_level(LCD_PIN_RST, 1);
    vTaskDelay(pdMS_TO_TICKS(120));
    
    // Basic initialization commands
    lcd_send_cmd(0x11);  // Sleep Out
    vTaskDelay(pdMS_TO_TICKS(10));
    
    lcd_send_cmd(0x36);  // Memory Access Control
    uint8_t madctl = 0x00;
    lcd_send_data(&madctl, 1);
    
    lcd_send_cmd(0x3A);  // Interface Pixel Format
    uint8_t colmod = 0x05;  // 16-bit color
    lcd_send_data(&colmod, 1);
    
    lcd_send_cmd(0x21);  // Display Inversion On
    vTaskDelay(pdMS_TO_TICKS(10));
    
    lcd_send_cmd(0x29);  // Display ON
    vTaskDelay(pdMS_TO_TICKS(10));
    
    // Turn on backlight
    gpio_set_level(LCD_PIN_BACKLIGHT, 1);
    
    ESP_LOGI(TAG, "ST7789 display initialized");
    return ESP_OK;
}

// Set LCD write window
static void lcd_set_window(uint16_t x0, uint16_t y0, uint16_t x1, uint16_t y1) {
    // Column address set
    lcd_send_cmd(0x2A);
    uint8_t col[4] = {(x0 >> 8), (x0 & 0xFF), (x1 >> 8), (x1 & 0xFF)};
    lcd_send_data(col, 4);
    
    // Row address set
    lcd_send_cmd(0x2B);
    uint8_t row[4] = {(y0 >> 8), (y0 & 0xFF), (y1 >> 8), (y1 & 0xFF)};
    lcd_send_data(row, 4);
    
    // Memory write
    lcd_send_cmd(0x2C);
}

// Fill LCD with a solid color (RGB565)
static void lcd_fill_color(uint16_t color) {
    uint16_t width = LCD_WIDTH;
    uint16_t height = LCD_HEIGHT;
    
    ESP_LOGI(TAG, "LCD: Filling with color 0x%04X (width=%d, height=%d)", color, width, height);
    
    // Set write window to full screen
    lcd_set_window(0, 0, width - 1, height - 1);
    
    // Allocate buffer for one row
    uint16_t *row_buffer = malloc(width * sizeof(uint16_t));
    if (!row_buffer) {
        ESP_LOGE(TAG, "Failed to allocate row buffer");
        return;
    }
    
    // Fill buffer with color
    for (uint16_t i = 0; i < width; i++) {
        row_buffer[i] = color;
    }
    
    // Send each row
    gpio_set_level(LCD_PIN_DC, 1);  // Data mode
    
    for (uint16_t row = 0; row < height; row++) {
        spi_transaction_t t = {
            .length = width * 16,  // bits
            .tx_buffer = row_buffer,
        };
        
        ESP_ERROR_CHECK(spi_device_transmit(lcd_spi, &t));
        
        if (row % 50 == 0) {
            ESP_LOGI(TAG, "LCD: Row %d/%d", row, height);
        }
    }
    
    free(row_buffer);
    ESP_LOGI(TAG, "LCD: Fill complete");
}

// Fill LCD with RED
static void lcd_fill_red(void) {
    lcd_fill_color(LCD_COLOR_RED);
}

// Fill LCD with GREEN
static void lcd_fill_green(void) {
    lcd_fill_color(LCD_COLOR_GREEN);
}

// Fill LCD with BLUE
static void lcd_fill_blue(void) {
    lcd_fill_color(LCD_COLOR_BLUE);
}

// Fill LCD with BLACK
static void lcd_fill_black(void) {
    lcd_fill_color(LCD_COLOR_BLACK);
}

// Fill LCD with YELLOW (for CONNECTING state)
static void lcd_fill_yellow(void) {
    lcd_fill_color(LCD_COLOR_YELLOW);
}

// Fill LCD with WHITE  
static void lcd_fill_white(void) {
    lcd_fill_color(LCD_COLOR_WHITE);
}

// Helper function to get LCD color for a given status
static uint16_t get_color_for_status(display_status_t status) {
    switch (status) {
        case DISPLAY_STATUS_IDLE:
            return LCD_COLOR_BLUE;          // Blue = waiting, idle
        case DISPLAY_STATUS_CONNECTING:
            return LCD_COLOR_YELLOW;        // Yellow = attempting connection
        case DISPLAY_STATUS_CONNECTED:
            return LCD_COLOR_GREEN;         // Green = successfully connected
        case DISPLAY_STATUS_ERROR:
            return LCD_COLOR_RED;           // Red = error/failure
        case DISPLAY_STATUS_TRANSMITTING:
            return LCD_COLOR_GREEN;         // Green = transmitting data
        default:
            return LCD_COLOR_BLACK;         // Black = unknown state
    }
}

// Helper function to get status name
static const char* get_status_name(display_status_t status) {
    switch (status) {
        case DISPLAY_STATUS_IDLE:
            return "IDLE";
        case DISPLAY_STATUS_CONNECTING:
            return "CONNECTING";
        case DISPLAY_STATUS_CONNECTED:
            return "CONNECTED";
        case DISPLAY_STATUS_ERROR:
            return "ERROR";
        case DISPLAY_STATUS_TRANSMITTING:
            return "TRANSMITTING";
        default:
            return "UNKNOWN";
    }
}

// Display status task - Shows device status on LCD screen
static void display_blink_task(void *pvParameter) {
    vTaskDelay(pdMS_TO_TICKS(500));
    
    ESP_LOGI(TAG, "=== LCD Status Display Task Started ===");
    ESP_LOGI(TAG, "Color Mapping:");
    ESP_LOGI(TAG, "  IDLE → BLUE");
    ESP_LOGI(TAG, "  CONNECTING → YELLOW");
    ESP_LOGI(TAG, "  CONNECTED → GREEN");
    ESP_LOGI(TAG, "  ERROR → RED");
    ESP_LOGI(TAG, "  TRANSMITTING → GREEN (with blink)");
    
    // ===== COLOR TEST MODE =====
    ESP_LOGI(TAG, "=== Starting LCD Color Test ===");
    ESP_LOGI(TAG, "Cycling through all colors (2 seconds each)...");
    
    // Test each color
    ESP_LOGI(TAG, "[1/6] Testing BLUE");
    lcd_fill_blue();
    vTaskDelay(pdMS_TO_TICKS(2000));
    
    ESP_LOGI(TAG, "[2/6] Testing YELLOW");
    lcd_fill_yellow();
    vTaskDelay(pdMS_TO_TICKS(2000));
    
    ESP_LOGI(TAG, "[3/6] Testing GREEN");
    lcd_fill_green();
    vTaskDelay(pdMS_TO_TICKS(2000));
    
    ESP_LOGI(TAG, "[4/6] Testing RED");
    lcd_fill_red();
    vTaskDelay(pdMS_TO_TICKS(2000));
    
    ESP_LOGI(TAG, "[5/6] Testing WHITE");
    lcd_fill_white();
    vTaskDelay(pdMS_TO_TICKS(2000));
    
    ESP_LOGI(TAG, "[6/6] Testing BLACK");
    lcd_fill_black();
    vTaskDelay(pdMS_TO_TICKS(2000));
    
    ESP_LOGI(TAG, "=== Color Test Complete ===");
    ESP_LOGI(TAG, "Returning to normal status display mode");
    
    // ===== NORMAL STATUS DISPLAY MODE =====
    display_status_t last_status = DISPLAY_STATUS_IDLE;
    uint16_t blink_counter = 0;
    
    while (1) {
        display_status_t current = current_status;
        
        // Handle status changes
        if (current != last_status) {
            ESP_LOGI(TAG, "Status changed: %s → %s", 
                     get_status_name(last_status), 
                     get_status_name(current));
            last_status = current;
            blink_counter = 0;
        }
        
        // Update LCD based on status
        uint16_t color = get_color_for_status(current);
        
        // Special handling for TRANSMITTING - blink effect
        if (current == DISPLAY_STATUS_TRANSMITTING) {
            // Blink effect: ON for 200ms, OFF for 300ms
            if (blink_counter % 2 == 0) {
                lcd_fill_color(color);  // GREEN on
            } else {
                lcd_fill_black();        // OFF
            }
            blink_counter++;
            ESP_LOGV(TAG, "TRANSMITTING blink cycle %d, color: %s", 
                     blink_counter, blink_counter % 2 == 0 ? "ON" : "OFF");
            vTaskDelay(pdMS_TO_TICKS(250));
        } else {
            // Solid color for other states
            lcd_fill_color(color);
            ESP_LOGV(TAG, "Display: %s (0x%04X)", get_status_name(current), color);
            vTaskDelay(pdMS_TO_TICKS(500));
        }
    }
}

esp_err_t display_init(void) {
    ESP_LOGI(TAG, "Initializing display with corrected GPIO pins (Waveshare verified)");
    
    // ===== Initialize LCD backlight control (GPIO 15) =====
    // This is the display backlight - MUST be HIGH to see anything on LCD
    gpio_reset_pin(LCD_PIN_BACKLIGHT);
    gpio_set_direction(LCD_PIN_BACKLIGHT, GPIO_MODE_OUTPUT);
    gpio_set_level(LCD_PIN_BACKLIGHT, 1);  // Turn ON backlight
    ESP_LOGI(TAG, "LCD backlight enabled (GPIO%d = HIGH)", LCD_PIN_BACKLIGHT);
    
    // ===== DIAGNOSTIC: Verify GPIO 15 is actually HIGH =====
    int backlight_level = gpio_get_level(LCD_PIN_BACKLIGHT);
    ESP_LOGI(TAG, "DIAGNOSTIC: GPIO%d read back as: %d (should be 1)", LCD_PIN_BACKLIGHT, backlight_level);
    if (backlight_level != 1) {
        ESP_LOGE(TAG, "ERROR: Backlight GPIO not responding! Pin may be misconfigured or shorted");
    }
    
    // ===== Initialize LCD Reset and DC pins =====
    gpio_reset_pin(LCD_PIN_RST);
    gpio_set_direction(LCD_PIN_RST, GPIO_MODE_OUTPUT);
    gpio_reset_pin(LCD_PIN_DC);
    gpio_set_direction(LCD_PIN_DC, GPIO_MODE_OUTPUT);
    ESP_LOGI(TAG, "LCD control pins configured (RST=%d, DC=%d)", LCD_PIN_RST, LCD_PIN_DC);
    
    // ===== Initialize LCD SPI Interface =====
    ESP_LOGI(TAG, "Initializing LCD SPI (MOSI=%d, CLK=%d, CS=%d)", 
             LCD_PIN_MOSI, LCD_PIN_SCLK, LCD_PIN_CS);
    if (lcd_spi_init() != ESP_OK) {
        ESP_LOGE(TAG, "Failed to initialize LCD SPI");
        return ESP_FAIL;
    }
    
    // ===== Initialize ST7789 Display =====
    if (lcd_st7789_init() != ESP_OK) {
        ESP_LOGE(TAG, "Failed to initialize ST7789");
        return ESP_FAIL;
    }
    
    // ===== RGB LED (WS2812B) - Pending RMT Implementation =====
    ESP_LOGW(TAG, "RGB LED (WS2812B) support pending RMT implementation");
    ESP_LOGW(TAG, "  Data Pin: GPIO%d (requires RMT peripheral)", RGB_LED_DATA_PIN);
    
    // Create status display task
    if (xTaskCreate(display_blink_task, "display_status", 3072, NULL, 5, &blink_task_handle) != pdPASS) {
        ESP_LOGE(TAG, "Failed to create display task");
        return ESP_FAIL;
    }
    
    ESP_LOGI(TAG, "Display init complete - LCD ready for status display");
    current_status = DISPLAY_STATUS_IDLE;
    
    // Show initial IDLE state (blue)
    lcd_fill_blue();
    
    return ESP_OK;
}

esp_err_t display_set_status(display_status_t status) {
    if (current_status != status) {
        previous_status = current_status;
        current_status = status;
        uint16_t color = get_color_for_status(status);
        
        const char *color_name = "UNKNOWN";
        switch (color) {
            case LCD_COLOR_RED:
                color_name = "RED"; break;
            case LCD_COLOR_GREEN:
                color_name = "GREEN"; break;
            case LCD_COLOR_BLUE:
                color_name = "BLUE"; break;
            case LCD_COLOR_YELLOW:
                color_name = "YELLOW"; break;
            case LCD_COLOR_BLACK:
                color_name = "BLACK"; break;
            case LCD_COLOR_WHITE:
                color_name = "WHITE"; break;
        }
        
        ESP_LOGI(TAG, "Display status: %s → %s (LCD: %s, 0x%04X)", 
                 get_status_name(previous_status), 
                 get_status_name(status),
                 color_name, color);
    }
    
    return ESP_OK;
}

display_status_t display_get_status(void) {
    return current_status;
}

esp_err_t display_deinit(void) {
    if (blink_task_handle != NULL) {
        vTaskDelete(blink_task_handle);
        blink_task_handle = NULL;
    }
    
    // Turn off LCD display (black)
    lcd_fill_black();
    
    // Turn off backlight
    gpio_set_level(LCD_PIN_BACKLIGHT, 0);
    
    ESP_LOGI(TAG, "Display driver deinitialized - backlight OFF");
    
    return ESP_OK;
}
