#include <ArduinoWebsockets.h>
#include <ESP8266WiFi.h>
#define valve_1 0
#define valve_2 2
#include <Ticker.h>
#include <ArduinoQueue.h>

const char* ssid = "Tenda"; //Enter SSID
const char* password = "46213228"; //Enter Password
const char* websockets_server_host = "192.168.0.126"; //Enter server adress
const uint16_t websockets_server_port = 8765; // Enter server port

using namespace websockets;
int Minute,Sprnk,Drip,Timer;
int arr[100];
int tctr=0,timer;
Ticker blinker;
bool clos=true;
bool Timr_running=false;
long mils=0;
WebsocketsClient client;
bool connected=false ;
ArduinoQueue<String> out(10);
void onEventsCallback(WebsocketsEvent event,String data){
  if (event== WebsocketsEvent::ConnectionOpened){
    Serial.println("Connection Opened");
    tctr=0;
  }else if (event== WebsocketsEvent::ConnectionClosed){
    Serial.println("Connection Closed");
    delay(1000);
    connected=false;
  }else if (event== WebsocketsEvent::GotPing){
    //Serial.println("Got pings");
  }else if (event== WebsocketsEvent::GotPong){
    //Serial.println("Got pongs");
  } 
}
void Connect_websocket()
{
   while(!connected){
     connected = client.connect(websockets_server_host, websockets_server_port, "/target");
     if(connected) {
              client.send("0");
          } else {
              Serial.println("Not Connected!");
               delay(5000);
          }
     client.onMessage([&](WebsocketsMessage message) {
        process_data(message.data());
    });
     client.onEvent(onEventsCallback);
    }
    client.poll();
}
void setup() {
    pinMode(valve_1,OUTPUT);
    pinMode(valve_2,OUTPUT);
    Serial.begin(115200);
    // Connect to wifi
    WiFi.begin(ssid, password);
    
    for(int i = 0; i < 10 && WiFi.status() != WL_CONNECTED; i++) {
        Serial.print(".");
        delay(1000);
    }
    
    if(WiFi.status() != WL_CONNECTED) {
        Serial.println("No Wifi!");
        return;
    }
    Serial.println("Connected to Wifi, Connecting to server.");
    blinker.attach(60, inc_min);
    Connect_websocket();
}
void loop() {   
  if(connected){  
    if(client.available()) {
        client.poll();
    }
    if(!(out.isEmpty())){
    client.send(out.dequeue());
    }
  }
  else
  Connect_websocket();
}
void process_data(String str)
{
    Serial.println("Recieving Data:"+str);
    if(str[0]=='4')
       if(Timr_running){
       Timr_running=false;
       out.enqueue("1 2 0");
       Serial.println("Timer Force quit");
       }
       if(str[2]=='1'&&str[4]=='1')
           control_val("direct control",valve_1,HIGH);
       else if(str[2]=='1'&&str[4]=='0')
           control_val("direct control",valve_1,LOW);
       else if(str[2]=='2'&&str[4]=='1')
           control_val("direct control",valve_2,HIGH);
       else if(str[2]=='2'&&str[4]=='0')
           control_val("direct control",valve_2,LOW);   
   if(str[0]=='1')
       conv_array(str.substring(2));  
   if(str[0]=='2'){
       Sprnk=int(str[2]-'0');
       Drip=int(str[4]-'0');  
       Serial.println(Sprnk);
       Serial.println(Drip);
   }  
   if(str[0]=='3')
       ESP.restart();  
   if(str[0]=='5'){
       Minute=(str.substring(2)).toInt();   
       Serial.println("Time Updated:"+String(Minute));
    }
    if(str[0]=='6'){
      tctr=0;
      out.enqueue("0");     
    }
}
void control_val(String source,int valve,bool op)
{
  Serial.print("valve:");
  Serial.print(valve);
  Serial.print((op)?"  High":"  Low");
  Serial.println("   by "+source);
  out.enqueue("1 1 "+String(valve)+" "+String(op)+" "+source);
  digitalWrite(valve,op);
}
void inc_min()
{
  Minute++; 
  //Serial.println("Minute:"+String(Minute));
  if(Minute==60*24)
   { 
      Minute=0;
   }
   if(!Timr_running){
        for(int i=0;i<tctr;i++)
       {
          if (arr[i]==Minute)
          {
            Serial.println("Timer"+String(arr[i]));
            out.enqueue("1 2 "+String(arr[i]));
            Timr_running=true;
            Timer=0;
            control_val("timer",valve_1,HIGH); 
            if(Timer==Sprnk){
               control_val("timer",valve_1,LOW);
               control_val("timer",valve_2,HIGH);
            }
          }
       }
   }
   else{
      Timer++;
      Serial.println("Timer:"+String(Timer)+":"+String(Sprnk)+":"+String(Drip));
      if(Timer==Sprnk){
         control_val("timer",valve_1,LOW);
         control_val("timer",valve_2,HIGH);
      }
      if(Timer>=Sprnk+Drip){
        control_val("timer",valve_2,LOW);
        Timr_running=false;
        out.enqueue("1 2 0");
      }
   }
   
}
void conv_array(String str)
{
   if(str.length()<=2)
   return;
   Serial.println("Timers Set");
   Serial.flush();
   String tmp;
   for(int i=0;i<str.length();i++)
      { 
        if(str[i]==' '||str[i]==';')
           {
            if(tmp.toInt()>0){
              arr[tctr++]=tmp.toInt();
              Serial.println(":"+tmp);
              tmp="";
              i++;
            }
           }
         tmp+=str[i];  
      }
   Serial.println("Timers");
   for (int i=0;i<tctr;i++)
   Serial.println(arr[i]);   
}
