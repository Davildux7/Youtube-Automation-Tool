import threading
import queue
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox

# constants
import config
from config import WATERMARK_FILENAME

# services
from services.youtube import YoutubeProspector
from services.audio import AudioProcessor, GroqService, SRTConverter

class UnifiedApp(ctk.CTk):
    def __init__(self, video_processor):
        super().__init__()
        self.video_processor = video_processor
        
        self.title("Youtube Automation Tool")
        self.geometry("800x650")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.video_path_subtitle = ctk.StringVar()
        self.api_key = ctk.StringVar(value=os.getenv("GROQ_API_KEY", ""))
        self.msg_queue = queue.Queue() 

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=10, fill="both", expand=True)
        
        self.tab_watermark = self.tabview.add("Watermark")
        self.tab_subtitle = self.tabview.add("Whisper Subtitles")
        self.tab_prospector = self.tabview.add("YouTube Hunter")
        
        self.create_watermark_tab()
        self.create_subtitle_tab()
        self.create_prospector_tab()

        self.check_queue()

    # tab 1 - watermark
    def create_watermark_tab(self):
        frame = ctk.CTkFrame(self.tab_watermark)
        frame.pack(pady=20, padx=20, fill="both", expand=True)

        ctk.CTkLabel(frame, text="Apply Watermark (Overlay)", font=("", 16, "bold")).pack(pady=(20, 10))
        ctk.CTkLabel(frame, text=f"Select a watermark image before processing.", wraplength=400, text_color="gray").pack(pady=10)

        # watermark file selection
        self.watermark_path = ctk.StringVar(value=WATERMARK_FILENAME)
        frame_wm = ctk.CTkFrame(frame, fg_color="transparent")
        frame_wm.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(frame_wm, text="Watermark Image:").pack(side="left", padx=(0, 5))
        self.entry_wm = ctk.CTkEntry(frame_wm, textvariable=self.watermark_path, state="readonly")
        self.entry_wm.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(frame_wm, text="Select", width=80, command=self.select_watermark_file).pack(side="right")

        self.btn_watermark = ctk.CTkButton(frame, text="Select Video and Process", command=self.start_watermark_thread, height=40)
        self.btn_watermark.pack(pady=20, padx=50, fill="x")

        self.lbl_status_watermark = ctk.CTkLabel(frame, text="")
        self.lbl_status_watermark.pack(pady=5)

    def select_watermark_file(self):
        path = filedialog.askopenfilename(title="Select watermark image", filetypes=[("PNG Images", "*.png"), ("All", "*.*")])
        if path:
            self.watermark_path.set(path)
            # update watermark path on video_processor
            self.video_processor.watermark_image_path = path

    def start_watermark_thread(self):
        video_path = filedialog.askopenfilename(title="Select a video file", filetypes=(("Videos", "*.mp4 *.avi"), ("All", "*.*")))
        if not video_path:
            return

        # updates video_processor BEFORE processing
        self.video_processor.watermark_image_path = self.watermark_path.get()

        self.btn_watermark.configure(state="disabled", text="Processing...")
        self.lbl_status_watermark.configure(text="Applying overlay... (This may take a while)", text_color="blue")
        threading.Thread(target=self.process_watermark_background, args=(video_path,), daemon=True).start()

    def process_watermark_background(self, video_path):
        success, error = self.video_processor.apply_watermark(video_path)
        if success:
            self.msg_queue.put(("watermark_ok", "Completed successfully!"))
        else:
            self.msg_queue.put(("watermark_error", str(error)))

    # tab 2 - subtitles
    def create_subtitle_tab(self):
        main_frame = ctk.CTkFrame(self.tab_subtitle)
        main_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        frame_api = ctk.CTkFrame(main_frame, fg_color="transparent")
        frame_api.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(frame_api, text="Groq API Key:").pack(anchor="w")
        self.entry_key = ctk.CTkEntry(frame_api, textvariable=self.api_key, show="*")
        self.entry_key.pack(fill="x", pady=(5,0))

        frame_file = ctk.CTkFrame(main_frame, fg_color="transparent")
        frame_file.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(frame_file, text="Video File:").pack(anchor="w")
        
        frame_input = ctk.CTkFrame(frame_file, fg_color="transparent")
        frame_input.pack(fill="x", pady=5)
        self.entry_path = ctk.CTkEntry(frame_input, textvariable=self.video_path_subtitle, state='readonly')
        self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(frame_input, text="Search", width=80, command=self.browse_subtitle_video).pack(side="right")

        self.btn_convert = ctk.CTkButton(main_frame, text="GENERATE SUBTITLES", command=self.start_subtitle_thread, state="disabled", height=40)
        self.btn_convert.pack(pady=15, padx=50, fill="x")
        
        self.progress = ctk.CTkProgressBar(main_frame, mode='indeterminate')
        self.lbl_status_subtitle = ctk.CTkLabel(main_frame, text="Waiting for selection...")
        self.lbl_status_subtitle.pack(side="bottom", pady=10)

    def browse_subtitle_video(self):
        path = filedialog.askopenfilename(filetypes=[("Videos", "*.mp4 *.mkv"), ("All", "*.*")])
        if path:
            self.video_path_subtitle.set(path)
            self.btn_convert.configure(state="normal")

    def toggle_subtitle_inputs(self, enable):
        state = "normal" if enable else "disabled"
        self.btn_convert.configure(state=state)
        self.entry_key.configure(state=state)

    def start_subtitle_thread(self):
        key = self.api_key.get().strip()
        vid = self.video_path_subtitle.get()
        if not key:
            messagebox.showwarning("Warning", "API Key required.")
            return
        threading.Thread(target=self.process_video_subtitle, args=(key, vid), daemon=True).start()

    def process_video_subtitle(self, api_key, video_path):
        self.msg_queue.put(("subtitle_start", None))
        temp_audio = "temp_audio_extract.mp3"
        try:
            AudioProcessor.extract_audio(video_path, temp_audio)
            result = GroqService.transcribe(api_key, temp_audio)
            output_path = f"{os.path.splitext(video_path)[0]}.srt"
            SRTConverter.save_srt(result.segments, output_path) # type: ignore
            self.msg_queue.put(("subtitle_ok", f"Subtitle saved: {output_path}"))
        except Exception as e:
            self.msg_queue.put(("subtitle_error", str(e)))
        finally:
            if os.path.exists(temp_audio): os.remove(temp_audio)

    # tab 3 - prospector (i dont know why i didnt gave this a beter name)
    def create_prospector_tab(self):
        self.frame_pros = ctk.CTkFrame(self.tab_prospector)
        self.frame_pros.pack(fill="both", expand=True, padx=10, pady=10)

        # left Config Panel
        panel_config = ctk.CTkFrame(self.frame_pros, width=200)
        panel_config.pack(side="left", fill="y", padx=(0, 10))

        ctk.CTkLabel(panel_config, text="FILTERS", font=("", 14, "bold")).pack(pady=10)
        
        self.input_days = self.create_input(panel_config, "Days Ago:", "30")
        
        # views Filters
        ctk.CTkLabel(panel_config, text="Views:", text_color="cyan").pack(pady=(10,0))
        self.input_views_min = self.create_input(panel_config, "Minimum:", "1000")
        self.input_views_max = self.create_input(panel_config, "Maximum:", "70000")

        self.input_goal = self.create_input(panel_config, "Lead Goal:", "20")

        # right Panel (Terms and Log)
        panel_main = ctk.CTkFrame(self.frame_pros, fg_color="transparent")
        panel_main.pack(side="right", fill="both", expand=True)

        ctk.CTkLabel(panel_main, text="Search Terms (one per line):", anchor="w").pack(fill="x")
        
        default_terms = "gameplay commentary\nsurvival episode 1"
        
        self.txt_terms = ctk.CTkTextbox(panel_main, height=80)
        self.txt_terms.pack(fill="x", pady=(0, 10))
        self.txt_terms.insert("1.0", default_terms)

        self.btn_search = ctk.CTkButton(panel_main, text="START HUNT", command=self.start_prospector_thread, height=40, fg_color="green")
        self.btn_search.pack(fill="x", pady=5)

        ctk.CTkLabel(panel_main, text="Execution Log:", anchor="w").pack(fill="x")
        self.txt_log = ctk.CTkTextbox(panel_main, state="disabled")
        self.txt_log.pack(fill="both", expand=True)

    def create_input(self, parent, label, default):
        ctk.CTkLabel(parent, text=label).pack(pady=(5,0))
        entry = ctk.CTkEntry(parent, width=140)
        entry.pack(pady=(0,5))
        entry.insert(0, default)
        return entry

    def log_prospector(self, msg):
        self.msg_queue.put(("log_pros", msg))

    def start_prospector_thread(self):
        try:
            # capture inputs
            config_params = {
                'days_ago': int(self.input_days.get()),
                'views_min': int(self.input_views_min.get()), 
                'views_max': int(self.input_views_max.get()),
                'duration_min': 120, 
                'duration_max': 7200, 
                'search_limit_per_term': 30,
                'total_goal': int(self.input_goal.get())
            }
            terms_raw = self.txt_terms.get("1.0", "end").strip()
            terms = [t for t in terms_raw.split('\n') if t.strip()]
            
            if not terms:
                messagebox.showwarning("Warning", "Enter at least one search term.")
                return

            self.btn_search.configure(state="disabled", text="Hunting...")
            self.txt_log.configure(state="normal")
            self.txt_log.delete("1.0", "end")
            self.txt_log.configure(state="disabled")

            # instantiate using the imported class
            self.prospector_instance = YoutubeProspector(config_params, self.log_prospector)
            threading.Thread(target=self.run_prospector, args=(terms,), daemon=True).start()

        except ValueError:
            messagebox.showerror("Error", "Ensure numeric fields (Views/Days/Goal) contain only numbers.")

    def run_prospector(self, terms):
        try:
            self.prospector_instance.search(terms)
            self.msg_queue.put(("end_pros", None))
        except Exception as e:
            self.msg_queue.put(("log_pros", f"FATAL ERROR: {e}"))
            self.msg_queue.put(("end_pros", None))

    # queue manager
    def check_queue(self):
        try:
            while True:
                msg_type, data = self.msg_queue.get_nowait()
                
                if msg_type == "watermark_ok":
                    self.lbl_status_watermark.configure(text=data, text_color="green")
                    messagebox.showinfo("Success", "Watermark applied!")
                    self.btn_watermark.configure(state="normal", text="Select Video and Process")
                elif msg_type == "watermark_error":
                    self.lbl_status_watermark.configure(text="Error", text_color="red")
                    messagebox.showerror("Error", data)
                    self.btn_watermark.configure(state="normal", text="Select Video and Process")
                
                elif msg_type == "subtitle_start":
                    self.toggle_subtitle_inputs(False)
                    self.progress.pack(fill="x", padx=20, pady=5)
                    self.progress.start()
                    self.lbl_status_subtitle.configure(text="Sending audio to Groq API...", text_color="blue")
                elif msg_type == "subtitle_ok":
                    self.lbl_status_subtitle.configure(text="Finished!", text_color="green")
                    messagebox.showinfo("Success", data)
                    self.progress.stop()
                    self.progress.pack_forget()
                    self.toggle_subtitle_inputs(True)
                elif msg_type == "subtitle_error":
                    self.lbl_status_subtitle.configure(text="Error", text_color="red")
                    messagebox.showerror("Error", data)
                    self.progress.stop()
                    self.progress.pack_forget()
                    self.toggle_subtitle_inputs(True)
                
                elif msg_type == "log_pros":
                    self.txt_log.configure(state="normal")
                    self.txt_log.insert("end", data + "\n")
                    self.txt_log.see("end")
                    self.txt_log.configure(state="disabled")
                elif msg_type == "end_pros":
                    self.btn_search.configure(state="normal", text="START HUNT")
                    messagebox.showinfo("Finished", "Search finished! Check 'youtube_leads.csv'")

        except queue.Empty:
            pass
        finally:
            self.after(100, self.check_queue)