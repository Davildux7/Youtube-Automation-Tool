import os
import csv
from datetime import datetime, timedelta
from yt_dlp import YoutubeDL

class YoutubeProspector:
    def __init__(self, config, log_callback):
        self.config = config
        self.log = log_callback
        # Calculate cutoff date in YYYYMMDD format for comparison
        self.cutoff_date = (datetime.now() - timedelta(days=int(config['days_ago']))).strftime('%Y%m%d')
        self.seen_channels = set()
        self.results = []
        self.stop_flag = False 
        
        self.ydl_opts = {
            'quiet': True,
            'ignoreerrors': True,
            'no_warnings': True,
            'extract_flat': False,
        }

    def _validate_video(self, video):
        if not video: return False
        
        channel = video.get('uploader')
        views = video.get('view_count', 0)
        duration = video.get('duration', 0)
        upload_date = video.get('upload_date', '00000000')

        if not channel or channel in self.seen_channels: return False
        
        try:
            dur_min = float(self.config['duration_min'])
            dur_max = float(self.config['duration_max'])
            views_min = int(self.config['views_min'])
            views_max = int(self.config['views_max'])
        except ValueError:
            return False

        if not (dur_min <= duration <= dur_max): return False
        if upload_date < self.cutoff_date: return False
        if not (views_min <= views <= views_max): return False

        return True

    def save_csv(self):
        if not self.results:
            self.log("No results to save.")
            return

        filename = 'youtube_leads.csv'
        columns = ['Channel', 'Title', 'Views', 'Channel Link', 'Date']
        
        file_exists = os.path.exists(filename)
        
        try:
            with open(filename, 'a', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore', delimiter=';')
                
                if not file_exists:
                    writer.writeheader()
                
                writer.writerows(self.results)
                
            self.log(f"\n{len(self.results)} leads saved to '{filename}'")
            self.results = [] 
        except Exception as e:
            self.log(f"Error saving CSV: {e}")

    def search(self, terms):
        self.log(f"STARTING PROFESSIONAL HUNT")
        self.log(f"Videos from: {datetime.strptime(self.cutoff_date, '%Y%m%d').strftime('%m/%d/%Y')}")
        self.log(f"View Filter: Min {self.config['views_min']} | Max {self.config['views_max']}")
        self.log("-" * 40)

        goal_reached = False

        with YoutubeDL(self.ydl_opts) as ydl: # type: ignore
            for term in terms:
                if goal_reached or self.stop_flag: break
                
                term = term.strip()
                if not term: continue

                self.log(f"\nProbing niche: '{term}'...")
                
                try:
                    limit = self.config['search_limit_per_term']
                    query = f"ytsearch{limit}:{term}"
                    info = ydl.extract_info(query, download=False)

                    if 'entries' not in info: continue

                    for video in info['entries']: # type: ignore
                        if self.stop_flag: break
                        if self._validate_video(video):
                            
                            raw_date = video.get('upload_date')
                            formatted_date = raw_date
                            if raw_date:
                                try:
                                    dt_obj = datetime.strptime(raw_date, '%Y%m%d')
                                    formatted_date = dt_obj.strftime('%d/%m/%Y')
                                except:
                                    pass

                            channel_link = video.get('uploader_url') or video.get('channel_url')
                            if not channel_link and video.get('channel_id'):
                                channel_link = f"https://www.youtube.com/channel/{video.get('channel_id')}"
                            
                            video_data = {
                                'Channel': video.get('uploader'),
                                'Title': video.get('title'),
                                'Views': video.get('view_count'),
                                'Channel Link': channel_link,
                                'Date': formatted_date
                            }
                            
                            self.results.append(video_data)
                            self.seen_channels.add(video_data['Channel'])
                            
                            self.log(f"TARGET: {video_data['Channel']}")
                            self.log(f"   {video_data['Views']} views | {video_data['Date']}")

                            if len(self.results) >= int(self.config['total_goal']):
                                self.log("\nTotal lead goal reached!")
                                goal_reached = True
                                break
                
                except Exception as e:
                    self.log(f"Error on term '{term}': {e}")
                    continue

        self.save_csv()
        self.log(f"\nHunt finished. Total new leads: {len(self.results)}")

        # im too lazy to document all of this