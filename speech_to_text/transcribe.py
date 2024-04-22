from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

openai_transcriber = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))




def transcribe_audio(audio_file):
    transcription = openai_transcriber.audio.transcriptions.create(
    model="whisper-1",
    language="en", 
    file=audio_file, 
    response_format="text"
    )
    return transcription
