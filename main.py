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
    languages: Optional[List[str]] = Query(["en"], description="List of language codes to prefer"),
    format: str = Query("json", description="Output format: 'json' or 'text'")
):
    """
    Retrieve the transcript for a given YouTube video ID.
    """
    try:
        # For version 1.2.3+, we must instantiate the class
        api = YouTubeTranscriptApi()
        transcript_list = api.fetch(video_id, languages=languages)
        
        # Convert objects to list of dicts
        transcript_data = [
            {"text": item.text, "start": item.start, "duration": item.duration}
            for item in transcript_list
        ]
        
        if format.lower() == "text":
            text_content = " ".join([item["text"] for item in transcript_data])
            return {"video_id": video_id, "transcript": text_content, "format": "text"}
        
        return {"video_id": video_id, "transcript": transcript_data, "format": "json"}
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
    languages: Optional[List[str]] = Query(["en"], description="List of language codes to prefer"),
    format: str = Query("json", description="Output format: 'json' or 'text'")
):
    """
    Alternative endpoint using query parameter.
    """
    return get_transcript(video_id, languages, format)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
