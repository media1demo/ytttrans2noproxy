from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        # Parse query parameters
        query_components = parse_qs(urlparse(self.path).query)
        video_id = query_components.get("video_id", [None])[0]

        if not video_id:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response_data = {"error": "video_id query parameter is required"}
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            return

        try:
            # --- Your core logic starts here ---
            # The library's get_transcript directly returns the list of segment dictionaries
            # This is what your original code iterated over effectively.
            fetched_transcript_segments = YouTubeTranscriptApi.get_transcript(video_id)

            # is iterable (demonstrated by creating a list of texts)
            all_texts = []
            for snippet_dict in fetched_transcript_segments:
                all_texts.append(snippet_dict['text'])

            # indexable (get the last snippet's text)
            last_snippet_text = "N/A"
            if fetched_transcript_segments:
                last_snippet_text = fetched_transcript_segments[-1]['text']

            # provides a length
            snippet_count = len(fetched_transcript_segments)
            # --- Your core logic ends here ---

            response_data = {
                "video_id": video_id,
                "snippet_count": snippet_count,
                "last_snippet_text": last_snippet_text,
                "transcript_texts": all_texts,
                # "full_transcript_data": fetched_transcript_segments # Optional: if you want to send all data
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))

        except TranscriptsDisabled:
            self.send_response(404) # Or another appropriate code
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_msg = f"Transcripts are disabled for video: {video_id}"
            self.wfile.write(json.dumps({"error": error_msg, "video_id": video_id}).encode('utf-8'))
        except NoTranscriptFound:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_msg = f"No transcript found for video: {video_id}. It might be a non-English video or have no captions."
            # You could try to list available transcripts and fetch a specific language if needed:
            # transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            # for transcript_info in transcript_list:
            #     # transcript_info.language, transcript_info.language_code
            #     if transcript_info.language_code == 'en': # example
            #         # transcript = transcript_info.fetch()
            #         pass # implement fetching logic
            self.wfile.write(json.dumps({"error": error_msg, "video_id": video_id}).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e), "video_id": video_id}).encode('utf-8'))
        return
