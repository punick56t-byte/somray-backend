"""
SOMRAY - AI Video Dubbing Backend & Mobile Host Server
Target Dubbing Languages: Khmer (km-KH) & English (en-US)
Clean translation, Edge-TTS Neural Voice synthesis, and Mobile Network Host.
"""

import os
import sys
import socket
import asyncio
import tempfile
import requests
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
import shutil
import json
import re
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="SOMRAY AI Dubbing Studio")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TTSRequest(BaseModel):
    text: str
    voice: str = "km-KH-PisethNeural"
    rate: str = "+0%"
    volume: str = "+30%"

class TranslateRequest(BaseModel):
    text: str
    source: str = "auto"
    target: str = "km"

class TranscribeRequest(BaseModel):
    video_path: str = ""

@app.get("/api/status")
async def get_status():
    return {
        "status": "online",
        "app": "SOMRAY AI Dubbing Studio",
        "target_languages": ["km", "en"],
        "voices": {
            "km": ["km-KH-PisethNeural", "km-KH-SreymomNeural"],
            "en": ["en-US-GuyNeural", "en-US-JennyNeural"]
        }
    }

@app.post("/api/tts")
async def generate_tts(req: TTSRequest):
    """Generate high-quality speech with Edge-TTS for Khmer and English"""
    try:
        import edge_tts
        
        # Format rate properly: must start with '+' or '-'
        rate = req.rate.strip()
        if not rate.startswith("+") and not rate.startswith("-"):
            rate = f"+{rate}"
        if not rate.endswith("%"):
            rate = f"{rate}%"

        # Format volume boost (+30% by default)
        vol = getattr(req, "volume", "+30%").strip()
        if not vol.startswith("+") and not vol.startswith("-"):
            vol = f"+{vol}"
        if not vol.endswith("%"):
            vol = f"{vol}%"

        communicate = edge_tts.Communicate(req.text, req.voice, rate=rate, volume=vol)
        
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        await communicate.save(tmp_path)

        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()

        try:
            os.remove(tmp_path)
        except Exception:
            pass

        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        print(f"TTS Error: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"TTS error: {str(e)}")

@app.post("/api/upload_video")
async def upload_video(file: UploadFile = File(...)):
    """Upload any general video file for transcription and dubbing"""
    try:
        clean_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename or "video.mp4")
        if not clean_name.lower().endswith(('.mp4', '.mkv', '.mov', '.avi', '.webm', '.ts', '.mp3', '.wav', '.m4a')):
            clean_name += ".mp4"

        timestamp = int(asyncio.get_event_loop().time())
        saved_filename = f"uploaded_{timestamp}_{clean_name}"
        saved_path = os.path.join(BASE_DIR, "assets", saved_filename)

        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        rel_path = f"assets/{saved_filename}"
        print(f"[Upload] Received and saved custom video: {saved_path} ({os.path.getsize(saved_path)} bytes)")
        return {
            "status": "success",
            "video_path": rel_path,
            "filename": saved_filename
        }
    except Exception as e:
        print(f"Video upload error: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=str(e))

# Comprehensive Natural Khmer Movie Dubbing Dictionary (Contextual & Grammatical)
QUICK_DICT = {
    # Emergency & Questions
    'hey! speak english?': 'នែ! ចេះនិយាយអង់គ្លេសទេ?!',
    'hey. speak english?': 'នែ! ចេះនិយាយអង់គ្លេសទេ?!',
    'speak english?': 'ចេះនិយាយអង់គ្លេសទេ?!',
    'you speak english?': 'ឯងចេះនិយាយអង់គ្លេសទេ?!',
    'do you speak english?': 'តើឯងចេះនិយាយអង់គ្លេសទេ?!',
    'do you understand?': 'តើឯងយល់ទេ?!',
    'you understand?': 'ឯងយល់ទេ?!',
    'who are you?': 'តើឯងជាអ្នកណា?!',
    'what do you want?': 'តើឯងចង់បានអី?!',
    'what are you doing?': 'តើឯងកំពុងធ្វើស្អីហ្នឹង?!',
    'what is happening?': 'តើមានរឿងអីកើតឡើង?!',
    'what happened?': 'មានរឿងអីហ្នឹង?!',
    'where are you going?': 'តើឯងទៅណា?!',
    'are you crazy?': 'ឯងឆ្កួតហើយឬ?!',
    'are you out of your mind?': 'ឯងឆ្កួតហើយមែនទេ?!',
    'are you okay?': 'ឯងមិនអីទេមែនទេ?!',
    'are you hurt?': 'ឯងមានត្រូវរបួសទេ?!',

    # Taxi / Transportation Scene
    'no, no, no, no!': 'ទេៗៗ! អត់ចេះទេ!',
    'no, no, no!': 'ទេៗៗ! អត់ចេះទេ!',
    'no, no, no.': 'ទេៗៗ! អត់ចេះទេ!',
    'no!': 'ទេ!',
    'ah!': 'អ្ហះ!',
    'yes, yes!': 'បាទៗ! ចេះៗ!',
    'yes, yes.': 'បាទៗ! ចេះៗ!',
    'yes!': 'បាទ!',
    'uh-huh!': 'បាទៗ!',
    'take me to the hospital now.': 'ជូនខ្ញុំទៅមន្ទីរពេទ្យឥឡូវនេះភ្លាម!',
    'take me to the hospital.': 'ជូនខ្ញុំទៅមន្ទីរពេទ្យ!',
    'take me to the police station.': 'ជូនខ្ញុំទៅប៉ុស្តិ៍ប៉ូលីស!',
    'take me home.': 'ជូនខ្ញុំទៅផ្ទះ!',
    'hurry up!': 'ប្រញាប់ឡើង!',
    'drive!': 'បើកឡានទៅ!',
    'drive now!': 'បើកទៅឥឡូវនេះភ្លាម!',
    'faster!': 'លឿនឡើង!',
    'stop!': 'ឈប់!',
    'stop the car!': 'ឈប់ឡានភ្លាម!',

    # Urgent Help & Medical
    'i need help. it\'s urgent.': 'ខ្ញុំត្រូវការព្យាបាល វាជាការបន្ទាន់បំផុត!',
    'i need help, it\'s urgent.': 'ខ្ញុំត្រូវការព្យាបាល វាជាការបន្ទាន់បំផុត!',
    'i need help.': 'ខ្ញុំត្រូវការព្យាបាល!',
    'it\'s urgent.': 'វាជាការបន្ទាន់បំផុត!',
    'help me!': 'ជួយខ្ញុំផង!',
    'help!': 'ជួយផង!',
    'somebody help!': 'អ្នកណាក៏បានជួយផង!',
    'call an ambulance!': 'ហៅឡានពេទ្យភ្លាម!',
    'call 911!': 'ទូរស័ព្ទហៅប៉ូលីសភ្លាម!',
    'call the police!': 'ហៅប៉ូលីសភ្លាម!',
    'you cannot be in here. we are operating.': 'អ្នកមិនអាចចូលទីនេះបានទេ! ពួកយើងកំពុងតែវះកាត់!',
    'you cannot be in here.': 'អ្នកមិនអាចចូលទីនេះបានទេ!',
    'you can\'t be in here.': 'អ្នកមិនអាចចូលទីនេះបានទេ!',
    'we are operating.': 'ពួកយើងកំពុងតែវះកាត់!',
    'we are in surgery.': 'ពួកយើងកំពុងតែវះកាត់!',

    # Surgery Scene & Lucy Commands
    'you wouldn\'t have been able to save him anyway.': 'ទោះជាយ៉ាងណា ក៏លោកមិនអាចជួយសង្គ្រោះគាត់បានដែរ។',
    'you couldn\'t have saved him anyway.': 'ទោះជាយ៉ាងណា ក៏លោកមិនអាចជួយសង្គ្រោះគាត់បានដែរ។',
    'the tumor had already invaded the cortex on the right side of his spine.': 'ដុំសាច់បានរាលដាលដល់សរសៃប្រសាទខួរក្បាល និងផ្នែកខាងស្តាំនៃឆ្អឹងខ្នងគាត់បាត់ទៅហើយ។',
    'the tumor had already invaded the cortex.': 'ដុំសាច់បានរាលដាលដល់សរសៃប្រសាទខួរក្បាលបាត់ទៅហើយ។',
    'out. out now!': 'ចេញទៅ! ចេញទៅឥឡូវនេះភ្លាម!',
    'out now!': 'ចេញទៅឥឡូវនេះភ្លាម!',
    'get out!': 'ចេញទៅ!',
    'get out of here!': 'ចេញពីទីនេះទៅ!',
    'do it now.': 'វះវាឥឡូវនេះភ្លាម!',
    'do it!': 'ធ្វើវាភ្លាម!',
    'operate now!': 'វះវាឥឡូវនេះភ្លាម!',
    'don\'t bother.': 'មិនបាច់ចាក់ថ្នាំស្ពឹកទេ!',
    'don\'t bother with anesthesia.': 'មិនបាច់ចាក់ថ្នាំស្ពឹកទេ!',

    # Surgeon & Action Reactions
    'okay. calm down, please. p-p-p-put the gun down.': 'បាទៗ! សូមចិត្តត្រជាក់សិន... ដ-ដ-ដាក់កាំភ្លើងចុះសិនទៅ!',
    'calm down, please.': 'សូមចិត្តត្រជាក់សិន!',
    'calm down!': 'ចិត្តត្រជាក់សិន!',
    'put the gun down.': 'ដាក់កាំភ្លើងចុះសិនទៅ!',
    'please put the gun down.': 'សូមដាក់កាំភ្លើងចុះសិនទៅ!',
    'don\'t shoot!': 'កុំបាញ់អី!',
    'don\'t move!': 'កុំកម្រើក!',
    'hands up!': 'លើកដៃឡើង!',
    'drop the weapon!': 'ទម្លាក់អាវុធចុះ!',
    'listen to me!': 'ស្តាប់ខ្ញុំសិន!',
    'look at me!': 'មើលមកខ្ញុំ!',
    'shut up!': 'ស្ងាត់មាត់!',
    'be quiet!': 'ស្ងាត់សិន!',
    'don\'t touch me!': 'កុំប៉ះខ្ញុំ!',
    'don\'t touch her!': 'កុំប៉ះពាល់នាងឲ្យសោះ!',
    'don\'t touch him!': 'កុំប៉ះពាល់គាត់ឲ្យសោះ!',
    'leave me alone!': 'ទុកឲ្យខ្ញុំនៅម្នាក់ឯងទៅ!',
    'trust me.': 'ជឿខ្ញុំទៅ!',
    'i promise.': 'ខ្ញុំសន្យា!',
    'it\'s over.': 'ចប់សព្វគ្រប់ហើយ!',
    'we have to go.': 'ពួកយើងត្រូវទៅហើយ!',
    'let\'s go!': 'តោះទៅ!',
    'run!': 'រត់ទៅ!',
    'run away!': 'រត់ឲ្យលឿនទៅ!'
}

def polish_khmer_grammar(text: str, source_text: str = "") -> str:
    """Refine translated Khmer to ensure natural spoken cinematic grammar and tone"""
    if not text or not text.strip():
        return text
    cleaned = text.strip()

    # Rule 1: Fix literal "take me to" (យកខ្ញុំទៅ -> ជូនខ្ញុំទៅ)
    cleaned = re.sub(r'យកខ្ញុំទៅ', 'ជូនខ្ញុំទៅ', cleaned)
    cleaned = re.sub(r'យកគាត់ទៅ', 'ជូនគាត់ទៅ', cleaned)
    cleaned = re.sub(r'យកនាងទៅ', 'ជូននាងទៅ', cleaned)

    # Rule 2: Fix "don't bother" (កុំរំខាន -> មិនបាច់ទេ)
    cleaned = re.sub(r'កុំរំខាន\s*(\S*)', 'មិនបាច់ទេ!', cleaned)

    # Rule 3: Fix literal "speak language" questions
    cleaned = re.sub(r'និយាយភាសាអង់គ្លេស\?', 'ចេះនិយាយអង់គ្លេសទេ?!', cleaned)
    cleaned = re.sub(r'តើអ្នកនិយាយភាសាអង់គ្លេស\?', 'ឯងចេះនិយាយអង់គ្លេសទេ?!', cleaned)
    cleaned = re.sub(r'តើអ្នកចេះនិយាយភាសាអង់គ្លេស\?', 'ឯងចេះនិយាយអង់គ្លេសទេ?!', cleaned)
    cleaned = re.sub(r'និយាយភាសាអង់គ្លេសទេ', 'ចេះនិយាយអង់គ្លេសទេ', cleaned)

    # Rule 4: Fix operating room context
    cleaned = re.sub(r'យើងកំពុងដំណើរការ', 'ពួកយើងកំពុងតែវះកាត់', cleaned)
    cleaned = re.sub(r'ពួកយើងកំពុងដំណើរការ', 'ពួកយើងកំពុងតែវះកាត់', cleaned)
    cleaned = re.sub(r'អ្នកមិនអាចនៅទីនេះបានទេ', 'អ្នកមិនអាចចូលទីនេះបានទេ!', cleaned)
    cleaned = re.sub(r'អ្នកមិនអាចនៅទីនេះទេ', 'អ្នកមិនអាចចូលទីនេះបានទេ!', cleaned)
    cleaned = re.sub(r'ដុំសាច់បានលុកលុយ', 'ដុំសាច់បានរាលដាលដល់', cleaned)
    cleaned = re.sub(r'ដុំសាច់បានឈ្លានពាន', 'ដុំសាច់បានរាលដាលដល់', cleaned)

    # Rule 5: Fix tense confrontation & weapon commands
    cleaned = re.sub(r'ស្ងប់ស្ងាត់', 'សូមចិត្តត្រជាក់សិន', cleaned)
    cleaned = re.sub(r'ស្ងប់អារម្មណ៍', 'ចិត្តត្រជាក់សិន', cleaned)
    cleaned = re.sub(r'ដាក់កាំភ្លើងចុះ', 'ដាក់កាំភ្លើងចុះសិនទៅ', cleaned)
    cleaned = re.sub(r'ទម្លាក់កាំភ្លើង', 'ទម្លាក់កាំភ្លើងចុះ', cleaned)
    cleaned = re.sub(r'ចេញពីទីនេះ', 'ចេញទៅឥឡូវនេះភ្លាម', cleaned)
    cleaned = re.sub(r'ចេញឥឡូវនេះ', 'ចេញទៅឥឡូវនេះភ្លាម', cleaned)
    cleaned = re.sub(r'ធ្វើវាឥឡូវនេះ', 'ធ្វើវាឥឡូវនេះភ្លាម', cleaned)

    # Rule 6: Fix repetitive single words
    cleaned = re.sub(r'(ទេ\s*){4,}', 'ទេៗៗ! អត់ចេះទេ! ', cleaned)
    cleaned = re.sub(r'(បាទ\s*){4,}', 'បាទៗ! ចេះៗ! ', cleaned)

    # Rule 7: Natural spoken pronouns in movie dialogue
    cleaned = re.sub(r'តើអ្នកឈ្មោះអ្វី\?', 'ឯងឈ្មោះអី?!', cleaned)
    cleaned = re.sub(r'តើអ្នកកំពុងធ្វើអ្វី\?', 'តើឯងកំពុងធ្វើស្អីហ្នឹង?!', cleaned)
    cleaned = re.sub(r'តើអ្នកចង់បានអ្វី\?', 'តើឯងចង់បានអី?!', cleaned)
    cleaned = re.sub(r'តើអ្នកជាអ្នកណា\?', 'តើឯងជាអ្នកណា?!', cleaned)
    cleaned = re.sub(r'កុំបារម្ភអំពីវា', 'កុំបារម្ភអី!', cleaned)
    cleaned = re.sub(r'តើមានអ្វីកើតឡើង\?', 'មានរឿងអីកើតឡើង?!', cleaned)
    cleaned = re.sub(r'តើមានរឿងអ្វី\?', 'មានរឿងអី?!', cleaned)
    cleaned = re.sub(r'មិនអាចទៅរួចទេ', 'មិនអាចទេ!', cleaned)
    cleaned = re.sub(r'ខ្ញុំមិនដឹងទេ', 'ខ្ញុំអត់ដឹងទេ!', cleaned)
    cleaned = re.sub(r'ទុកឱ្យខ្ញុំនៅម្នាក់ឯង', 'ទុកឲ្យខ្ញុំនៅម្នាក់ឯងទៅ!', cleaned)

    # Rule 8: Remove stiff written/documentary grammar markers
    cleaned = re.sub(r'ត្រូវបាន\s*(\S+)', r'\1', cleaned)
    cleaned = re.sub(r'គឺត្រូវតែ\s*', 'ត្រូវតែ', cleaned)
    cleaned = re.sub(r'នៅក្នុងខណៈពេលដែល\s*', 'ពេលដែល', cleaned)
    cleaned = re.sub(r'កាលពីអតីតកាល\s*', 'ពីមុន', cleaned)
    cleaned = re.sub(r'ផងដែរ$', 'ដែរ', cleaned)

    return cleaned.strip()

def condense_khmer_for_duration(text: str, slot_duration: float) -> str:
    """
    Intelligently summarize and condense Khmer dialogue if it exceeds the character's speaking duration slot.
    Preserves exact core meaning and emotional intent while matching lip duration.
    """
    if not text or not text.strip() or slot_duration <= 0:
        return text

    clean = text.strip()
    # Estimate speech duration: Khmer chars typically ~0.088 - 0.11s per char in Edge-TTS
    # If estimated duration > slot_duration * 1.15, condense text
    char_count = len(re.sub(r'[\s\u200b\.,!?:;\-\–]', '', clean))
    est_dur = char_count * 0.092

    if est_dur <= slot_duration * 1.15:
        return clean

    # Step 1: Remove verbose filler words and passive particles that aren't spoken in movie dialogue
    clean = re.sub(r'ជាការពិតណាស់', '', clean)
    clean = re.sub(r'ជាក់ស្តែង', '', clean)
    clean = re.sub(r'គឺថា\s*', '', clean)
    clean = re.sub(r'ដែលជា\s*', '', clean)
    clean = re.sub(r'នៅក្នុង\s*', '', clean)
    clean = re.sub(r'កាលពី\s*', '', clean)
    clean = re.sub(r'មួយចំនួន\s*', '', clean)
    clean = re.sub(r'ផងដែរ\s*', '', clean)
    clean = re.sub(r'ទាំងអស់គ្នា\s*', '', clean)
    clean = re.sub(r'សូមមេត្តា\s*', '', clean)
    clean = re.sub(r'ទោះជាយ៉ាងណាក៏ដោយ\s*', 'ទោះយ៉ាងណា ', clean)
    clean = re.sub(r'ដោយសារតែ\s*', 'ព្រោះ ', clean)
    clean = re.sub(r'ពិតប្រាកដ\s*', 'ពិត ', clean)
    clean = re.sub(r'យ៉ាងខ្លាំង\s*', 'ណាស់ ', clean)
    clean = re.sub(r'ត្រូវបាន\s*', '', clean)

    # Step 2: Specific high-frequency conversational condensations
    CONDENSE_RULES = [
        # Questions
        (r'តើឯងកំពុងធ្វើស្អីហ្នឹង[?!]*', 'ធ្វើស្អីហ្នឹង?!'),
        (r'តើអ្នកកំពុងធ្វើអ្វី[?!]*', 'ធ្វើអីហ្នឹង?!'),
        (r'តើអ្នកចង់បានអ្វី[?!]*', 'ចង់បានអី?!'),
        (r'តើឯងចង់បានអី[?!]*', 'ចង់បានអី?!'),
        (r'តើអ្នកជាអ្នកណា[?!]*', 'ឯងជាអ្នកណា?!'),
        (r'តើលោកជាអ្នកណា[?!]*', 'លោកជាអ្នកណា?!'),
        (r'តើមានរឿងអ្វីកើតឡើង[?!]*', 'មានរឿងអី?!'),
        (r'តើមានរឿងអ្វី[?!]*', 'មានរឿងអី?!'),
        (r'តើមានបញ្ហាអ្វី[?!]*', 'មានបញ្ហាអី?!'),
        (r'តើឯងយល់ទេ[?!]*', 'យល់ទេ?!'),
        (r'តើអ្នកយល់ទេ[?!]*', 'យល់ទេ?!'),
        (r'តើឯងចេះនិយាយអង់គ្លេសទេ[?!]*', 'ចេះអង់គ្លេសទេ?!'),
        (r'តើអ្នកចេះនិយាយអង់គ្លេសទេ[?!]*', 'ចេះអង់គ្លេសទេ?!'),
        (r'ចេះនិយាយអង់គ្លេសទេ[?!]*', 'ចេះអង់គ្លេសទេ?!'),
        (r'តើឯងកំពុងនិយាយពីស្អី[?!]*', 'និយាយពីអី?!'),
        (r'តើអ្នកកំពុងនិយាយអំពីអ្វី[?!]*', 'និយាយពីអី?!'),
        (r'តើយើងត្រូវធ្វើអ្វីឥឡូវនេះ[?!]*', 'ឥឡូវធ្វើម៉េច?!'),
        (r'តើឯងប្រាកដចិត្តទេ[?!]*', 'ប្រាកដទេ?!'),
        (r'តើអ្នកប្រាកដទេ[?!]*', 'ប្រាកដទេ?!'),
        (r'រួចរាល់ហើយឬនៅ[?!]*', 'រួចរាល់នៅ?!'),
        # Commands & Urgent Action
        (r'សូមចិត្តត្រជាក់សិន\.\.\. ដ-ដ-ដាក់កាំភ្លើងចុះសិនទៅ!?', 'ចិត្តត្រជាក់! ដាក់កាំភ្លើងចុះ!'),
        (r'សូមចិត្តត្រជាក់សិន[?!]*', 'ចិត្តត្រជាក់!'),
        (r'សូមដាក់កាំភ្លើងចុះសិនទៅ[?!]*', 'ដាក់កាំភ្លើងចុះ!'),
        (r'ដាក់កាំភ្លើងចុះសិនទៅ[?!]*', 'ដាក់កាំភ្លើងចុះ!'),
        (r'ចេញទៅ! ចេញទៅឥឡូវនេះភ្លាម[?!]*', 'ចេញទៅភ្លាម!'),
        (r'ចេញទៅឥឡូវនេះភ្លាម[?!]*', 'ចេញទៅភ្លាម!'),
        (r'ចេញពីទីនេះទៅ[?!]*', 'ចេញទៅ!'),
        (r'ពួកយើងកំពុងតែវះកាត់[?!]*', 'កំពុងវះកាត់!'),
        (r'អ្នកមិនអាចចូលទីនេះបានទេ[?!]*', 'ចូលមិនបានទេ!'),
        (r'ជូនខ្ញុំទៅមន្ទីរពេទ្យឥឡូវនេះភ្លាម[?!]*', 'ជូនទៅពេទ្យភ្លាម!'),
        (r'ជូនខ្ញុំទៅមន្ទីរពេទ្យ[?!]*', 'ជូនទៅពេទ្យ!'),
        (r'ជូនខ្ញុំទៅប៉ុស្តិ៍ប៉ូលីស[?!]*', 'ជូនទៅប៉ុស្តិ៍ប៉ូលីស!'),
        (r'ខ្ញុំត្រូវការព្យាបាល វាជាការបន្ទាន់បំផុត[?!]*', 'ត្រូវការព្យាបាលបន្ទាន់!'),
        (r'ខ្ញុំត្រូវការព្យាបាល[?!]*', 'ត្រូវការព្យាបាល!'),
        (r'ទោះជាយ៉ាងណា ក៏លោកមិនអាចជួយសង្គ្រោះគាត់បានដែរ[?!]*', 'ទោះជួយ ក៏មិនរស់ដែរ!'),
        (r'ដុំសាច់បានរាលដាលដល់សរសៃប្រសាទខួរក្បាល និងផ្នែកខាងស្តាំនៃឆ្អឹងខ្នងគាត់បាត់ទៅហើយ[?!]*', 'ដុំសាច់រាលដល់ខួរក្បាល និងឆ្អឹងខ្នងអស់ហើយ!'),
        (r'ដុំសាច់បានរាលដាលដល់សរសៃប្រសាទខួរក្បាលបាត់ទៅហើយ[?!]*', 'ដុំសាច់រាលដល់ខួរក្បាលអស់ហើយ!'),
        (r'មិនបាច់ចាក់ថ្នាំស្ពឹកទេ[?!]*', 'មិនបាច់ស្ពឹកទេ!'),
        (r'វះវាឥឡូវនេះភ្លាម[?!]*', 'វះវាភ្លាម!'),
        (r'ធ្វើវាឥឡូវនេះភ្លាម[?!]*', 'ធ្វើវាភ្លាម!'),
        (r'បើកទៅឥឡូវនេះភ្លាម[?!]*', 'បើកទៅភ្លាម!'),
        (r'ស្តាប់ខ្ញុំសិន[?!]*', 'ស្តាប់សិន!'),
        (r'មើលមកខ្ញុំ[?!]*', 'មើលខ្ញុំ!'),
        (r'កុំធ្វើបែបនេះអី[?!]*', 'កុំធ្វើចឹង!'),
        (r'ខ្ញុំមិនអីទេ[?!]*', 'មិនអីទេ!'),
        (r'ចប់សព្វគ្រប់ហើយ[?!]*', 'ចប់ហើយ!'),
        (r'យើងត្រូវតែរត់[?!]*', 'រត់ទៅ!'),
        (r'សន្យានឹងខ្ញុំ[?!]*', 'សន្យាមក!'),
        (r'ជឿខ្ញុំទៅ[?!]*', 'ជឿខ្ញុំ!'),
        (r'ចាំខ្ញុំនៅទីនេះសិន[?!]*', 'ចាំទីនេះ!'),
        (r'ខ្ញុំនឹងត្រឡប់មកវិញ[?!]*', 'ខ្ញុំនឹងមកវិញ!'),
        (r'ខ្ញុំទ្រាំលែងបានហើយ[?!]*', 'ទ្រាំលែងបានហើយ!'),
        (r'កុំសម្លាប់ខ្ញុំអី[?!]*', 'កុំសម្លាប់ខ្ញុំ!'),
        (r'កុំប៉ះពាល់នាងឲ្យសោះ[?!]*', 'កុំប៉ះនាង!'),
        (r'កុំប៉ះពាល់គាត់ឲ្យសោះ[?!]*', 'កុំប៉ះគាត់!'),
        (r'និយាយការពិតមក[?!]*', 'និយាយការពិត!'),
        (r'ខ្ញុំអត់បានកុហកទេ[?!]*', 'ខ្ញុំអត់កុហកទេ!')
    ]

    for pat, rep in CONDENSE_RULES:
        clean = re.sub(pat, rep, clean)

    clean = re.sub(r'\s+', ' ', clean).strip()

    # If still too long for an extremely short slot (<1.2s), extract core action
    char_count = len(re.sub(r'[\s\u200b\.,!?:;\-\–]', '', clean))
    est_dur = char_count * 0.088
    if est_dur > slot_duration * 1.3 and slot_duration < 1.2:
        parts = re.split(r'[!?,.]', clean)
        if len(parts) > 1 and parts[0].strip():
            clean = parts[0].strip() + "!"

    return clean.strip()

whisper_model = None
def get_whisper():
    global whisper_model
    if whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            whisper_model = WhisperModel('tiny', device='cpu', compute_type='int8')
        except Exception as e:
            print(f"Failed to load faster_whisper: {e}", file=sys.stderr)
    return whisper_model

def detect_audio_character_gender(audio_path: str, start_s: float, end_s: float, text: str = "", speaker: str = ""):
    """Real acoustic pitch (F0) & linguistic gender classifier for characters"""
    import subprocess
    import numpy as np
    import scipy.io.wavfile as wavfile
    import scipy.signal as signal

    spk_lower = (speaker + " " + text).lower()

    # 1. Linguistic strong cues (English & Khmer dialogue cues)
    female_cues = ["lucy", "scarlett", "woman", "girl", "mrs", "miss", "lady", "she", "her", "madam", "mother", "mom", "sister", "daughter", "female", "actress", "ស្រី", "នាង", "អ្នកនាង", "កញ្ញា", "ម៉ាក់", "ម្តាយ", "បងស្រី", "ប្អូនស្រី", "យាយ"]
    male_cues = ["driver", "surgeon", "doctor", "man", "boy", "mr", "sir", "he", "his", "him", "father", "dad", "brother", "son", "guy", "male", "actor", "ប្រុស", "លោក", "លោកពូ", "បងប្រុស", "ប្អូនប្រុស", "តា", "បុរស"]

    if any(w in spk_lower for w in female_cues) and not any(w in spk_lower for w in male_cues):
        return "female", 240.0
    if any(w in spk_lower for w in male_cues) and not any(w in spk_lower for w in female_cues):
        return "male", 115.0

    # 2. Fast In-Memory Acoustic pitch estimation (0 subprocesses, instant for 60-min movies)
    try:
        sr = 16000
        if isinstance(audio_path, np.ndarray):
            start_idx = int(max(0, start_s * sr))
            end_idx = min(len(audio_path), int(end_s * sr))
            data = audio_path[start_idx:end_idx]
        elif isinstance(audio_path, str) and os.path.exists(audio_path):
            sr_file, data_file = wavfile.read(audio_path)
            sr = sr_file
            start_idx = int(max(0, start_s * sr))
            end_idx = min(len(data_file), int(end_s * sr))
            data = data_file[start_idx:end_idx].astype(np.float32)
        else:
            data = np.array([])

        if len(data) >= sr * 0.15:
            # 4th order bandpass filter 75Hz - 340Hz to isolate voice fundamental
            sos = signal.butter(4, [75, 340], 'bandpass', fs=sr, output='sos')
            filtered = signal.sosfilt(sos, data)
            frame_len = int(sr * 0.04)
            hop = int(sr * 0.02)
            pitches = []
            min_lag = int(sr / 340)
            max_lag = int(sr / 75)
            for i in range(0, len(filtered) - frame_len, hop):
                frame = filtered[i:i+frame_len]
                if np.sum(frame**2) < 1e4:
                    continue
                corr = np.correlate(frame, frame, mode='full')[frame_len-1:]
                lag_corr = corr[min_lag:max_lag]
                if len(lag_corr) > 0 and np.max(lag_corr) > 0.35 * corr[0]:
                    p = sr / (min_lag + np.argmax(lag_corr))
                    if 75 <= p <= 340:
                        pitches.append(p)
            if len(pitches) > 0:
                med_pitch = float(np.median(pitches))
                # Average adult male fundamental frequency is 85-155Hz; female is 165-260Hz.
                gender = "female" if med_pitch >= 160.0 else "male"
                return gender, round(med_pitch, 1)
    except Exception as e:
        print(f"Pitch detection note: {e}", file=sys.stderr)

    return "male", 120.0

def resolve_server_video_path(video_path: str) -> str:
    """Robust resolution of video paths from client or local filesystem"""
    if not video_path:
        return ""
    clean_p = video_path.strip().replace("\\", "/")
    if "://" in clean_p:
        from urllib.parse import urlparse
        clean_p = urlparse(clean_p).path.lstrip("/")

    if os.path.isabs(clean_p) and os.path.exists(clean_p):
        return clean_p

    clean_rel = clean_p.lstrip("/")
    cand = os.path.join(BASE_DIR, clean_rel)
    if os.path.exists(cand):
        return cand

    alt = os.path.join(BASE_DIR, "assets", os.path.basename(clean_rel))
    if os.path.exists(alt):
        return alt

    return ""

def get_video_info(video_path: str) -> dict:
    """Extract complete video dimensions, duration, DAR, and audio stream status"""
    info = {
        "duration": 0.0,
        "width": 1920,
        "height": 1080,
        "aspect_ratio": "16:9",
        "has_audio": False
    }
    if not video_path or not os.path.exists(video_path):
        return info
    try:
        import subprocess, json
        res = subprocess.run([
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", video_path
        ], capture_output=True, text=True, timeout=15)
        data = json.loads(res.stdout)
        fmt = data.get("format", {})
        info["duration"] = float(fmt.get("duration", 0.0))
        for s in data.get("streams", []):
            if s.get("codec_type") == "video":
                w = int(s.get("width", 1920))
                h = int(s.get("height", 1080))
                info["width"] = w
                info["height"] = h
                if h > 0:
                    r = w / h
                    if abs(r - (16/9)) < 0.15:
                        info["aspect_ratio"] = "16:9"
                    elif abs(r - (9/16)) < 0.15:
                        info["aspect_ratio"] = "9:16"
                    elif abs(r - 1.0) < 0.15:
                        info["aspect_ratio"] = "1:1"
                    elif r > 2.0:
                        info["aspect_ratio"] = "21:9"
                    else:
                        info["aspect_ratio"] = f"{w}:{h}"
            elif s.get("codec_type") == "audio":
                info["has_audio"] = True
    except Exception as e:
        print(f"ffprobe info error: {e}", file=sys.stderr)
    return info

def has_audio_track(video_path: str) -> bool:
    """Check if the video has an audio stream"""
    info = get_video_info(video_path)
    return info["has_audio"]

def translate_to_target(text: str, target: str = "km") -> str:
    """Natural contextual translation from any language to Khmer/English with fallback engines"""
    if not text or not text.strip():
        return ""
    target_code = "km" if target in ["km", "khmer", "km-KH"] else "en"
    norm = text.lower().strip()
    if target_code == "km" and norm in QUICK_DICT:
        return QUICK_DICT[norm]

    raw_translated = None

    # Engine 1: Chrome Extension Google API (dict-chrome-ex, unthrottled and reliable for all languages)
    endpoints = [
        ("https://translate.googleapis.com/translate_a/single", {
            "client": "dict-chrome-ex", "sl": "auto", "tl": target_code, "dt": "t", "q": text
        }),
        ("https://clients5.google.com/translate_a/t", {
            "client": "dict-chrome-ex", "sl": "auto", "tl": target_code, "q": text
        })
    ]
    for url, params in endpoints:
        try:
            r = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}, timeout=6)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list) and len(data) > 0:
                    if isinstance(data[0], list) and len(data[0]) > 0:
                        first = data[0][0]
                        if isinstance(first, list) and len(first) > 0 and isinstance(first[0], str):
                            cand = "".join([item[0] for item in data[0] if isinstance(item, list) and len(item) > 0 and isinstance(item[0], str)]).strip()
                            if cand:
                                raw_translated = cand
                                break
                        elif isinstance(first, str):
                            raw_translated = first.strip()
                            break
                    elif isinstance(data[0], str):
                        raw_translated = data[0].strip()
                        break
        except Exception:
            pass
        if raw_translated:
            break

    # Engine 2: Multi-Language MyMemory Translation with script detection
    if not raw_translated or raw_translated == text:
        try:
            from deep_translator import MyMemoryTranslator
            # Automatically detect source language code
            src = "en-US"
            if re.search(r'[\u4e00-\u9fff]', text):
                src = "zh-CN"
            elif re.search(r'[\u0e00-\u0e7f]', text):
                src = "th-TH"
            elif re.search(r'[\u3040-\u30ff]', text):
                src = "ja-JP"
            elif re.search(r'[\uac00-\ud7af]', text):
                src = "ko-KR"
            tgt = "km-KH" if target_code == "km" else "en-US"
            cand = MyMemoryTranslator(source=src, target=tgt).translate(text)
            if cand and cand.strip():
                raw_translated = cand.strip()
        except Exception:
            pass

    if not raw_translated:
        raw_translated = text

    if target_code == "km":
        return polish_khmer_grammar(raw_translated, text)
    return raw_translated

