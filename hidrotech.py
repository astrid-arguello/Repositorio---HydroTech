#Librerias utilizadas 
import serial
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
import csv
from datetime import datetime 


SERIAL_PORT = "COM5" #puerto de comunicasción con el que se conecta el circuito
BAUD_RATE = 9600  #Velocidad de transmisión de datos
MAX_POINTS = 50  #Define un limite o tamaño maximo para una coleccion de datos

TDS_CONTAMINATION_THRESHOLD = 500 # Umbral de contaminación (Valor fijo)

data_buffer = deque([0] * MAX_POINTS, maxlen=MAX_POINTS)
ser = None
update_id = None
contamination_label = None 

is_logging = False
log_file = None
log_writer = None 

def toggle_logging():
    global is_logging, log_file, log_writer
    
    if not ser or not ser.is_open:
        messagebox.showwarning("Advertencia", "Debe estar conectado para iniciar el registro.")
        return

    if not is_logging:
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt", 
            filetypes=[("Archivos de Texto (Log Ordenado)", ".txt"), ("Todos los Archivos", ".*")],
            initialfile=f"TDS_Log_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        if filename:
            try:
                log_file = open(filename, "w", newline="", encoding='utf-8') 

                # 🔥 NUEVO: ENCABEZADO ORDENADO EN COLUMNAS
                log_file.write(f"{'Fecha':<15}{'Hora':<20}{'Valor TDS (ppm)':<20}{'Contaminación':<15}\n")

                log_writer = True  # Solo para indicar que está activo
                
                is_logging = True
                log_btn.config(text="◼ Detener Log (Activo)", style="Red.TButton")
                status_label.config(text=f"✅ Log Iniciado: {filename.split('/')[-1]}", foreground="#010B15") 
            except Exception as e:
                messagebox.showerror("Error", f"Fallo al iniciar el log: {e}")
                is_logging = False
                log_file = None
                log_writer = None
    else:
        if log_file:
            log_file.close()
        
        is_logging = False
        log_btn.config(text="▶ Iniciar Log", style="TButton")
        status_label.config(text="Log detenido.", foreground="gray")
        

def start_serial_connection():
    global ser, update_id
    
    if update_id:
        root.after_cancel(update_id)

    if ser and ser.is_open:
        try: ser.close()
        except: pass

    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        ser.flushInput()
        status_label.config(text=f"✅ Conectado a *{SERIAL_PORT}* @ {BAUD_RATE}", foreground="green")
        update_id = root.after(100, update_plot)
    except serial.SerialException as e:
        status_label.config(text=f" ❌ Error: No se pudo conectar a {SERIAL_PORT}. Verifica el cable y el puerto.", foreground="red")
        print(f"Error de conexión serial: {e}")

def stop_serial_connection():
    global ser, update_id

    if update_id:
        root.after_cancel(update_id)
        update_id = None
        
    if is_logging:
        toggle_logging() 

    if ser and ser.is_open:
        try:
            ser.close()
            status_label.config(text="🔌 Desconectado", foreground="orange")
        except:
            pass
            

def exit_program():
    stop_serial_connection() 
    root.quit()                
    root.destroy()           

def read_serial_data():
    if ser and ser.is_open and ser.in_waiting > 0:
        try:
            data_lines = ser.readlines() 
            
            for line_bytes in reversed(data_lines):
                try:
                    line = line_bytes.decode('utf-8').strip()
                    if not line: continue
                    tds_str = line.split('=')[-1].split(',')[0].strip()
                    tds = float(tds_str)
                    return tds 
                except (IndexError, ValueError):
                    continue 
        except Exception as e:
            print(f"Error durante la lectura serial: {e}")
            ser.close()
            stop_serial_connection()
            
    return None


def update_plot():
    global update_id

    tds_value = read_serial_data()

    if tds_value is not None:
        data_buffer.append(tds_value)

        # 🔥 Línea solicitada: solo un valor mostrado
        value_label.config(text=f"TDS Actual: {tds_value:.2f} ppm")

        is_contaminated = tds_value >= TDS_CONTAMINATION_THRESHOLD
        
        fg_alert = "#D9534F" if is_contaminated else "#5CB85C" 
        text_alert = f"🚨 ¡AGUA CONTAMINADA! (Umbral {TDS_CONTAMINATION_THRESHOLD} ppm)" if is_contaminated else "✅ Agua Segura. Nivel TDS Aceptable."
        font_style = "bold" if is_contaminated else "normal"
        
        contamination_label.config(
            text=text_alert,
            foreground=fg_alert, 
            font=("Arial", 16, font_style) 
        )

        # 🔥 NUEVO: LOG ORDENADO EN COLUMNAS
        if is_logging and log_writer:
            fecha = datetime.now().strftime("%Y-%m-%d")
            hora = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            estado = "SI" if is_contaminated else "NO"

            try:
                log_file.write(
                    f"{fecha:<15}{hora:<20}{tds_value:<20.2f}{estado:<15}\n"
                )
                log_file.flush()
            except Exception as e:
                print(f"Error escribiendo en el archivo de log: {e}")

    ax.cla()
    x = range(len(data_buffer))
    data = list(data_buffer)

    ax.plot(x, data, linewidth=3, color="#131414") 
    ax.fill_between(x, data, alpha=0.15, color="#131414") 

    if data:
        ax.plot(len(data)-1, data[-1], "o", color="#131414", markersize=8, markeredgecolor="#333333", markeredgewidth=1) 
        
        ax.axhline(TDS_CONTAMINATION_THRESHOLD, color='#D9534F', linestyle='--', linewidth=1.5, alpha=0.8)
        ax.text(MAX_POINTS * 0.95, TDS_CONTAMINATION_THRESHOLD * 1.05, f'Umbral ({TDS_CONTAMINATION_THRESHOLD})', color='#D9534F', fontsize=9, ha='right')

    ax.set_title("Gráfico de Concentración de TDS (ppm)", fontsize=14)
    ax.set_xlabel("Muestras Recientes")
    ax.set_ylabel("TDS (ppm)")
    
    y_max = max(data) if data else 0
    limit_y = max(y_max * 1.2, 1024, TDS_CONTAMINATION_THRESHOLD * 1.1) 
    ax.set_ylim(0, limit_y)
    
    ax.grid(True, linestyle=":", alpha=0.6, color="#CCCCCC") 
    
    canvas.draw()
    update_id = root.after(100, update_plot)


