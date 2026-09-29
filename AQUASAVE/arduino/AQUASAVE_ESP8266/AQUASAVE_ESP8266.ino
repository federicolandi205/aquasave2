#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <ArduinoJson.h>

// ---------------- WIFI ----------------
const char* ssid = "TU_WIFI";
const char* password = "CONTRASEÑA";

// IP del servidor Python
const char* servidor = " http://192.168.0.100:8000/api/mediciones ";

// Identificador único del prototipo
const char* PROTOTIPO = "AQ-001";

// ------------ Pines ---------------
#define TRIG D5
#define ECHO D6

#definir LED_VERDE D1
#definir LED_AMARILLO D2
#definir LED_ROJO D7

#definir ZUMBADOR D8

// Altura del sensor respecto al agua (cm)
const float ALTURA_ARROYO = 100.0;

// Umbrales
const float NORMAL = 30;
const float ALERTA = 60;
const float PELIGRO = 85;

unsigned long ultimoEnvio = 0;

void setup() {

Serial.begin(115200);

pinMode(TRIG, SALIDA);
pinMode(ECHO, ENTRADA);

pinMode(LED_VERDE, SALIDA);
pinMode(LED_AMARILLO, SALIDA);
pinMode(LED_ROJO, SALIDA);

pinMode(ZUMBADOR, SALIDA);

WiFi.begin(ssid, contraseña);

while (WiFi.status() != WL_CONNECTED) {
delay(500);
Serial.print(".");
}

Serial.println("WiFi conectado");
}

flotar medirNivel() {

digitalWrite(TRIG, LOW);
delayMicroseconds(5);

digitalWrite(TRIG, HIGH);
delayMicroseconds(10);

digitalWrite(TRIG, LOW);

larga duracion = pulseIn(ECHO, ALTA);

flotador distancia = duracion * 0.0343 / 2;

float nivel = ALTURA_ARROYO - distancia;

si (nivel < 0)
nivel = 0;

devolver nivel;
}

String obtenerEstado(float nivel) {

si (nivel < NORMAL)
devolver "NORMAL";

if (nivel < ALERTA)
retorna "SUBIENDO";

devolver "PELIGRO";
}

void activarAlertas(float nivel) {

digitalWrite(LED_VERDE, BAJO);
digitalWrite(LED_AMARILLO, BAJO);
digitalWrite(LED_ROJO, BAJO);
noTone(ZUMBADOR);

si (nivel < NORMAL) {

digitalWrite(LED_VERDE, HIGH);
}

else if (nivel < ALERTA) {

digitalWrite(LED_AMARILLO, HIGH);

tone(BUZZER, 1200);
delay(150);
noTone(BUZZER);
delay(150);
}

demás {

digitalWrite(LED_ROJO, HIGH);

tone(BUZZER, 2500);
}
}

void enviarServidor(float nivel, String estado) {

Si (WiFi.status() != WL_CONNECTED)
regresar;

Cliente WiFi; Cliente
HTTP http;

http.begin(cliente, servidor);

http.addHeader("Content-Type", "application/json");

Documento Json estático<256> doc;

doc["prototipo"] = PROTOTIPO;
doc["nivel_cm"] = nivel;
doc["estado"] = estado;
doc["bateria"] = 100;

Cadena json;

serializarJson(doc, json);

int código = http.POST(json);

Serial.println(código);

http.end();
}

void loop() {

float nivel = medirNivel();

String estado obtener =Estado(nivel);

activarAlertas(nivel);

if (millis() - ultimoEnvio > 5000) {

enviarServidor(nivel, estado);

ultimoEnvio = millis();
}

Serial.print("Nivel: ");
Serial.print(nivel);
Serial.print(" cm Estado: ");
Serial.println(estado);

retraso(500);
}

Actividad
Añade un comentario
Nuevo comentario
Entrada Markdown: modo de edición seleccionado.
Escribir
Avance
Utiliza Markdown para dar formato a tu comentario.