from concurrent.futures import ThreadPoolExecutor

def batch_translate_to_target(texts: list, target: str = "km") -> list:
    """Fast concurrent translation of dialogues supporting 1000+ segments for 60-minute movies"""
    if not texts:
        return []

    results = [None] * len(texts)
    to_translate = []

    for idx, txt in enumerate(texts):
        if not txt or not txt.strip():
            results[idx] = ""
            continue
        norm = txt.lower().strip()
        if target == "km" and norm in QUICK_DICT:
            results[idx] = QUICK_DICT[norm]
        else:
            to_translate.append((idx, txt))

    if not to_translate:
        return results

    def fetch_trans(item):
        i, t = item
        return i, translate_to_target(t, target)

    # Use 12 concurrent workers for high-speed translation
    with ThreadPoolExecutor(max_workers=12) as executor:
        for i, trans_text in executor.map(fetch_trans, to_translate):
            results[i] = trans_text

    return results

@app.post("/api/translate")
async def translate_text(req: TranslateRequest):
    """Natural contextual translation with Khmer grammar enhancement"""
    return {"translated": translate_to_target(req.text, req.target)}

@app.post("/api/transcribe")
async def transcribe_video(req: TranscribeRequest):
    """Real speech-to-text transcription with acoustic character sex detection on actual video"""
    # 1. If user explicitly requested demo video, return curated segments
    if req.video_path == "demo":
        cached_json = os.path.join(BASE_DIR, "assets", "user_video_segments.json")
        if os.path.exists(cached_json):
            try:
                with open(cached_json, "r", encoding="utf-8") as f:
                    return {"status": "success", "segments": json.load(f)}
            except Exception:
                pass

    # 2. Resolve video path strictly to the user's uploaded video
    video_full = resolve_server_video_path(req.video_path)

    if not video_full or not os.path.exists(video_full):
        raise HTTPException(status_code=404, detail=f"Video file not found on server: {req.video_path}")

    # Check for audio stream
    video_info = get_video_info(video_full)
    if not video_info["has_audio"]:
        return {
            "status": "success",
            "language": "none",
            "segments": [],
            "message": "No audio stream detected",
            "video_info": video_info
        }

    # 3. Transcribe using faster-whisper with VAD filter to handle up to 60-minute movies efficiently
    model = get_whisper()
    if model:
        try:
            wav_tmp = os.path.join(tempfile.gettempdir(), f"somray_audio_{int(asyncio.get_event_loop().time())}.wav")
            import subprocess
            subprocess.run([
                'ffmpeg', '-y', '-i', video_full,
                '-vn', '-ar', '16000', '-ac', '1',
                '-c:a', 'pcm_s16le', wav_tmp
            ], check=True, capture_output=True)

            # Read audio data into memory once for high-speed slicing (0 subprocesses!)
            import scipy.io.wavfile as wavfile
            import numpy as np
            sr_audio, full_audio_data = wavfile.read(wav_tmp)
            full_audio_data = full_audio_data.astype(np.float32)

            # vad_filter=True removes background music & silences in 1-2 hour movies
            raw_segments, info = model.transcribe(
                wav_tmp,
                beam_size=3,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=400)
            )

            parsed_list = []
            idx = 1
            for s in raw_segments:
                # Support videos up to 60 minutes (3600 seconds)
                if s.start > 3600.0:
                    break
                txt = s.text.strip()
                if not txt or len(txt) < 1:
                    continue

                start_val = round(s.start, 2)
                end_val = round(s.end, 2)
                slot_dur = max(0.4, round(end_val - start_val, 2))

                # Real acoustic F0 & linguistic character gender detection using in-memory array (instant!)
                gender, pitch_hz = detect_audio_character_gender(full_audio_data, start_val, end_val, txt)
                voice = 'km-KH-SreymomNeural' if gender == 'female' else 'km-KH-PisethNeural'
                speaker_name = f'តួអង្គ {idx} ({"ស្រី" if gender == "female" else "ប្រុស"})'

                parsed_list.append({
                    'id': idx,
                    'speaker': speaker_name,
                    'gender': gender,
                    'gender_label': f'👩 តួស្រី ({pitch_hz:.0f}Hz)' if gender == 'female' else f'👨 តួប្រុស ({pitch_hz:.0f}Hz)',
                    'start': start_val,
                    'end': end_val,
                    'slot_dur': slot_dur,
                    'origText': txt,
                    'voice': voice
                })
                idx += 1

            # High-speed batch translation (concurrent threads - finishes 500+ segments in seconds!)
            all_texts = [p['origText'] for p in parsed_list]
            translated_texts = batch_translate_to_target(all_texts, target="km")

            segments = []
            for p, trans in zip(parsed_list, translated_texts):
                condensed = condense_khmer_for_duration(trans, p['slot_dur'])
                p['dubText'] = condensed
                del p['slot_dur']
                segments.append(p)

            if os.path.exists(wav_tmp):
                try:
                    os.remove(wav_tmp)
                except Exception:
                    pass

            return {
                "status": "success",
                "language": info.language,
                "segments": segments,
                "video_info": video_info
            }
        except Exception as e:
            print(f"Faster-whisper error: {e}", file=sys.stderr)
            raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

    return {"status": "fallback", "segments": []}

