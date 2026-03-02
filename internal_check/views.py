from django.shortcuts import render

# Create your views here.
def check_similarity(request):
            
    return render(request, 'voice_similarity.html')
