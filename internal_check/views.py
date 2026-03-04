import tempfile
import os
import numpy as np
from django.shortcuts import render, redirect
from django.contrib import messages
from resemblyzer import VoiceEncoder, preprocess_wav



#search_youtube
def search_youtube(request):

    return render(request, 'search_youtube.html') 

# Function to compute similarity
def your_similarity_function(path1, path2):
    encoder = VoiceEncoder()

    # Preprocess the wav files (converts to float, mono, trims silence)
    wav1 = preprocess_wav(path1)
    wav2 = preprocess_wav(path2)

    # Create embeddings
    embedding1 = encoder.embed_utterance(wav1)
    embedding2 = encoder.embed_utterance(wav2)

    # Cosine similarity
    similarity = np.dot(embedding1, embedding2) / (
        np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
    )

    # Convert to percentage
    return float(similarity * 100)


# Django view for voice comparison
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
                # Save voice1 temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp1:
                    for chunk in voice1.chunks():
                        tmp1.write(chunk)
                    path1 = tmp1.name

                # Save voice2 temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp2:
                    for chunk in voice2.chunks():
                        tmp2.write(chunk)
                    path2 = tmp2.name

                # Compute similarity
                similarity_score = your_similarity_function(path1, path2)

                context['result'] = {
                    'score': round(similarity_score, 2),
                    'message': "Analysis completed successfully.",
                    'file_name': f"{voice1.name} Vs {voice2.name}"
                }

                messages.success(request, "Comparison completed.")

            except Exception as e:
                messages.error(request, f"Error processing files: {str(e)}")

            finally:
                # Clean up temp files
                if 'path1' in locals() and os.path.exists(path1):
                    os.remove(path1)
                if 'path2' in locals() and os.path.exists(path2):
                    os.remove(path2)

    return render(request, 'voice_similarity.html', context)