def reset_graph():
    data_buffer.clear()
    for _ in range(MAX_POINTS):
        data_buffer.append(0)
    value_label.config(text="TDS Actual: -- ppm")
    contamination_label.config(text="Esperando datos para análisis...", foreground="gray", font=("Arial", 16, "normal"))
    

def save_csv():
    filename = filedialog.asksaveasfilename(defaultextension=".csv", 
                                             filetypes=[("CSV", "*.csv")],
                                             initialfile="TDS_Data_Buffer") 
    if filename:
        try:
            with open(filename, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Muestra", "Valor TDS (ppm)"])
                data_to_write = list(data_buffer)
                for i, val in enumerate(data_to_write):
                    writer.writerow([i, val])
            messagebox.showinfo("Éxito", f"Buffer de datos guardado en CSV.")
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al guardar archivo: {e}")


root = tk.Tk()
root.title("💧 Monitor de Calidad del Agua (TDS)")
try:
    root.iconbitmap('icono.ico') 
except tk.TclError:
    print("Advertencia: No se pudo cargar el archivo de icono 'water_icon.ico'.")

BG_COLOR = "#F7F7F7"
root.configure(bg=BG_COLOR)

style = ttk.Style()
style.theme_use("clam")
style.configure("TFrame", background=BG_COLOR)
style.configure("TLabel", background=BG_COLOR, foreground="black", font=("Arial", 11))
style.configure("TButton", font=("Arial", 11, "bold"), padding=8)
style.configure("Red.TButton", background="#D9534F", foreground="white") 
style.map("Red.TButton", background=[('active', '#C9302C')])

top_frame = ttk.Frame(root, padding=15)
top_frame.pack(fill="x")

connect_btn = ttk.Button(top_frame, text=f"🔌 Conectar ({SERIAL_PORT})", command=start_serial_connection)
disconnect_btn = ttk.Button(top_frame, text="❌ Desconectar", command=stop_serial_connection)
log_btn = ttk.Button(top_frame, text="▶ Iniciar Loggin", command=toggle_logging)
save_btn = ttk.Button(top_frame, text="💾 Guardar Buffer CSV", command=save_csv)
reset_btn = ttk.Button(top_frame, text="🔄 Reiniciar Gráfico", command=reset_graph)
exit_btn = ttk.Button(top_frame, text="🚪 Salir", command=exit_program)

connect_btn.pack(side="left", padx=(0, 5))
disconnect_btn.pack(side="left", padx=5)
log_btn.pack(side="left", padx=(15, 5)) 
save_btn.pack(side="left", padx=(15, 5)) 
reset_btn.pack(side="left", padx=5)
exit_btn.pack(side="right", padx=5)

status_label = ttk.Label(root, text="Esperando conexión...", foreground="black", anchor="center")
status_label.pack(fill="x", pady=(10, 5))

value_label = tk.Label(root, text="TDS Actual: -- ppm", font=("Arial", 20, "bold"), bg=BG_COLOR, fg="#153655", anchor="center")
value_label.pack(fill="x", pady=(0, 5))

contamination_label = tk.Label(root, text=f"Umbral de Alerta: {TDS_CONTAMINATION_THRESHOLD} ppm", foreground="black", font=("Arial", 14, "normal"), bg=BG_COLOR, anchor="center")
contamination_label.pack(fill="x", pady=(0, 15))

plt.style.use("seaborn-v0_8-whitegrid")
fig, ax = plt.subplots(figsize=(8, 4))
fig.tight_layout(pad=3.0)
ax.set_xlabel("Muestras Recientes")
ax.set_ylabel("TDS (ppm)")

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=(0, 15)) 

for widget in [value_label, contamination_label]:
    widget.configure(bg=BG_COLOR)

root.protocol("WM_DELETE_WINDOW", exit_program) 
root.mainloop()