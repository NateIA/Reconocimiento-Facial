import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import sqlite3
import os
import cv2
import face_recognition
import numpy as np
import pandas as pd
from datetime import datetime

# ------------------------------------------------------------
# Funciones de inicialización y logging
# ------------------------------------------------------------
def create_logs_table():
    """
    Conecta a la base de datos existente (attendance.db) y crea
    únicamente la tabla 'logs' si no existe.
    """
    conn = sqlite3.connect("database/attendance.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            action   TEXT NOT NULL,
            date     TEXT NOT NULL,
            time     TEXT NOT NULL,
            grade    TEXT,
            section  TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_event(username, action, grade, section):
    """
    Inserta un registro en la tabla 'logs' con fecha, hora, usuario, acción, grado y sección.
    """
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")
    conn = sqlite3.connect("database/attendance.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO logs (username, action, date, time, grade, section)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (username, action, date_str, time_str, grade, section))
    conn.commit()
    conn.close()

# ------------------------------------------------------------
# Función para volver al login principal
# ------------------------------------------------------------
def run_login():
    create_logs_table()  # Asegura que exista la tabla 'logs'
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()

# ------------------------------------------------------------
# Ventana de Login
# ------------------------------------------------------------
class LoginApp:
    def __init__(self, master):
        self.master = master
        master.title("Login - Sistema de Asistencia")
        master.geometry("750x600")
        self.create_menu()

        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "assets", "icon.ico")
        bg_path = os.path.join(script_dir, "assets", "background_image.png")

        try:
            master.iconbitmap(icon_path)
        except Exception:
            pass

        try:
            self.bg_image = ImageTk.PhotoImage(file=bg_path)
            bg_label = tk.Label(master, image=self.bg_image)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception:
            pass

        self.label_title = tk.Label(master, text="Inicio de Sesión", font=("Helvetica", 16), bg='#add8e6')
        self.label_title.pack(pady=20)

        self.label_user = tk.Label(master, text="Usuario:", bg='#add8e6')
        self.label_user.pack(pady=(10,0))
        self.entry_user = tk.Entry(master)
        self.entry_user.pack()

        self.label_pass = tk.Label(master, text="Contraseña:", bg='#add8e6')
        self.label_pass.pack(pady=(10,0))
        self.entry_pass = tk.Entry(master, show="*")
        self.entry_pass.pack()

        self.login_button = tk.Button(master, text="Iniciar Sesión", width=20, command=self.login)
        self.login_button.pack(pady=20)

    def create_menu(self):
        menubar = tk.Menu(self.master)
        opciones = tk.Menu(menubar, tearoff=0)
        opciones.add_command(label="Cerrar sesión", command=self.master.destroy)
        opciones.add_command(label="Volver", command=lambda: None)  # No aplica en login
        menubar.add_cascade(label="Opciones", menu=opciones)
        self.master.config(menu=menubar)

    def login(self):
        username = self.entry_user.get()
        password = self.entry_pass.get()

        conn = sqlite3.connect("database/attendance.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, assigned_grade, assigned_section FROM users WHERE username=? AND password=?",
            (username, password)
        )
        result_users = cursor.fetchone()
        cursor.execute(
            "SELECT role FROM admin WHERE username=? AND password=?",
            (username, password)
        )
        result_admin = cursor.fetchone()
        conn.close()

        if result_users or result_admin:
            if result_users:
                role, grade, section = result_users
            else:
                role = result_admin[0]
                grade, section = None, None

            # Registro en logs de inicio de sesión
            log_event(username, "Iniciar sesión", grade if grade else "", section if section else "")

            messagebox.showinfo("Éxito", f"Bienvenido, {username} ({role})")
            self.master.destroy()

            if role == "docente":
                root = tk.Tk()
                app = DocenteMenu(root, username)
                root.mainloop()
            elif role == "admin":
                root = tk.Tk()
                app = RegisterTeacherApp(root)
                root.mainloop()
            else:
                messagebox.showerror("Error", "Rol no reconocido")
        else:
            messagebox.showerror("Error", "Credenciales inválidas")

# ------------------------------------------------------------
# Ventana Menú Docente
# ------------------------------------------------------------
class DocenteMenu:
    def __init__(self, master, username):
        self.master = master
        self.username = username
        master.title("Menú Docente")
        master.geometry("750x600")
        self.create_menu()

        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "assets", "icon.ico")
        bg_path = os.path.join(script_dir, "assets", "background_image.png")

        try:
            master.iconbitmap(icon_path)
        except Exception:
            pass

        try:
            self.bg_image = ImageTk.PhotoImage(file=bg_path)
            bg_label = tk.Label(master, image=self.bg_image)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception:
            pass

        tk.Label(master, text="Menú Docente", font=("Helvetica", 16), bg='#d0f0c0').pack(pady=20)

        btn_register = tk.Button(master, text="Registrar Alumnos", width=25, command=self.open_register_students)
        btn_register.pack(pady=10)

        btn_attendance = tk.Button(master, text="Tomar Asistencia", width=25, command=self.open_take_attendance)
        btn_attendance.pack(pady=10)

    def create_menu(self):
        menubar = tk.Menu(self.master)
        opciones = tk.Menu(menubar, tearoff=0)
        opciones.add_command(label="Cerrar sesión", command=self._logout)
        opciones.add_command(label="Volver", command=self._go_back_to_login)
        menubar.add_cascade(label="Opciones", menu=opciones)
        self.master.config(menu=menubar)

    def _logout(self):
        self.master.destroy()
        run_login()

    def _go_back_to_login(self):
        self.master.destroy()
        run_login()

    def open_register_students(self):
        self.master.destroy()
        root = tk.Tk()
        RegisterStudentApp(root, self.username)
        root.mainloop()

    def open_take_attendance(self):
        self.master.destroy()
        root = tk.Tk()
        TakeAttendanceApp(root, self.username)
        root.mainloop()