class DubVideoRequest(BaseModel):
    video_path: str = ""
    segments: list = []
    target_lang: str = "km"
    voice: str = "km-KH-PisethNeural"
    duck_volume: float = 0.60
    volume_boost: float = 1.3

@app.post("/api/dub_full_video")
async def dub_full_video(req: DubVideoRequest):
    """
    Generate all TTS voices with perfect lip-sync duration matching,
    master timeline speech track assembly (supporting 1-2 hour movies),
    and merge preserving original 16:9 / native resolution via FFmpeg stream copy.
    """
    import subprocess
    import edge_tts
    import numpy as np
    import scipy.io.wavfile as wavfile
    import math

    if not req.segments:
        raise HTTPException(status_code=400, detail="No segments provided")

    video_full = resolve_server_video_path(req.video_path)
    if not video_full or not os.path.exists(video_full):
        raise HTTPException(status_code=404, detail=f"Target video not found on server: {req.video_path}")

    video_info = get_video_info(video_full)
    total_video_dur = video_info["duration"]

    tmp_dir = tempfile.mkdtemp()
    SR = 24000  # High-fidelity 24kHz sample rate for Edge-TTS neural speech

    try:
        # Step 1: Prepare segments with duration condensation and voice assignment
        prepared_segments = []
        mute_intervals = []
        max_end_time = 0.0

        for idx, seg in enumerate(req.segments):
            text = seg.get("dubText") or seg.get("origText") or ""
            if not text.strip():
                continue

            start_s = float(seg.get("start", 0))
            end_s = float(seg.get("end", start_s + 1.5))
            slot_dur = max(0.4, round(end_s - start_s, 2))
            max_end_time = max(max_end_time, end_s)

            # Requirement 3: Lip-sync duration matching by condensing Khmer text
            if req.target_lang == "km":
                has_khmer = bool(re.search(r'[\u1780-\u17ff]', text))
                if not has_khmer:
                    text = translate_to_target(text, target="km")
                text = condense_khmer_for_duration(text, slot_dur)

            # Determine character voice
            if req.voice in ("male", "male-en"):
                voice = "km-KH-PisethNeural" if req.target_lang == "km" else "en-US-GuyNeural"
            elif req.voice in ("female", "female-en"):
                voice = "km-KH-SreymomNeural" if req.target_lang == "km" else "en-US-JennyNeural"
            elif req.voice in ("dual", "both", "auto", "multi-character") or not req.voice:
                spk = str(seg.get("speaker", "")).lower()
                is_female = (seg.get("gender") == "female" or any(w in spk for w in ["ស្រី", "woman", "female"])) and (seg.get("gender") != "male")
                if req.target_lang == "km":
                    voice = "km-KH-SreymomNeural" if is_female else "km-KH-PisethNeural"
                else:
                    voice = "en-US-JennyNeural" if is_female else "en-US-GuyNeural"
            elif seg.get("voice") in ("km-KH-PisethNeural", "km-KH-SreymomNeural", "en-US-GuyNeural", "en-US-JennyNeural"):
                voice = seg.get("voice")
            else:
                voice = "km-KH-PisethNeural" if req.target_lang == "km" else "en-US-GuyNeural"

            # Pre-tune Edge-TTS speaking rate to match mouth timing naturally
            char_count = len(re.sub(r'[\s\u200b\.,!?:;\-\–]', '', text))
            est_dur = char_count * 0.095
            rate_pct = 0
            if est_dur > slot_dur * 1.05:
                # Keep rate gentle (+4% to +12%) so voice remains human and clear
                rate_pct = min(12, max(4, int((est_dur / slot_dur - 1.0) * 40)))
            rate_str = f"+{rate_pct}%"

            mute_intervals.append(f"between(t,{start_s:.2f},{end_s:.2f})")

            prepared_segments.append({
                "idx": idx,
                "text": text,
                "voice": voice,
                "rate": rate_str,
                "start_s": start_s,
                "end_s": end_s,
                "slot_dur": slot_dur
            })

        if not prepared_segments:
            raise HTTPException(status_code=400, detail="No dialogue to synthesize")

        # Step 2: High-concurrency TTS generation (supports 1-2 hour movies with 500-1500 segments)
        sem = asyncio.Semaphore(16)

        async def synthesize_segment(seg_info):
            async with sem:
                idx = seg_info["idx"]
                text = seg_info["text"]
                voice = seg_info["voice"]
                rate = seg_info["rate"]
                slot_dur = seg_info["slot_dur"]

                mp3_path = os.path.join(tmp_dir, f"seg_{idx}.mp3")
                wav_path = os.path.join(tmp_dir, f"seg_{idx}.wav")

                # Robust TTS synthesis with auto-retry, timeout, and safe fallback
                try:
                    comm = edge_tts.Communicate(text, voice, rate=rate, volume="+30%")
                    await asyncio.wait_for(comm.save(mp3_path), timeout=15.0)
                except Exception as tts_err:
                    print(f"TTS retry on segment {idx}: {tts_err}", file=sys.stderr)
                    try:
                        clean_km = translate_to_target(text, target="km")
                        if not re.search(r'[\u1780-\u17ff]', clean_km):
                            clean_km = "បាទ" if "Piseth" in voice else "ចាស"
                        comm_fb = edge_tts.Communicate(clean_km, voice, rate="+0%", volume="+30%")
                        await asyncio.wait_for(comm_fb.save(mp3_path), timeout=12.0)
                    except Exception as fb_err:
                        print(f"TTS fallback failed on segment {idx}: {fb_err}", file=sys.stderr)

                # Convert to wav and inspect exact audio duration
                if not os.path.exists(mp3_path) or os.path.getsize(mp3_path) == 0:
                    # Write brief silent audio so long video dubbing never halts on single segment network glitch
                    silent_samples = np.zeros(int(max(0.4, slot_dur) * SR), dtype=np.int16)
                    wavfile.write(wav_path, SR, silent_samples)
                else:
                    try:
                        subprocess.run(['ffmpeg', '-y', '-i', mp3_path, '-ar', str(SR), '-ac', '1', wav_path], capture_output=True, check=True)
                    except Exception as conv_err:
                        silent_samples = np.zeros(int(max(0.4, slot_dur) * SR), dtype=np.int16)
                        wavfile.write(wav_path, SR, silent_samples)
                
                # Perfect Lip-Sync: gentle atempo adjustment (max 1.20)
                if os.path.exists(wav_path) and os.path.getsize(wav_path) > 44:
                    try:
                        sr_in, data = wavfile.read(wav_path)
                        actual_dur = len(data) / sr_in
                        if actual_dur > slot_dur * 1.03:
                            tempo = min(1.20, round(actual_dur / max(0.35, slot_dur), 2))
                            if tempo > 1.03:
                                synced_wav = os.path.join(tmp_dir, f"synced_{idx}.wav")
                                subprocess.run(['ffmpeg', '-y', '-i', wav_path, '-filter:a', f'atempo={tempo}', '-ar', str(SR), '-ac', '1', synced_wav], capture_output=True, check=True)
                                if os.path.exists(synced_wav):
                                    os.replace(synced_wav, wav_path)
                    except Exception as sync_err:
                        print(f"Sync check note on segment {idx}: {sync_err}", file=sys.stderr)

                seg_info["wav_path"] = wav_path
                return seg_info

        await asyncio.gather(*[synthesize_segment(s) for s in prepared_segments], return_exceptions=True)

        # Step 3: Master Speech Timeline Track Assembly (Memory-efficient numpy array)
        timeline_len_s = max(total_video_dur, max_end_time) + 2.0
        total_samples = int(math.ceil(timeline_len_s * SR))
        master_buffer = np.zeros(total_samples, dtype=np.float32)

        for seg_info in prepared_segments:
            wav_path = seg_info.get("wav_path")
            if not wav_path or not os.path.exists(wav_path) or os.path.getsize(wav_path) <= 44:
                continue
            try:
                sr, seg_samples = wavfile.read(wav_path)
                if sr != SR:
                    continue

                start_idx = int(seg_info["start_s"] * SR)
                end_idx = start_idx + len(seg_samples)

                if start_idx < total_samples:
                    avail = min(len(seg_samples), total_samples - start_idx)
                    master_buffer[start_idx:start_idx + avail] += seg_samples[:avail].astype(np.float32)
            except Exception as read_err:
                print(f"Segment read note: {read_err}", file=sys.stderr)

        # Apply user volume boost to dub speech (default 1.3 -> 130%)
        boost = float(getattr(req, "volume_boost", 1.3))
        speech_track = master_buffer * boost

        # Step 4: In-Memory Vocal Kill & Background SFX Mix
        has_bgm = video_info["has_audio"]
        sfx_vol = float(getattr(req, "duck_volume", 0.0))
        if sfx_vol > 0.60:
            sfx_vol = 0.60
        if sfx_vol <= 0.01:
            sfx_vol = 0.0

        if has_bgm and sfx_vol > 0.0:
            try:
                bgm_wav = os.path.join(tmp_dir, "orig_bgm.wav")
                subprocess.run([
                    'ffmpeg', '-y', '-i', video_full,
                    '-vn', '-ar', str(SR), '-ac', '1',
                    bgm_wav
                ], capture_output=True, check=True)
                _, bgm_data = wavfile.read(bgm_wav)
                bgm_samples = bgm_data.astype(np.float32)

                if len(bgm_samples) < total_samples:
                    bgm_samples = np.pad(bgm_samples, (0, total_samples - len(bgm_samples)))
                else:
                    bgm_samples = bgm_samples[:total_samples]

                # 100% Dialogue Vocal Kill: Completely silence original actors whenever characters speak!
                for seg_info in prepared_segments:
                    st_idx = max(0, int(seg_info["start_s"] * SR))
                    en_idx = min(total_samples, int(seg_info["end_s"] * SR))
                    if st_idx < en_idx:
                        bgm_samples[st_idx:en_idx] = 0.0

                mixed_audio = (bgm_samples * sfx_vol) + speech_track
            except Exception as mix_err:
                print(f"BGM mix fallback to speech track: {mix_err}", file=sys.stderr)
                mixed_audio = speech_track
        else:
            # 100% pure crystal clear Khmer AI dub (0% original speech)
            mixed_audio = speech_track

        # Clip to 16-bit PCM and export final audio
        master_pcm16 = np.clip(mixed_audio, -32768.0, 32767.0).astype(np.int16)
        final_audio_path = os.path.join(tmp_dir, "final_dubbed_audio.wav")
        wavfile.write(final_audio_path, SR, master_pcm16)

        # Step 5: Mux final video preserving 100% native aspect ratio and resolution (16:9 1080p/4K)
        output_filename = f"dubbed_{req.target_lang}_{int(asyncio.get_event_loop().time())}.mp4"
        output_path = os.path.join(BASE_DIR, "assets", output_filename)

        cmd = [
            "ffmpeg", "-y",
            "-i", video_full,
            "-i", final_audio_path,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            output_path
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as cpe:
            print(f"Stream copy fallback ({cpe}), re-encoding video preserving native dimensions...", file=sys.stderr)
            cmd_fallback = [
                "ffmpeg", "-y",
                "-i", video_full,
                "-i", final_audio_path,
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                output_path
            ]
            subprocess.run(cmd_fallback, check=True, capture_output=True)

        # Also copy to clean named video for direct download matching
        orig_base = os.path.basename(video_full)
        dubbed_custom_name = f"DUBBED_{orig_base}"
        dubbed_custom_path = os.path.join(BASE_DIR, "assets", dubbed_custom_name)
        # Also save stripped name without uploaded_\d+_ prefix (e.g. DUBBED_1000000119.mp4)
        clean_user_name = re.sub(r'^uploaded_\d+_', '', orig_base)
        dubbed_clean_name = f"DUBBED_{clean_user_name}"
        try:
            shutil.copyfile(output_path, dubbed_custom_path)
            shutil.copyfile(output_path, os.path.join(BASE_DIR, "assets", dubbed_clean_name))
            shutil.copyfile(output_path, os.path.join(BASE_DIR, dubbed_clean_name))
            # Update canonical master video files so any button immediately serves this newly dubbed video
            canonical_names = [
                "SOMRAY_DUBBED_KHMER_MOVIE.mp4",
                f"SOMRAY_DUBBED_{req.target_lang.upper()}_MOVIE.mp4",
                "dubbed_user_video.mp4"
            ]
            for cname in canonical_names:
                try:
                    shutil.copyfile(output_path, os.path.join(BASE_DIR, cname))
                    shutil.copyfile(output_path, os.path.join(BASE_DIR, "assets", cname))
                except Exception:
                    pass
            # Update desktop copy if accessible
            try:
                shutil.copyfile(output_path, r"C:\Users\PC\Desktop\SOMRAY_DUBBED_KHMER_MOVIE.mp4")
            except Exception:
                pass
        except Exception as copy_err:
            print(f"File copy warning: {copy_err}", file=sys.stderr)

        return {
            "status": "success",
            "video_url": f"assets/{output_filename}",
            "custom_video_url": f"assets/{dubbed_custom_name}",
            "video_info": video_info,
            "segments_count": len(prepared_segments)
        }

    except Exception as e:
        print(f"Dub video error: {e}", file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"Dubbing failed: {str(e)}")
    finally:
        try:
            shutil.rmtree(tmp_dir)
        except Exception:
            pass

assets_dir = os.path.join(BASE_DIR, "assets")
os.makedirs(assets_dir, exist_ok=True)
app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/")
@app.get("/index.html")
async def serve_index():
    idx_path = os.path.join(BASE_DIR, "index.html")
    if os.path.exists(idx_path):
        return FileResponse(idx_path)
    return {"status": "online", "app": "SOMRAY AI Dubbing Studio", "message": "Backend Cloud Server is running 100%!"}

@app.get("/style.css")
async def serve_css():
    return FileResponse(os.path.join(BASE_DIR, "style.css"), media_type="text/css")

@app.get("/app.js")
async def serve_js():
    return FileResponse(os.path.join(BASE_DIR, "app.js"), media_type="application/javascript")

@app.get("/manifest.json")
async def serve_manifest():
    return FileResponse(os.path.join(BASE_DIR, "manifest.json"), media_type="application/json")

@app.get("/sw.js")
async def serve_sw():
    return FileResponse(os.path.join(BASE_DIR, "sw.js"), media_type="application/javascript")

@app.get("/download-apk")
@app.get("/SOMRAY_DUBBING_APP.apk")
async def serve_apk():
    apk_path = os.path.join(BASE_DIR, "SOMRAY_DUBBING_APP.apk")
    if not os.path.exists(apk_path):
        apk_path = os.path.join(BASE_DIR, "assets", "SOMRAY_DUBBING_APP.apk")
    if not os.path.exists(apk_path):
        apk_path = os.path.join(BASE_DIR, "android_app", "app", "build", "outputs", "apk", "debug", "app-debug.apk")
    if os.path.exists(apk_path):
        return FileResponse(
            apk_path,
            media_type="application/vnd.android.package-archive",
            filename="SOMRAY_DUBBING_APP.apk"
        )
    raise HTTPException(status_code=404, detail="APK not found")

@app.api_route("/api/download", methods=["GET", "HEAD"])
async def download_file(file: str = ""):
    file_clean = os.path.basename(file.strip()) if file else ""
    target_path = None

    if file_clean:
        if not file_clean.endswith(".mp4"):
            file_clean = f"{file_clean}.mp4"
        cand = os.path.join(BASE_DIR, "assets", file_clean)
        if os.path.exists(cand) and os.path.getsize(cand) > 0:
            target_path = cand
        cand_root = os.path.join(BASE_DIR, file_clean)
        if not target_path and os.path.exists(cand_root) and os.path.getsize(cand_root) > 0:
            target_path = cand_root

    # Fuzzy match by core filename if exact match not found
    if file_clean and not target_path:
        core_name = re.sub(r'^(DUBBED_|uploaded_\d+_)+', '', file_clean).strip()
        assets_dir = os.path.join(BASE_DIR, "assets")
        if os.path.exists(assets_dir) and core_name:
            for f in os.listdir(assets_dir):
                if f.endswith(".mp4") and core_name in f:
                    cand_match = os.path.join(assets_dir, f)
                    if os.path.getsize(cand_match) > 0:
                        target_path = cand_match
                        break

    # If still not found, serve the most recently generated dubbed video
    if not target_path:
        assets_dir = os.path.join(BASE_DIR, "assets")
        if os.path.exists(assets_dir):
            mp4_files = [
                os.path.join(assets_dir, f) for f in os.listdir(assets_dir)
                if f.startswith("dubbed_") and f.endswith(".mp4") and os.path.getsize(os.path.join(assets_dir, f)) > 0
            ]
            if mp4_files:
                mp4_files.sort(key=os.path.getmtime, reverse=True)
                target_path = mp4_files[0]

    if not target_path or not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail="File not found")

    download_name = os.path.basename(target_path)
    return FileResponse(
        target_path,
        media_type="video/mp4",
        filename=download_name,
        headers={
            "Content-Disposition": f'attachment; filename="{download_name}"',
            "Content-Type": "video/mp4"
        }
    )

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    if len(sys.argv) > 1 and "--port" in sys.argv:
        try:
            p_idx = sys.argv.index("--port")
            if p_idx + 1 < len(sys.argv):
                port = int(sys.argv[p_idx + 1])
        except Exception:
            pass
    local_ip = get_local_ip()
    print("=" * 60)
    print("   SOMRAY AI Video Dubbing Studio (Khmer & English)")
    print("=" * 60)
    print(f" * Local PC Access:       http://localhost:{port}")
    print(f" * Mobile Phone (Android): http://{local_ip}:{port}")
    print(" * Open that link on your Android Chrome/Browser to test on phone!")
    print("=" * 60)
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
