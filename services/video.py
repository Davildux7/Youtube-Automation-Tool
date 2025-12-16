import os
import numpy as np
import PIL.Image
# imports config to make sure pillow is right
import config 
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip

class VideoProcessor:
    def __init__(self, watermark_image_path):
        self.watermark_image_path = watermark_image_path

    def apply_watermark(self, video_path):
        if not os.path.exists(self.watermark_image_path):
            return False, f"Image '{self.watermark_image_path}' not found."

        try:
            video_clip = VideoFileClip(video_path)
            pil_img = PIL.Image.open(self.watermark_image_path).convert('RGBA')
            
            # resize image to match video size
            pil_img_resized = pil_img.resize(video_clip.size, PIL.Image.LANCZOS) # type: ignore
            
            img_array = np.array(pil_img_resized)
            rgb_image = img_array[:, :, :3]
            alpha_mask = img_array[:, :, 3] / 255.0
            
            image_clip = ImageClip(rgb_image).set_mask(ImageClip(alpha_mask, ismask=True))
            opacity_image = image_clip.set_opacity(0.3)
            
            final_image = opacity_image.set_position(("center", "center"))
            final_image = final_image.set_duration(video_clip.duration)

            final_video = CompositeVideoClip([video_clip, final_image])

            temp_path = video_path + ".temp.mp4"
            
            # use threads to speed up writing if possible
            final_video.write_videofile(temp_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)

            video_clip.close()
            image_clip.close()
            final_video.close()

            os.remove(video_path)
            os.rename(temp_path, video_path)

            return True, None
        except Exception as e:
            return False, str(e)