# ------------------------------------------------------------
# Ventana Registro de Docentes (Admin)
# ------------------------------------------------------------
class RegisterTeacherApp:
    def __init__(self, master):
        self.master = master
        master.title("Registrar Docente")
        master.geometry("750x600")
        self.create_menu()

        master.configure(bg='lightblue')
        tk.Label(master, text="Registro de Docente", font=("Helvetica", 16), bg='lightblue').pack(pady=20)

        tk.Label(master, text="Usuario:", bg='lightblue').pack(pady=(10,0))
        self.username_entry = tk.Entry(master)
        self.username_entry.pack()

        tk.Label(master, text="Contraseña:", bg='lightblue').pack(pady=(10,0))
        self.password_entry = tk.Entry(master, show="*")
        self.password_entry.pack()

        tk.Label(master, text="Grado:", bg='lightblue').pack(pady=(10,0))
        self.grade_entry = tk.Entry(master)
        self.grade_entry.pack()

        tk.Label(master, text="Sección:", bg='lightblue').pack(pady=(10,0))
        self.section_entry = tk.Entry(master)
        self.section_entry.pack()

        self.register_btn = tk.Button(master, text="Registrar", width=20, command=self.register_teacher)
        self.register_btn.pack(pady=20)

    def create_menu(self):
        menubar = tk.Menu(self.master)
        opciones = tk.Menu(menubar, tearoff=0)
        opciones.add_command(label="Cerrar sesión", command=self._logout)
        opciones.add_command(label="Volver", command=self._go_back_to_login)
        menubar.add_cascade(label="Opciones", menu=opciones)
        self.master.config(menu=menubar)

    def _logout(self):
        self.master.destroy()
        run_login()

    def _go_back_to_login(self):
        self.master.destroy()
        run_login()

    def register_teacher(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        grade = self.grade_entry.get()
        section = self.section_entry.get()

        if not (username and password and grade and section):
            messagebox.showerror("Error", "Todos los campos son obligatorios.")
            return

        conn = sqlite3.connect("database/attendance.db")
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, role, assigned_grade, assigned_section) VALUES (?, ?, ?, ?, ?)",
                (username, password, "docente", grade, section)
            )
            conn.commit()
            messagebox.showinfo("Éxito", "Docente registrado correctamente.")
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.grade_entry.delete(0, tk.END)
            self.section_entry.delete(0, tk.END)
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "El nombre de usuario ya existe.")
        finally:
            conn.close()

