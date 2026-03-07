import tempfile
import os
import numpy as np
from django.shortcuts import render, redirect
from django.contrib import messages
from resemblyzer import VoiceEncoder, preprocess_wav
from django.conf import settings
import shutil
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse 
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import uuid
import matplotlib.patches as mpatches

#search_youtube
def search_youtube(request):

    return render(request, 'search_youtube.html') 



def comparison_graph(request, embedding1, embedding2):
    embedding1 = np.array(embedding1)
    embedding2 = np.array(embedding2)
    username = request.user.username

    # Create user temp folder
    user_folder = os.path.join(settings.MEDIA_ROOT, "temp", username)
    os.makedirs(user_folder, exist_ok=True)

    # --- LINE CHART ---
    line_filename = f"line_comparison_{uuid.uuid4().hex}.png"
    line_filepath = os.path.join(user_folder, line_filename)

    x = np.arange(len(embedding1))
    plt.figure(figsize=(12, 4))
    plt.plot(x, embedding1, label="Voice 1", color="green")
    plt.plot(x, embedding2, label="Voice 2", color="red", alpha=0.5)
    plt.fill_between(x, embedding1, embedding2, color='gray', alpha=0.2)
    plt.title("Voice Embeddings Comparison (Line Chart)")
    plt.xlabel("Embedding Index")
    plt.ylabel("Value")
    plt.legend()
    plt.grid(True)
    plt.savefig(line_filepath)
    plt.close()

    # --- BAR CHART ---
    bar_filename = f"bar_comparison_{uuid.uuid4().hex}.png"
    bar_filepath = os.path.join(user_folder, bar_filename)
    max_value = max(np.max(embedding1), np.max(embedding2))
    width = 0.4
    x = np.arange(len(embedding1))

    voice1_colors = []
    voice2_colors = []

    for v1, v2 in zip(embedding1, embedding2):
        if np.isclose(v1, v2, atol=1e-5):
            voice1_colors.append("yellow")
            voice2_colors.append("yellow")
        else:
            voice1_colors.append("green")
            voice2_colors.append("red")

    plt.figure(figsize=(12,4))

    # bars start from -1
    plt.bar(x - width/2, embedding1 + 1, width, bottom=-1, label="Voice 1", color=voice1_colors)
    plt.bar(x + width/2, embedding2 + 1, width, bottom=-1, label="Voice 2", color=voice2_colors)

    plt.title("Voice Embedding Comparison (Paired Bars)")
    plt.xlabel("Embedding Index")
    plt.ylabel("Value")

    # Force axis range
    plt.ylim(-0.03, max_value+0.05)

    # X labels every 50
    plt.xticks(np.arange(0, len(embedding1), 50))

    # Optional: create a custom patch for equal values
    equal_patch = mpatches.Patch(color='yellow', label='Maching')

    # Add legend
    plt.legend(handles=[plt.Line2D([0], [0], color='green', lw=6, label='Voice 1'),
                        plt.Line2D([0], [0], color='red', lw=6, label='Voice 2'),
                        equal_patch])
    plt.grid(axis="y", linestyle="-", alpha=0.5)

    plt.savefig(bar_filepath)
    plt.close()
    # Return both URLs
    line_url = settings.MEDIA_URL + f"temp/{username}/{line_filename}"
    bar_url = settings.MEDIA_URL + f"temp/{username}/{bar_filename}"

  

    # URLs
    line_url = settings.MEDIA_URL + f"temp/{username}/{line_filename}"
    bar_url = settings.MEDIA_URL + f"temp/{username}/{bar_filename}"
    

    return line_url, bar_url
def your_similarity_function(request, path1, path2):
    encoder = VoiceEncoder()

    # Preprocess the wav files (converts to float, mono, trims silence)
    wav1 = preprocess_wav(path1)
    wav2 = preprocess_wav(path2)

    # Create embeddings
    embedding1 = encoder.embed_utterance(wav1)
    embedding2 = encoder.embed_utterance(wav2)
    
    file_path, barchart =comparison_graph(request, embedding1,embedding2)
    
    # Cosine similarity
    similarity = np.dot(embedding1, embedding2) / (
        np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
    )

    # Convert to percentage
    return float(similarity * 100), file_path, barchart

@csrf_exempt
def delete_temp_files(request):
    user_dir = os.path.join(settings.MEDIA_ROOT, "temp", request.user.username)
    try:
        if os.path.exists(user_dir):
            shutil.rmtree(user_dir)  
        return JsonResponse({"status": "temp file deleted"})
    except Exception as e:
        # In case something goes wrong
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

                # Save files in MEDIA/temp/<username>/
                upload_dir = os.path.join(settings.MEDIA_ROOT, "temp", user_folder)
                os.makedirs(upload_dir, exist_ok=True)

                path1 = os.path.join(upload_dir, voice1.name)
                path2 = os.path.join(upload_dir, voice2.name)

                with open(path1, 'wb+') as f:
                    for chunk in voice1.chunks():
                        f.write(chunk)

                with open(path2, 'wb+') as f:
                    for chunk in voice2.chunks():
                        f.write(chunk)

                # Compute similarity
                similarity_score, comparison_graph, barchart = your_similarity_function(request,path1, path2)

                context['result'] = {
                    'score': round(similarity_score, 2),
                    'voice1_url': settings.MEDIA_URL + f"temp/{user_folder}/{voice1.name}",
                    'voice2_url': settings.MEDIA_URL + f"temp/{user_folder}/{voice2.name}",
                    'comparison_graph': comparison_graph,
                    'bar_chart': barchart,
                   
                    
                    'message': "Analysis completed successfully.",

                }

                messages.success(request, "Comparison completed.")

            except Exception as e:
                messages.error(request, f"Error processing files: {str(e)}")

    return render(request, 'voice_similarity.html', context)

# Django view for voice comparison
# def voice_similarity(request):
#     if not request.user.is_authenticated:
#         return redirect('home')

#     context = {}

#     if request.method == 'POST':
#         voice1 = request.FILES.get('voice1')
#         voice2 = request.FILES.get('voice2')
#         if not voice1 or not voice2:
#             messages.error(request, "Both voice files are required.")
#         else:
#             try:
#                 # Save voice1 temporarily
#                 with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp1:
#                     for chunk in voice1.chunks():
#                         tmp1.write(chunk)
#                     path1 = tmp1.name

#                 # Save voice2 temporarily
#                 with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp2:
#                     for chunk in voice2.chunks():
#                         tmp2.write(chunk)
#                     path2 = tmp2.name

#                 # Compute similarity
#                 similarity_score = your_similarity_function(path1, path2)

#                 context['result'] = {
#                     'score': round(similarity_score, 2),
#                     'message': "Analysis completed successfully.",
#                     'voice1_url': path1,

#                 }

#                 messages.success(request, "Comparison completed.")

#             except Exception as e:
#                 messages.error(request, f"Error processing files: {str(e)}")

#             finally:
#                 # Clean up temp files
#                 if 'path1' in locals() and os.path.exists(path1):
#                     os.remove(path1)
#                 if 'path2' in locals() and os.path.exists(path2):
#                     os.remove(path2)

#     return render(request, 'voice_similarity.html', context)