
int pinBoton = 2 ; //Declaramos la variable Pin del botón
int pinLed = 12;  //Declaramos la variable Pin del Led

//Variables dinámicas
int estadoBoton = 0;//Estado del botón
int contador = 0;  //Contador de parpadeos

void setup (){
  //Inicializa el pin del Led como salida:
  pinMode(pinLed, OUTPUT);
  //Inicializa el pin del Botón como entrada:
  pinMode(pinBoton, OUTPUT);
}

void loop() {
  estadoBoton =digitalRead(pinBoton);

  //Verifica si el botón esta pulsado:
  if(estadoBoton == HIGH) {
    contador++;
  }
  //Si el contador es impar, enciende el LED
  if(contador % 2 == 1){
    digitalWrite(pinLed, HIGH);
  }
  //Si el contador es par, apaga el LED
  else
  {
    //Si no, lo mantiene apagado:
    digitalWrite(pinLed, LOW);
  }
}