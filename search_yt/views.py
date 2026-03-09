import os
import uuid
import numpy as np
import shutil
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from resemblyzer import VoiceEncoder, preprocess_wav
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pydub import AudioSegment
import yt_dlp
from urllib.parse import urlparse, parse_qs
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST

def convert_to_wav_16khz_mono(input_path):
    """
    Convert any supported audio/video → mono 16kHz WAV using pydub + ffmpeg
    Returns path to temporary WAV file
    """
    if input_path.lower().endswith('.wav'):
        # Already wav → we still re-export to ensure 16kHz mono
        pass
    else:
        # Force conversion
        pass

    temp_dir = os.path.dirname(input_path)
    temp_wav_name = f"conv_{uuid.uuid4().hex[:12]}.wav"
    temp_wav_path = os.path.join(temp_dir, temp_wav_name)

    try:
        audio = AudioSegment.from_file(input_path, format=None)  # auto-detect format
        audio = audio.set_channels(1)                            # mono
        audio = audio.set_frame_rate(16000)                      # 16 kHz — good for Resemblyzer
        # Optional: slight normalization (helps with very quiet/loud recordings)
        audio = audio.normalize(headroom=1.0)
        audio.export(temp_wav_path, format="wav")
        return temp_wav_path

    except Exception as e:
        raise RuntimeError(f"Cannot convert {os.path.basename(input_path)} → WAV: {str(e)}")


def save_uploaded_file(uploaded_file, target_dir):
    """Save Django UploadedFile to disk and return path"""
    os.makedirs(target_dir, exist_ok=True)
    path = os.path.join(target_dir, uploaded_file.name)
    with open(path, 'wb+') as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)
    return path
def your_similarity_function(request, orig_path1, orig_path2):
    try:
        # Convert both files
        wav1 = convert_to_wav_16khz_mono(orig_path1)
        wav2 = convert_to_wav_16khz_mono(orig_path2)

        encoder = VoiceEncoder()

        # Resemblyzer expects float32 mono array
        audio1 = preprocess_wav(wav1)
        audio2 = preprocess_wav(wav2)

        emb1 = encoder.embed_utterance(audio1)
        emb2 = encoder.embed_utterance(audio2)

        # Cosine similarity
        sim = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        score_percent = float(sim * 100)

        # Clean temporary WAVs (important on production)
        for p in [wav1, wav2]:
            if p != orig_path1 and p != orig_path2 and os.path.exists(p):
                try:
                    os.remove(p)
                except:
                    pass

        return score_percent

    except Exception as e:
        raise RuntimeError(f"Voice comparison failed: {str(e)}")


def get_channel_video_urls(channel_url, max_videos=50):
    """
    Get list of video URLs from channel using yt-dlp (no API key needed)
    Returns: list of dicts [{ 'url': ..., 'title': ..., 'id': ... }]
    """
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,           # don't download, just metadata
        'playlistend': max_videos,
        'noplaylist': False,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(channel_url, download=False)
            videos = []
            if 'entries' in info:
                for entry in info['entries']:
                    if entry.get('url'):
                        videos.append({
                            'url': f"https://www.youtube.com/watch?v={entry['id']}",
                            'title': entry.get('title', 'Untitled'),
                            'id': entry['id'],
                        })
            return videos[:max_videos]
        except Exception as e:
            raise RuntimeError(f"Failed to fetch channel videos: {str(e)}")


def download_audio_from_youtube(video_url, output_dir):
    """Download audio only as wav using yt-dlp"""
    temp_path = os.path.join(output_dir, f"yt_{uuid.uuid4().hex[:12]}.wav")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': temp_path.replace('.wav', '.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])

    # yt-dlp might save with different name → find it
    for file in os.listdir(output_dir):
        if file.startswith("yt_") and file.endswith(".wav"):
            return os.path.join(output_dir, file)
    raise FileNotFoundError("Downloaded audio not found")


@require_POST
def process_channel_comparison(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Not authenticated"}, status=403)

    try:
        reference_file = request.FILES.get('reference_voice')
        channel_url = request.POST.get('channel_url')
        count = int(request.POST.get('count', 10))
        start_from = int(request.POST.get('start_from', 0))  # for "more" batches

        if not reference_file or not channel_url:
            return JsonResponse({"error": "Missing file or channel URL"}, status=400)

        user_folder = os.path.join(settings.MEDIA_ROOT, "temp", request.user.username)
        os.makedirs(user_folder, exist_ok=True)

        # Save reference once
        ref_path = save_uploaded_file(reference_file, user_folder)

        # Get video list (only once or cache per session later)
        videos = get_channel_video_urls(channel_url, max_videos=start_from + count + 50)
        videos_to_process = videos[start_from : start_from + count]

        results = []

        for idx, video in enumerate(videos_to_process, start=start_from + 1):
            try:
                # Download audio
                yt_audio_path = download_audio_from_youtube(video['url'], user_folder)

                # Compare
                score = your_similarity_function(request, ref_path, yt_audio_path)

                results.append({
                    'index': idx,
                    'video_url': video['url'],
                    'title': video['title'],
                    'similarity': round(score, 2),
                    'status': 'success'
                })

                # Clean temp yt audio
                if os.path.exists(yt_audio_path):
                    os.remove(yt_audio_path)

            except Exception as e:
                results.append({
                    'index': idx,
                    'video_url': video['url'],
                    'title': video['title'],
                    'similarity': None,
                    'status': 'error',
                    'message': str(e)
                })

        return JsonResponse({
            "results": results,
            "next_start": start_from + count,
            "has_more": len(videos) > start_from + count,
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

def channel_voice_search(request):
    if not request.user.is_authenticated:
        return redirect('home')
    return render(request, 'channel_voice_search.html')

@csrf_exempt
def delete_temp_files(request):
    if not request.user.is_authenticated:
        return JsonResponse({"status": "error", "message": "Not authenticated"}, status=403)

    user_dir = os.path.join(settings.MEDIA_ROOT, "temp", request.user.username)
    try:
        if os.path.exists(user_dir):
            shutil.rmtree(user_dir)
        return JsonResponse({"status": "success", "message": "Temp files deleted"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