# ------------------------------------------------------------
# Ventana Registro de Estudiantes
# ------------------------------------------------------------
class RegisterStudentApp:
    def __init__(self, master, username):
        self.master = master
        self.username = username

        master.title("Registro de Estudiantes")
        master.geometry("750x600")
        self.create_menu()

        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "assets", "icon.ico")
        bg_path = os.path.join(script_dir, "assets", "background_image.png")
        try:
            master.iconbitmap(icon_path)
        except Exception:
            pass

        try:
            self.bg_image = ImageTk.PhotoImage(file=bg_path)
            bg_label = tk.Label(master, image=self.bg_image)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception:
            pass

        self.title = tk.Label(master, text="Registrar Alumno", font=("Helvetica", 16), bg='#d0f0c0')
        self.title.pack(pady=20)

        tk.Label(master, text="Nombre:", bg='#d0f0c0').pack(pady=(10,0))
        self.name_entry = tk.Entry(master)
        self.name_entry.pack()

        tk.Label(master, text="Código del alumno:", bg='#d0f0c0').pack(pady=(10,0))
        self.code_entry = tk.Entry(master)
        self.code_entry.pack()

        tk.Label(master, text="Grado:", bg='#d0f0c0').pack(pady=(10,0))
        self.grade_entry = tk.Entry(master)
        self.grade_entry.pack()

        tk.Label(master, text="Sección:", bg='#d0f0c0').pack(pady=(10,0))
        self.section_entry = tk.Entry(master)
        self.section_entry.pack()

        self.capture_btn = tk.Button(master, text="Tomar Foto con Cámara", width=25, command=self.capture_photo)
        self.capture_btn.pack(pady=(15,5))

        self.upload_btn = tk.Button(master, text="Subir Foto desde Archivo", width=25, command=self.upload_photo)
        self.upload_btn.pack(pady=5)

        self.register_btn = tk.Button(master, text="Registrar", width=20, command=self.register_student)
        self.register_btn.pack(pady=20)

        self.photo_data = None

    def create_menu(self):
        menubar = tk.Menu(self.master)
        opciones = tk.Menu(menubar, tearoff=0)
        opciones.add_command(label="Cerrar sesión", command=self._logout)
        opciones.add_command(label="Volver", command=self._go_back_to_menu_docente)
        menubar.add_cascade(label="Opciones", menu=opciones)
        self.master.config(menu=menubar)

    def _logout(self):
        self.master.destroy()
        run_login()

    def _go_back_to_menu_docente(self):
        self.master.destroy()
        root = tk.Tk()
        DocenteMenu(root, self.username)
        root.mainloop()

    def register_student(self):
        name = self.name_entry.get()
        code = self.code_entry.get()
        grade = self.grade_entry.get()
        section = self.section_entry.get()

        if not (name and code and grade and section):
            messagebox.showerror("Error", "Todos los campos son obligatorios.")
            return

        if self.photo_data is None:
            messagebox.showerror("Error", "Debes subir una foto o tomar una con la cámara.")
            return

        conn = sqlite3.connect("database/attendance.db")
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO students (student_code, name, grade, section, photo) VALUES (?, ?, ?, ?, ?)",
                (code, name, grade, section, self.photo_data)
            )
            conn.commit()
            log_event(self.username, "Agregar alumno", grade, section)
            messagebox.showinfo("Éxito", "Alumno registrado con foto guardada en la base de datos.")
            self.name_entry.delete(0, tk.END)
            self.code_entry.delete(0, tk.END)
            self.grade_entry.delete(0, tk.END)
            self.section_entry.delete(0, tk.END)
            self.photo_data = None
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "El código del alumno ya existe.")
        finally:
            conn.close()

    def capture_photo(self):
        code = self.code_entry.get()
        if not code:
            messagebox.showerror("Error", "Debes ingresar el código del alumno antes de tomar la foto.")
            return

        cap = cv2.VideoCapture(0)
        messagebox.showinfo("Foto", "Se abrirá la cámara. Presiona 's' para guardar la imagen del alumno.")

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow("Captura de Foto - Presiona 's' para guardar", frame)
            key = cv2.waitKey(1)
            if key == ord('s'):
                ret2, buf = cv2.imencode('.jpg', frame)
                if ret2:
                    self.photo_data = buf.tobytes()
                    messagebox.showinfo("Foto guardada", "Foto capturada y lista para registrar.")
                    self.register_student()
                break
        cap.release()
        cv2.destroyAllWindows()

    def upload_photo(self):
        file_path = filedialog.askopenfilename(filetypes=[("JPG/PNG Files", "*.jpg *.png")])
        if file_path:
            with open(file_path, 'rb') as f:
                self.photo_data = f.read()
            messagebox.showinfo("Foto cargada", "Foto cargada y lista para registrar.")
            self.register_student()

