import os
import uuid
import numpy as np
import shutil
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from resemblyzer import VoiceEncoder, preprocess_wav
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pydub import AudioSegment


def save_uploaded_file(uploaded_file, target_dir):
    """Save Django UploadedFile to disk and return path"""
    os.makedirs(target_dir, exist_ok=True)
    path = os.path.join(target_dir, uploaded_file.name)
    with open(path, 'wb+') as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)
    return path


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


def comparison_graph(request, embedding1, embedding2):
    embedding1 = np.array(embedding1)
    embedding2 = np.array(embedding2)
    username = request.user.username

    user_folder = os.path.join(settings.MEDIA_ROOT, "temp", username)
    os.makedirs(user_folder, exist_ok=True)

    # LINE CHART
    line_filename = f"line_{uuid.uuid4().hex}.png"
    line_filepath = os.path.join(user_folder, line_filename)

    x = np.arange(len(embedding1))
    plt.figure(figsize=(12, 4))
    plt.plot(x, embedding1, label="Voice 1", color="green")
    plt.plot(x, embedding2, label="Voice 2", color="red", alpha=0.7)
    plt.fill_between(x, embedding1, embedding2, color='gray', alpha=0.15)
    plt.title("Voice Embeddings Comparison — Line")
    plt.xlabel("Dimension")
    plt.ylabel("Value")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig(line_filepath, dpi=120, bbox_inches='tight')
    plt.close()

    # BAR CHART (paired)
    bar_filename = f"bar_{uuid.uuid4().hex}.png"
    bar_filepath = os.path.join(user_folder, bar_filename)

    max_val = max(np.max(embedding1), np.max(embedding2))
    width = 0.38
    x_pos = np.arange(len(embedding1))

    colors1 = []
    colors2 = []
    for v1, v2 in zip(embedding1, embedding2):
        if np.isclose(v1, v2, atol=1e-5):
            colors1.append("gold")
            colors2.append("gold")
        else:
            colors1.append("limegreen")
            colors2.append("tomato")

    plt.figure(figsize=(12, 4.2))
    plt.bar(x_pos - width/2, embedding1 + 1, width, bottom=-1, label="Voice 1", color=colors1)
    plt.bar(x_pos + width/2, embedding2 + 1, width, bottom=-1, label="Voice 2", color=colors2)

    plt.title("Paired Voice Embedding Comparison")
    plt.xlabel("Dimension")
    plt.ylabel("Value (shifted)")
    plt.ylim(-0.05, max_val + 0.15)
    plt.xticks(np.arange(0, len(embedding1), 50))

    equal_patch = mpatches.Patch(color='gold', label='Very similar')
    plt.legend(handles=[
        plt.Line2D([0], [0], color='limegreen', lw=5, label='Voice 1'),
        plt.Line2D([0], [0], color='tomato',    lw=5, label='Voice 2'),
        equal_patch
    ])
    plt.grid(axis='y', linestyle='--', alpha=0.4)

    plt.savefig(bar_filepath, dpi=120, bbox_inches='tight')
    plt.close()

    line_url  = settings.MEDIA_URL + f"temp/{username}/{line_filename}"
    bar_url   = settings.MEDIA_URL + f"temp/{username}/{bar_filename}"

    return line_url, bar_url


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

        line_url, bar_url = comparison_graph(request, emb1, emb2)

        # Clean temporary WAVs (important on production)
        for p in [wav1, wav2]:
            if p != orig_path1 and p != orig_path2 and os.path.exists(p):
                try:
                    os.remove(p)
                except:
                    pass

        return score_percent, line_url, bar_url

    except Exception as e:
        raise RuntimeError(f"Voice comparison failed: {str(e)}")


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


def voice_similarity(request):
    if not request.user.is_authenticated:
        return redirect('home')

    context = {}

    if request.method == 'POST':
        voice1 = request.FILES.get('voice1')
        voice2 = request.FILES.get('voice2')

        if not voice1 or not voice2:
            messages.error(request, "Both voice files are required.")
        else:
            try:
                user_folder = request.user.username
                upload_dir = os.path.join(settings.MEDIA_ROOT, "temp", user_folder)
                
                path1 = save_uploaded_file(voice1, upload_dir)
                path2 = save_uploaded_file(voice2, upload_dir)

                # Now supports video & many audio formats
                similarity_score, graph_url, bar_url = your_similarity_function(request, path1, path2)

                context['result'] = {
                    'score': round(similarity_score, 2),
                    'voice1_url': settings.MEDIA_URL + f"temp/{user_folder}/{voice1.name}",
                    'voice2_url': settings.MEDIA_URL + f"temp/{user_folder}/{voice2.name}",
                    'comparison_graph': graph_url,
                    'bar_chart': bar_url,
                    'message': "Analysis completed successfully.",
                }

                messages.success(request, f"Comparison completed — similarity: {round(similarity_score, 1)}%")

            except Exception as e:
                messages.error(request, f"Error processing files: {str(e)}")

            # Optional: keep originals for preview, clean later via button / cron

    return render(request, 'voice_similarity.html', context)
