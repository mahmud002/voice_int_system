from django.shortcuts import render, redirect
from django.contrib import messages
import json
import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav
from scipy.spatial.distance import cosine
# Create your views here.
# def check_similarity(request):
#     if not request.user.is_authenticated:
#         return redirect('home')
            
#     return render(request, 'voice_similarity.html')
def your_similarity_function(voice1, voice2):
    return 30
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
                # Your similarity logic here
                similarity_score = your_similarity_function(voice1, voice2)  # 0–100
                
                context['result'] = {
                    'score': round(similarity_score, 1),
                    'message': "Analysis completed successfully."
                }
                messages.success(request, "Comparison completed.")
                
            except Exception as e:
                messages.error(request, f"Error processing files: {str(e)}")
    
    return render(request, 'voice_similarity.html', context)