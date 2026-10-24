// TFT_eSPI setup — Otto ST7789 240x240
// Copy this file over Arduino/libraries/TFT_eSPI/User_Setup.h before compile.
// CS=22 DC=21 MOSI=23 SCK=18 RST=27  BL wired to 3V3 (not a GPIO)

#define USER_SETUP_INFO "Otto_ST7789_240"

#define ST7789_DRIVER
#define TFT_WIDTH  240
#define TFT_HEIGHT 240

#define TFT_MOSI 23
#define TFT_SCLK 18
#define TFT_CS   22
#define TFT_DC   21
#define TFT_RST  27
#define TFT_BL   -1
#define TFT_MISO -1

#define TFT_INVERSION_ON

#define LOAD_GLCD
#define LOAD_FONT2

#define SPI_FREQUENCY 20000000
#define SPI_READ_FREQUENCY 16000000
#define SPI_TOUCH_FREQUENCY 2500000
