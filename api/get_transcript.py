from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse query parameters
        query_components = parse_qs(urlparse(self.path).query)
        video_id = query_components.get("videoId", [None])[0]

        if not video_id:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "videoId parameter is required"}).encode('utf-8'))
            return

        try:
            # Try to get English transcript first, then any available
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Prioritize manually created English, then generated English, then any first available
            try:
                transcript = transcript_list.find_manually_created_transcript(['en', 'en-GB', 'en-US'])
            except NoTranscriptFound:
                try:
                    transcript = transcript_list.find_generated_transcript(['en', 'en-GB', 'en-US'])
                except NoTranscriptFound:
                    # Fallback to the first available transcript if no English one is found
                    transcript_data = transcript_list.fetch()[0] # Get the first available language
                    fetched_transcript = transcript_data.fetch() # This is already a list of dicts
                    full_transcript_text = " ".join([segment['text'] for segment in fetched_transcript])
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"transcript": full_transcript_text, "language": transcript_data.language}).encode('utf-8'))
                    return

            # If English transcript was found (manual or generated)
            fetched_transcript_segments = transcript.fetch() # list of dicts: {'text': '...', 'start': ..., 'duration': ...}
            
            # Join segments into a single string
            full_transcript_text = " ".join([segment['text'] for segment in fetched_transcript_segments])

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"transcript": full_transcript_text, "language": transcript.language}).encode('utf-8'))

        except TranscriptsDisabled:
            self.send_response(403) # Forbidden or similar
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Transcripts are disabled for video: {video_id}"}).encode('utf-8'))
        except NoTranscriptFound:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"No transcript found for video: {video_id}"}).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"An unexpected error occurred: {str(e)}"}).encode('utf-8'))
        return
