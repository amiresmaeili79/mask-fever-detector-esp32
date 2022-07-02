#include "WiFi.h"
#include "esp_camera.h"
#include "esp_timer.h"
#include "img_converters.h"
#include "Arduino.h"
#include "soc/soc.h"		  // Disable brownour problems
#include "soc/rtc_cntl_reg.h" // Disable brownour problems
#include "driver/rtc_io.h"
#include "stdlib.h"
#include <SPIFFS.h>
#include <FS.h>
#include <PubSubClient.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"
#include <OneWire.h>
#include <DallasTemperature.h>
#include "../include/secrets.h"

// OV2640 camera module pins (CAMERA_MODEL_AI_THINKER)
#define PWDN_GPIO_NUM 32
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM 0
#define SIOD_GPIO_NUM 26
#define SIOC_GPIO_NUM 27
#define Y9_GPIO_NUM 35
#define Y8_GPIO_NUM 34
#define Y7_GPIO_NUM 39
#define Y6_GPIO_NUM 36
#define Y5_GPIO_NUM 21
#define Y4_GPIO_NUM 19
#define Y3_GPIO_NUM 18
#define Y2_GPIO_NUM 5
#define VSYNC_GPIO_NUM 25
#define HREF_GPIO_NUM 23
#define PCLK_GPIO_NUM 22
#define FLASH_GPIO_NUM 4

// ledPin refers to ESP32-CAM GPIO 4 (flashlight)
#define FLASH_GPIO_NUM 4

// Replace with your network credentials
const char *SSID = "Amir";
const char *PASSWORD = "A137915a";

WiFiClient wifiClient;
PubSubClient client(wifiClient);

boolean workInProgress = false;

// To avoid sending extra messages
boolean recievedResponse = true;
short counter = 0;

// Temperature ports
const int oneWireBus = 14;
OneWire oneWire(oneWireBus);
DallasTemperature sensors(&oneWire);

// Flashing ability 
void flashOnForNSeconds(int seconds)
{
	digitalWrite(FLASH_GPIO_NUM, HIGH);
	delay(seconds * 1000);
	digitalWrite(FLASH_GPIO_NUM, LOW);
}

// Capture Photo and Temperature and send it over MQTT
void capturePhotoAndTemp(void)
{
    if (workInProgress == false)
    {
        workInProgress = true;
        camera_fb_t *fb = NULL;
		
		// Get photo buffer
        fb = esp_camera_fb_get();
        if (!fb)
        {
            Serial.println("Camera capture failed");
            workInProgress = false;
            return;
        }

        bool res = client.publish(PUBLISH_TOPIC, fb->buf, fb->len, false);
		// If publishing photo succeeds
        if (res)
		{
			sensors.requestTemperatures(); 
  			int temperatureC = sensors.getTempCByIndex(0);
			char temp[34];
			sprintf(temp, "%d", temperatureC);
			// Publish temperature
			client.publish(PUBLISH_TOPIC, temp);
            Serial.println("[INFO] New message published");
			recievedResponse = false;
			counter++;
		}
        else
		{
            Serial.println("[ERRRO] Failed to publish message");
			recievedResponse = true;
		}

		// Release frame buffer
        esp_camera_fb_return(fb);
        workInProgress = false;
    }
}

void initCamera()
{
	// Turn-off the 'brownout detector'
	WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

	// OV2640 camera module
	camera_config_t config;
	config.ledc_channel = LEDC_CHANNEL_0;
	config.ledc_timer = LEDC_TIMER_0;
	config.pin_d0 = Y2_GPIO_NUM;
	config.pin_d1 = Y3_GPIO_NUM;
	config.pin_d2 = Y4_GPIO_NUM;
	config.pin_d3 = Y5_GPIO_NUM;
	config.pin_d4 = Y6_GPIO_NUM;
	config.pin_d5 = Y7_GPIO_NUM;
	config.pin_d6 = Y8_GPIO_NUM;
	config.pin_d7 = Y9_GPIO_NUM;
	config.pin_xclk = XCLK_GPIO_NUM;
	config.pin_pclk = PCLK_GPIO_NUM;
	config.pin_vsync = VSYNC_GPIO_NUM;
	config.pin_href = HREF_GPIO_NUM;
	config.pin_sscb_sda = SIOD_GPIO_NUM;
	config.pin_sscb_scl = SIOC_GPIO_NUM;
	config.pin_pwdn = PWDN_GPIO_NUM;
	config.pin_reset = RESET_GPIO_NUM;
	config.xclk_freq_hz = 20000000;
	config.pixel_format = PIXFORMAT_JPEG;
	config.frame_size = FRAMESIZE_VGA;
	config.jpeg_quality = 10;
	config.fb_count = 1;

	// Camera init
	esp_err_t err = esp_camera_init(&config);
	if (err != ESP_OK)
	{
		Serial.printf("Camera init failed with error 0x%x", err);
		ESP.restart();
	}
}

void initAndConnectWifi()
{
	// Connect to Wi-Fi
	int startWifiTime = millis();
	WiFi.begin(SSID, PASSWORD);
	while (WiFi.status() != WL_CONNECTED)
	{
		int secondsWaiting = (millis() - startWifiTime) / 1000;
		Serial.println("[INFO] Connecting to Wi-Fi...");
		Serial.println(secondsWaiting);
		delay(1000);
	}
	// Print ESP32 Local IP Address
	Serial.print("[INFO] Connected to Wi-Fi: IP Address: http://");
	Serial.println(WiFi.localIP());
}

// This function handles new messages from subscription
void callback(char *topic, byte *payload, unsigned int length)
{
	recievedResponse = true;
	counter--;
	Serial.printf("[INFO] Message #%d arrived - Has mask: ");
	for (int i = 0; i < length; i++)
	{
		Serial.print((char)payload[i]);
	}
	Serial.println();
}

// Connect to MQTT server
void connect()
{
	if (!client.connected())
		client.connect(CLIENT_ID, MQTT_USER, MQTT_PASS);
}

// Subscribe to topic
void subscribe()
{
	client.subscribe(SUBSCRIBE_TOPIC);
	client.setCallback(callback);
}

void setup()
{
	// Serial port for debugging purposes
	Serial.begin(9600);
	WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);

	// initialize digital pin ledPin as an output
	pinMode(FLASH_GPIO_NUM, OUTPUT);

	// connect to wifi
	initAndConnectWifi();
	initCamera();

	// MQTT start
	client.setServer(BROKER, 1883);
	connect();
	subscribe();

	bool couldAlloc = client.setBufferSize(65535);
	if (!couldAlloc)
		Serial.println("[ERROR] Could not allocate buffer size");

	// Start temperature
	sensors.begin();
}

void loop()
{
	// Connection may get lost while looping
	while (!client.connected())
		connect();

	// If we have more than three messages without response
	// don't send anything
	if (recievedResponse || counter <= 3)
		capturePhotoAndTemp();

	client.loop();
	delay(3000);
}