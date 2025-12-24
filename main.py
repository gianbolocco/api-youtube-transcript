from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from typing import List, Optional

app = FastAPI(
    title="YouTube Transcript API",
    description="A simple API to fetch YouTube video transcripts.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the YouTube Transcript API. Use /transcript/{video_id} to get a transcript."}

@app.get("/transcript/{video_id}")
def get_transcript(
    video_id: str,
    languages: Optional[List[str]] = Query(None, description="List of language codes to prefer. If empty, tries to find any available."),
    include_timestamps: bool = Query(False, description="If true, returns list of segments with timestamps. Default is false (single string)."),
    format: str = Query("json", description="Output format: 'json' or 'text'")
):
    """
    Retrieve the transcript for a given YouTube video ID.
    By default, it tries to find the best available transcript (English preferred)
    and returns it as a single string.
    """
    try:
        # For version 1.2.3+, we must instantiate the class
        api = YouTubeTranscriptApi()
        
        transcript_list_obj = api.list(video_id)
        
        transcript = None
        
        if languages:
            # If user specified languages, try to find them
            transcript = transcript_list_obj.find_transcript(languages)
        else:
            # Fallback logic:
            # 1. Manually created English
            # 2. Manually created any language
            # 3. Generated English
            # 4. Generated any language
            try:
               transcript = transcript_list_obj.find_manually_created_transcript(['en'])
            except:
               try:
                   # Get the first manually created transcript
                   manual_transcripts = list(transcript_list_obj._manually_created_transcripts.values())
                   if manual_transcripts:
                       transcript = manual_transcripts[0]
               except:
                   pass
            
            if not transcript:
                try:
                    transcript = transcript_list_obj.find_generated_transcript(['en'])
                except:
                    try:
                        # Fallback to whatever is available (first generated)
                        generated_transcripts = list(transcript_list_obj._generated_transcripts.values())
                        if generated_transcripts:
                            transcript = generated_transcripts[0]
                    except:
                        pass
        
        if not transcript:
             # Final attempt: just try to fetch anything if logic above failed somehow but list wasn't empty
             # effectively calling .fetch() on the list object calls find_transcript(['en']) by default which might fail
             # so we rely on the logic above to select a specific 'Transcript' object.
             # If we still don't have one, we might really be out of luck or need to force 'en'
             transcript = transcript_list_obj.find_transcript(['en']) # specific fallback

        # Fetch the actual data
        transcript_list = transcript.fetch()
        
        # Convert objects to list of dicts
        transcript_data = [
            {"text": item.text, "start": item.start, "duration": item.duration}
            for item in transcript_list
        ]
        
        full_text = " ".join([item["text"] for item in transcript_data])

        if format.lower() == "text":
            return {"video_id": video_id, "transcript": full_text, "format": "text"}
        
        # JSON Response:
        # Default: single string in "transcript" field
        # If include_timestamps is True: list of segments in "segments" field
        
        response = {
            "video_id": video_id, 
            "transcript": full_text, 
            "language": transcript.language_code,
            "generated": transcript.is_generated,
            "format": "json"
        }
        
        if include_timestamps:
            response["segments"] = transcript_data
            
        return response
            
    except TranscriptsDisabled:
        raise HTTPException(status_code=404, detail="Transcripts are disabled for this video.")
    except NoTranscriptFound:
        raise HTTPException(status_code=404, detail="No transcript found for this video.")
    except VideoUnavailable:
        raise HTTPException(status_code=404, detail="Video is unavailable.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/transcript")
def get_transcript_query(
    video_id: str = Query(..., description="The ID of the YouTube video"),
    languages: Optional[List[str]] = Query(None, description="List of language codes to prefer"),
    include_timestamps: bool = Query(False, description="If true, returns list of segments with timestamps"),
    format: str = Query("json", description="Output format: 'json' or 'text'")
):
    """
    Alternative endpoint using query parameter.
    """
    return get_transcript(video_id, languages, include_timestamps, format)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
