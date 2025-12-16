from tkinter import messagebox
from config import WATERMARK_FILENAME
from services.video import VideoProcessor
from UI.interface import UnifiedApp

if __name__ == "__main__":
    try:
        # Inicializa o processador de vídeo com o caminho da imagem do config
        video_processor = VideoProcessor(WATERMARK_FILENAME)
        
        # Inicia a Interface
        app = UnifiedApp(video_processor)
        app.mainloop()
        
    except Exception as e:
        # Se algo falhar antes da UI abrir, tenta mostrar um popup básico
        try:
            messagebox.showerror("Fatal Error", str(e))
        except:
            print(f"CRITICAL ERROR: {e}")