# ------------------------------------------------------------
# Ventana Tomar Asistencia
# ------------------------------------------------------------
class TakeAttendanceApp:
    def __init__(self, master, username):
        self.master = master
        self.username = username

        master.title("Tomar Asistencia - Reconocimiento Facial")
        master.geometry("750x600")
        self.create_menu()

        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "assets", "icon.ico")
        bg_path = os.path.join(script_dir, "assets", "background_image.png")

        try:
            master.iconbitmap(icon_path)
        except Exception:
            pass

        try:
            self.bg_image = ImageTk.PhotoImage(file=bg_path)
            bg_label = tk.Label(master, image=self.bg_image)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception:
            pass

        tk.Label(master, text=f"Usuario: {username}", font=("Helvetica", 14), bg='#ffffe0').pack(pady=20)

        self.btn_upload = tk.Button(master, text="Subir Imagen o Video", width=25, command=self.upload_file)
        self.btn_upload.pack(pady=5)

        self.btn_take_photo = tk.Button(master, text="Tomar Foto (Asistencia)", width=25, command=self.take_photo)
        self.btn_take_photo.pack(pady=5)

        self.btn_record_video = tk.Button(master, text="Grabar Video (Asistencia)", width=25, command=self.record_video)
        self.btn_record_video.pack(pady=5)

        self.btn_export = tk.Button(master, text="Exportar Asistencia del Día", width=25, command=self.export_today_attendance)
        self.btn_export.pack(pady=5)

        self.display_label = tk.Label(master)
        self.display_label.pack(pady=10)

        self.text = tk.Text(master, height=10, width=90)
        self.text.pack(pady=10)

        self.dataset_dir = os.path.join(script_dir, "dataset")
        if not os.path.exists(self.dataset_dir):
            messagebox.showerror("Error", f"No existe la carpeta de imágenes de referencia: {self.dataset_dir}")

        self.known_face_encodings = []
        self.known_face_names = []
        self.load_known_faces()

        self.grade, self.section = self.get_teacher_grade_section()
        self.recorded_video_path = None

    def create_menu(self):
        menubar = tk.Menu(self.master)
        opciones = tk.Menu(menubar, tearoff=0)
        opciones.add_command(label="Cerrar sesión", command=self._logout)
        opciones.add_command(label="Volver", command=self._go_back_to_menu_docente)
        menubar.add_cascade(label="Opciones", menu=opciones)
        self.master.config(menu=menubar)

    def _logout(self):
        self.master.destroy()
        run_login()

    def _go_back_to_menu_docente(self):
        self.master.destroy()
        root = tk.Tk()
        DocenteMenu(root, self.username)
        root.mainloop()

    def get_teacher_grade_section(self):
        conn = sqlite3.connect("database/attendance.db")
        cursor = conn.cursor()
        cursor.execute("SELECT assigned_grade, assigned_section FROM users WHERE username=?", (self.username,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0], result[1]
        else:
            return "", ""

    def load_known_faces(self):
        self.known_face_encodings = []
        self.known_face_names = []
        for filename in os.listdir(self.dataset_dir):
            if filename.lower().endswith((".jpg", ".png")):
                path = os.path.join(self.dataset_dir, filename)
                image = face_recognition.load_image_file(path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    self.known_face_encodings.append(encodings[0])
                    name = os.path.splitext(filename)[0]
                    self.known_face_names.append(name)

    def upload_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Archivos de imagen y video", "*.jpg *.png *.mp4 *.avi")])
        if not file_path:
            return
        ext = os.path.splitext(file_path)[1].lower()
        if ext in [".jpg", ".png"]:
            self.process_image(file_path)
            self.show_image(file_path)
        elif ext in [".mp4", ".avi"]:
            self.process_video(file_path)
            self.recorded_video_path = file_path
            self.text.insert(tk.END, f"Video cargado: {file_path}\n")
            self.show_video_controls()
        else:
            messagebox.showerror("Error", "Formato no soportado.")

    def process_image(self, image_path):
        image = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image)
        face_encodings = face_recognition.face_encodings(image, face_locations)

        presentes = set()
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.5)
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if matches[best_match_index]:
                presentes.add(self.known_face_names[best_match_index])

        if presentes:
            self.register_attendance(presentes)
            self.text.insert(tk.END, f"Asistencia tomada: {', '.join(presentes)}\n")
        else:
            self.text.insert(tk.END, "No se reconocieron rostros conocidos.\n")

    def process_video(self, video_path):
        cap = cv2.VideoCapture(video_path)
        presentes = set()

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            rgb_frame = frame[:, :, ::-1]
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.5)
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    presentes.add(self.known_face_names[best_match_index])

        cap.release()

        if presentes:
            self.register_attendance(presentes)
            self.text.insert(tk.END, f"Asistencia tomada: {', '.join(presentes)}\n")
        else:
            self.text.insert(tk.END, "No se reconocieron rostros conocidos en el video.\n")

    def take_photo(self):
        cap = cv2.VideoCapture(0)
        self.text.insert(tk.END, "Abriendo cámara para tomar foto...\n")
        messagebox.showinfo("Foto", "Se abrirá la cámara. Presiona 's' para tomar la foto.")

        presentes = set()
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow("Tomar Foto - Presiona 's' para capturar", frame)
            key = cv2.waitKey(1)
            if key == ord('s'):
                temp_img_path = "temp_photo.jpg"
                cv2.imwrite(temp_img_path, frame)
                rgb_frame = frame[:, :, ::-1]
                face_locations = face_recognition.face_locations(rgb_frame)
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                for face_encoding in face_encodings:
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.5)
                    face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        presentes.add(self.known_face_names[best_match_index])
                break
        cap.release()
        cv2.destroyAllWindows()

        if presentes:
            self.register_attendance(presentes)
            self.text.insert(tk.END, f"Asistencia tomada (foto): {', '.join(presentes)}\n")
        else:
            self.text.insert(tk.END, "No se reconocieron rostros conocidos en la foto.\n")

        self.show_image(temp_img_path)

    def record_video(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        temp_video_path = os.path.join(script_dir, "temp_record.avi")

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "No se pudo abrir la cámara para grabar.")
            return

        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(temp_video_path, fourcc, 20.0, (640,480))

        messagebox.showinfo("Grabación", "Presiona 'q' para detener la grabación.")

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
            cv2.imshow('Grabando Video - Presiona q para detener', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        out.release()
        cv2.destroyAllWindows()

        self.process_video(temp_video_path)
        self.recorded_video_path = temp_video_path
        self.text.insert(tk.END, f"Video grabado: {temp_video_path}\n")
        self.show_video_controls()

    def show_image(self, image_path):
        img = Image.open(image_path)
        img = img.resize((480, 360))
        imgtk = ImageTk.PhotoImage(img)
        self.display_label.imgtk = imgtk
        self.display_label.configure(image=imgtk)

        self.clear_controls()
        btn_save = tk.Button(self.master, text="Guardar Imagen", width=20, command=lambda: self.save_file(image_path))
        btn_save.pack(pady=5)
        btn_clear = tk.Button(self.master, text="Limpiar Vista", width=20, command=self.clear_display)
        btn_clear.pack(pady=5)

    def show_video_controls(self):
        self.clear_controls()
        btn_play = tk.Button(self.master, text="Reproducir Video", width=20, command=self.play_recorded_video)
        btn_play.pack(pady=5)
        btn_save = tk.Button(self.master, text="Guardar Video", width=20, command=lambda: self.save_file(self.recorded_video_path))
        btn_save.pack(pady=5)
        btn_clear = tk.Button(self.master, text="Limpiar Vista", width=20, command=self.clear_display)
        btn_clear.pack(pady=5)

    def clear_controls(self):
        for widget in self.master.pack_slaves():
            if isinstance(widget, tk.Button) and widget not in [self.btn_upload, self.btn_take_photo, self.btn_record_video, self.btn_export]:
                widget.destroy()

    def clear_display(self):
        self.display_label.configure(image='')
        self.display_label.imgtk = None
        self.text.insert(tk.END, "Vista limpiada.\n")
        self.clear_controls()

    def save_file(self, src_path):
        if not src_path or not os.path.exists(src_path):
            messagebox.showerror("Error", "No hay archivo para guardar.")
            return
        dest_path = filedialog.asksaveasfilename(defaultextension=os.path.splitext(src_path)[1],
                                                 filetypes=[("Archivos", f"*{os.path.splitext(src_path)[1]}")])
        if dest_path:
            try:
                with open(src_path, 'rb') as fsrc, open(dest_path, 'wb') as fdst:
                    fdst.write(fsrc.read())
                messagebox.showinfo("Éxito", f"Archivo guardado en:\n{dest_path}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{e}")

    def play_recorded_video(self):
        if not self.recorded_video_path or not os.path.exists(self.recorded_video_path):
            messagebox.showerror("Error", "No hay video para reproducir.")
            return
        cap = cv2.VideoCapture(self.recorded_video_path)
        self.text.insert(tk.END, f"Reproduciendo video: {self.recorded_video_path}\n")
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            cv2.imshow("Video Grabado", frame)
            if cv2.waitKey(25) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()

    def register_attendance(self, presentes):
        # Log del evento de asistencia
        log_event(self.username, "Tomar asistencia", self.grade, self.section)

        now = datetime.now()
        fecha_str = now.strftime("%Y-%m-%d")
        hora_str = now.strftime("%H:%M:%S")

        csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "attendance_records.csv")
        df = pd.DataFrame(columns=["Nombre", "Fecha", "Hora"])
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
        for nombre in presentes:
            if not ((df["Nombre"] == nombre) & (df["Fecha"] == fecha_str)).any():
                df.loc[len(df)] = {"Nombre": nombre, "Fecha": fecha_str, "Hora": hora_str}
        df.to_csv(csv_path, index=False)

        conn = sqlite3.connect("database/attendance.db")
        cursor = conn.cursor()
        for nombre in presentes:
            cursor.execute(
                "SELECT student_code, grade, section FROM students WHERE student_code=?",
                (nombre,)
            )
            res = cursor.fetchone()
            if res:
                student_code, grade, section = res
                cursor.execute("""
                    INSERT INTO attendance (student_code, name, grade, section, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (student_code, nombre, grade, section, now.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

    def export_today_attendance(self):
        fecha_str = datetime.now().strftime("%Y-%m-%d")
        docente = self.username.replace(" ", "_")
        filename = f"Asistencia_{self.grade}_{self.section}_{docente}_{fecha_str}.csv"
        script_dir = os.path.dirname(os.path.abspath(__file__))
        export_path = os.path.join(script_dir, filename)

        conn = sqlite3.connect("database/attendance.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT student_code, name, grade, section, timestamp FROM attendance
            WHERE date(timestamp) = ?
              AND grade = ?
              AND section = ?
        """, (fecha_str, self.grade, self.section))
        records = cursor.fetchall()
        conn.close()

        if not records:
            messagebox.showinfo("Info", "No hay registros de asistencia para el día de hoy.")
            return

        df = pd.DataFrame(records, columns=["Código", "Nombre", "Grado", "Sección", "FechaHora"])
        df.to_csv(export_path, index=False)
        messagebox.showinfo("Éxito", f"Asistencia exportada a:\n{export_path}")

# ------------------------------------------------------------
# Ejecución principal
# ------------------------------------------------------------
if __name__ == "__main__":
    run_login()
