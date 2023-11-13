#importerer biblioteker
import serial
import time
import customtkinter
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import matplotlib.ticker as ticker

#Setter startverdier for appearance og color theme
customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("green")


#Appfunksjonen. Dette er hovedsaklig selve programmet, og blir kalt fra nederste linje i koden når koden kjøres.
class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        #Setter riktig kommunikasjonsport og baud rate
        self.ser = serial.Serial("/dev/cu.usbserial-0001", 500000)
        
        #Noen startverdier. Value_counter er laget for å vite når det er mange nok verdier i listen dataList til å kunne regne ut gjennomsnittsfart.
        self.value_counter = 0
        self.value_counter2 = 0
        self.limListx = 40
        
        # Konfigurerer størrelsen på appvinduet og tittel
        self.geometry(f"{1100}x{600}")
        self.title("Docking Interface")
        
        #Bestemmer hvilke av radene og kolonnene som skal justeres i henhold til det som puttes i cellene
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2, 3), weight=1)
        
        #Sidebar for å ha utseende-menyer i
        self.side_ramme = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.side_ramme.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.side_ramme.grid_rowconfigure(4, weight=1)

        #Lager meny i sidebar for å kunne skifte dark/light
        self.appearance_mode_label = customtkinter.CTkLabel(self.side_ramme, text="TEMA:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.side_ramme, values=["Light", "Dark"], command=self.change_appearance_mode_event) #Kaller funksjonen change_appearance_mode_event hvis man velger en verdi i menyen 
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))
        
        #Meny i sidebar for skalering av sidebar
        self.scaling_label = customtkinter.CTkLabel(self.side_ramme, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(self.side_ramme, values=["80%", "90%", "100%", "110%", "120%"], command=self.change_scaling_event) #Kaller funksjonen change_scaling_event hvis man velger en verdi i menyen 
        self.scaling_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))
        
        #Setter defaultverdier for menyene til Dark og 100%
        self.appearance_mode_optionemenu.set("Dark")
        self.scaling_optionemenu.set("100%")

        #Lager en hovedramme der avstand og fart skal vises
        self.hoved_ramme = customtkinter.CTkFrame(self, fg_color="transparent")
        self.hoved_ramme.grid(row=0, column=1, padx=(20, 0), pady=(20, 10), sticky="nsew")
        self.hoved_ramme.grid_columnconfigure(0, weight=1)
        self.hoved_ramme.grid_rowconfigure(10, weight=0)
        
        #Lager en inforamme inne i hovedrammen
        self.INFO_ramme = customtkinter.CTkFrame(self.hoved_ramme)  
        self.INFO_ramme.grid(row=1, column=0, padx=(20, 20), pady=(2, 0), sticky="nsew")
        
        #Lager en tekst som skal vises inne i inforammen i hovedrammen. Denne teksten skal inneholde avstand og fart
        self.INFO_label1 = customtkinter.CTkLabel(self.hoved_ramme, text="", anchor="w", font=customtkinter.CTkFont(size=40, weight="bold"))
        self.INFO_label1.grid(row=1, column=0, padx=20, pady=(10, 100))
        
        #Lager en tråd avstand_thread som vi starter. Denne kjører fortsetter å kjøre mens datamaskinen utfører resten av koden.
        #Tråden kaller på funksjonen hent_avstand_tall
        avstand_thread = threading.Thread(target=self.hent_avstand_tall, args=(self.INFO_label1, self.ser))
        avstand_thread.daemon = True
        avstand_thread.start() 

        #Oppretter en liste der datapunktene skal lagres
        self.dataList = []
        
        #Oppretter en figur med subplot. Suplotet er akser på figuren. 
        self.fig1 = Figure(figsize=(10, 7.3), dpi=70) #Dots per inch
        self.ax1 = self.fig1.add_subplot(111)
        
        #Lager et lerret i appen til å vise figuren på.
        self.canvas1 = FigureCanvasTkAgg(self.fig1, master=self)
        self.canvas_widget = self.canvas1.get_tk_widget()
        self.canvas_widget.grid(row=3, column=1, pady=(10,30))
        
        #Definerer en animasjonstråd og kjører denne. Tråden kaller på funksjonen run_animation.
        self.animation_thread = threading.Thread(target=self.run_animation)
        self.animation_thread.daemon = True
        self.animation_thread.start()
        
    
    #Denne funksjonen kaller på funksjonen animate med jevne mellomrom
    def run_animation(self):
        self.ani = animation.FuncAnimation(self.fig1, self.animate, frames=100, fargs=(self.ser,), interval=40) #Oppdaterer jevnlig fig1 til å inneholde ny versjon av ax1
    
        
    def animate(self, i, ser):
        self.dataList = self.dataList[-self.limListx:] #Henter listen "dataList" og slicer den - kutter i praksis ut siste verdi, etter en viss mengde verdie

        self.ax1.clear() #Fjerner verdiene som evt er i ax1 fra før
        
        valid_data = [val if val is not None else float('nan') for val in self.dataList]  #Konverter None til NaN
    
        self.ax1.plot(range(len(valid_data)), valid_data, color='b')  #Plotter de gyldige dataene i subplotet til fig1, ax1
        self.ax1.fill_between(range(len(valid_data)), 0, valid_data, alpha=0.2, color='b')  #Fyller området under de gyldige dataene

        #Aksegrenser, tittel, navn på y-akse og rutenett
        self.ax1.set_ylim([0, 50])
        self.ax1.set_xlim([0, self.limListx])
        self.ax1.set_title("Avstand til båt ($cm$)", fontsize=20)
        self.ax1.set_ylabel("Avstand ($cm$)")
        self.ax1.grid()
        self.ax1.xaxis.set_major_locator(ticker.MaxNLocator(4))
        self.ax1.yaxis.set_major_locator(ticker.MaxNLocator(5))
        
        
    #Blir kalt på av avstand-tråden.    
    def hent_avstand_tall(self, INFO_label1, ser):
        while True: #Starter en "evig" while-løkke
            avstandsverdi = self.avstand(ser) #Finner avstandsverdien ved å kalle på funksjonen avstand og lagrer returverdien i variabelen avstandsverdi
            fart = "0" #Startverdi
            self.value_counter += 1 #Øker value_counter med 1 for hver gang løkken repeteres
            if self.value_counter == 1: 
                avstandsverdi = str(avstandsverdi)
                INFO_label1.configure(text=f" Avstand: {avstandsverdi} cm. \n Fart: cm/s") #For å alltid vise frem første verdi for avstand, uansett om farten ikke er klar til å vises enda
            elif self.value_counter % 3 == 0: #Bestemmer hvor ofte tall-avstanden skal oppdateres.
                if avstandsverdi is None:
                    avstandsverdi = "0"
                avstandsverdi = str(avstandsverdi)
                if len(self.dataList) >= 7: #Når listen har minst 7 verdier, kan vi regne ut gjennomsnittsfarten
                    self.value_counter2 += 1
                    if all(element is not None for element in self.dataList[-1:-7:-1]):
                        delta_avstand = ((self.dataList[-1] + self.dataList[-2])/2 - (self.dataList[-5] + self.dataList[-6])/2)
                        fart = -delta_avstand / (0.04 * 4 * 4 * 100)
                        fart_cms = str(int((fart) * 100)) #Valgte cm/s fordi bevegelsen skjer sakte i prototypen, og avstanden er vist i cm
                        #fart_knop = str(int(fart * 1.943844)) #Hvis man vil vise farten i knop
                        if self.value_counter2 % 4 == 0: 
                            INFO_label1.configure(text=f" Avstand: {avstandsverdi} cm. \n Fart: {fart_cms} cm/s")
                        else:
                            pass
                    else:
                        if self.value_counter2 % 4 == 0:
                            INFO_label1.configure(text=f" Avstand: {avstandsverdi} cm. \n Fart: cm/s") 
                else:
                    if self.value_counter2 % 4 == 0:
                        INFO_label1.configure(text=f" Avstand: {avstandsverdi} cm. \n Fart: cm/s")
            time.sleep(0.04) #Venter i 0.04 sekunder etter hver iterasjon av løkken
            
            
    #Blir kalt på av hent_avstand_tall - funksjonen
    def avstand(self, ser): 
        ser.write(b'g') #Skriver 'g' i seriellporten vi har valgt tidligere i koden. ESP-en har fått beskjed om å sende avstandsverdi når den får tegnet g.
        arduinoData_string = ser.readline().decode('ascii') #Leser infoen/datapunktet vi får fra ESP-en
        try:
            arduinoData_int = (int(arduinoData_string)) - 5 #-5 fordi ESP-en er plassert 5cm bak der båten skal legge til merda
            self.dataList.append(arduinoData_int) #Legger til verdien fra ESP-en i listen dataList
            return arduinoData_int #Returnerer avstandsverdien til variabelen avstandsverdi i funksjonen hent_avstand_tall
        except ValueError: #Hvis vi får meldingen ValueError skal funksjonen legge til verdien None (slik at grafen ikke "stopper opp"), men ikke returnere noe til hent_avstand_tall
            self.dataList.append(None)
            pass
    
    #Endrer utseende (dark/light) hvis man velger dette i menyen i side-rammen
    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)
    
    #Endrer skaleringen av siderammen hvis man velger dette i menyen i side-rammen
    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)


#Setter i gang appen når man kjører koden.
if __name__ == "__main__":
    app = App()
    app.mainloop()