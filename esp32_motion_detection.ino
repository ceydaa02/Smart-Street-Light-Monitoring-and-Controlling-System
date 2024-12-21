#include <WiFi.h>             // ESP32 Wi-Fi kütüphanesi
#include <WebServer.h>        // ESP32 Web Server kütüphanesi
#include <HTTPClient.h>

// Wi-Fi bilgileri
const char* ssid = "Ceyda";      // Wi-Fi ağ adı
const char* password = "merhabalarben1234";       // Wi-Fi şifresi

const char* serverUrl = "http://172.20.10.5:5000/data";


int LDR_Val = 0;                // Variable to store photoresistor value
int sensor = 34;                // Analog Input for photoresistor
int led[] = {25, 26, 27};           // LED output Pins
const int IR_SENSOR[] = {12, 13, 14}; // Infrared sensor Pins
unsigned long smpltmr[] = {0, 0, 0}; // Sampling timers for IR sensors
unsigned long ledTimer[] = {0, 0, 0}; // LED timers for independent control
bool ledOn[] = {0, 0, 0};  // LED state for each sensor
byte lastSt[] = {0xFF, 0xFF, 0xFF};   // Last states for IR sensors
byte fixedSt[] = {0xFF, 0xFF, 0xFF};  // Fixed states for IR sensors
bool ldrState = false;          // High Intensity (true) or Low Intensity (false)
int check_old_led[] = {0, 0, 0};

void updateLedState(int index, int state) {
    ledOn[index] = state;
}

int check_led(int ledIndex, int value){
  if(check_old_led[ledIndex] == value){
    return 1;
  }
  else{
    check_old_led[ledIndex] = value;
    return 0;
  }
}

String get_json_data(int ledIndex, int value) {
    if (ledIndex < 0 || ledIndex >= 3) { // Geçerli bir index kontrolü
        return "{\"error\": \"Invalid LED index\"}";
    }
    if(!check_led(ledIndex, value)){
      String jsonResponse = "{";
      jsonResponse += "\"LED" + String(ledIndex + 1) + "_Status\": " + String(value);
      jsonResponse += "}";
      // Serial.println("Sending data: " + jsonResponse);

      return jsonResponse;
    }
    else{
      return "";
    }
}



void sendDataToServer(int ledIndex, int value) {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http; // HTTP istemci nesnesi

    http.begin(serverUrl); // Sunucu adresini başlat
    http.addHeader("Content-Type", "application/json"); // JSON gönderimi için header ekle

    String json_data = get_json_data(ledIndex, value);
    if(json_data != ""){
    int httpResponseCode = http.POST(json_data); // Veri gönderimi (POST isteği)
    if (httpResponseCode > 0) {
      Serial.println("Sunucuya veri gönderildi. HTTP Yanıt Kodu: " + String(httpResponseCode));
    } else {
      Serial.println("Veri gönderim hatası: " + String(http.errorToString(httpResponseCode).c_str()));
    }
    
    http.end(); // İstek tamamlandı
    }
  } else {
    Serial.println("WiFi bağlantısı yok. Veri gönderilemedi.");
  }
}


void setup() {
      WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.println("Connecting to WiFi...");
    }
    Serial.println("WiFi connected. IP Address: " + WiFi.localIP().toString());

  for (int i = 0; i < 3; i++) {
    pinMode(IR_SENSOR[i], INPUT); // Set IR sensor pins as input
    pinMode(led[i], OUTPUT);      // Set LED pins as output
  }
  Serial.begin(115200);          // Baud rate for serial communication
}


void loop() {
  // LDR okuma ve ışık yoğunluğu kontrolü
  LDR_Val = analogRead(sensor); // LDR değerini oku
  Serial.print("LDR Output Value: ");
  Serial.println(LDR_Val); // LDR değerini seri monitöre yazdır

  // Eğer ışık yoğunluğu yüksekse
  if (LDR_Val > 100) { 
    if (!ldrState) { // Eğer önceden Low Intensity durumundaydıysa
      Serial.println("High Intensity");
      for (int i = 0; i < 3; i++) {
        analogWrite(led[i], 0); // LED'leri kapat
        updateLedState(i, 0);       // LED durumunu güncelle
        sendDataToServer(i, 0); 
      }
      ldrState = true;          // High Intensity durumuna geçiş
    }
  } 
  else { // Eğer ışık yoğunluğu düşükse
    if (ldrState) { // Eğer önceden High Intensity durumundaydıysa
      Serial.println("Low Intensity... Checking motion.");
      for (int i = 0; i < 3; i++) {
        analogWrite(led[i], 50); // LED'leri düşük yoğunlukta yak
        updateLedState(i, 1);;          // LED açık duruma geçer
        sendDataToServer(i, 1); 
      }
      ldrState = false;          // Low Intensity durumuna geçiş
    }

    for (int i = 0; i < 3; i++) {
      // Her sensör için IR kontrolü
      if (millis() - smpltmr[i] >= 40) {
        smpltmr[i] = millis();
        byte st = digitalRead(IR_SENSOR[i]);
        int cmp = (st == lastSt[i]);
        lastSt[i] = st;

        if (cmp && st != fixedSt[i]) {
          fixedSt[i] = st;
          st = (~st) & 0x01; // Durumu ters çevir
          if (st == 1) {
            Serial.print("Sensor ");
            Serial.print(i + 1);
            Serial.println(": Obstacle detected");
            analogWrite(led[i], 255); // LED yüksek yoğunlukta yanar
            updateLedState(i, 2);;          // LED açık duruma geçer
            sendDataToServer(i, 2); 
            ledTimer[i] = millis();   // Zamanlayıcı başlatılır
          } 
          else {
            Serial.print("Sensor ");
            Serial.print(i + 1);
            Serial.println(": Obstacle cleared");
            analogWrite(led[i], 50);  // LED düşük yoğunlukta yanar
            updateLedState(i, 1);        // LED kapalı duruma geçer
            sendDataToServer(i, 1); 
          }
        }
      }

      // LED'in açık kalma süresini kontrol et
      if (ledOn[i] && millis() - ledTimer[i] >= 3000) {
        analogWrite(led[i], 50); // LED düşük yoğunlukta yanar
        updateLedState(i, 1);        // LED kapalı duruma geçer
        sendDataToServer(i, 1);        // LED kapalı duruma geçer
      }
    }
  }
  delay(500); // LDR değerini kontrol etmek için kısa bir gecikme
}