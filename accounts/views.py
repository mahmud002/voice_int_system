from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm


def home(request):
 
    if request.user.is_authenticated:         
        return render(request, 'home.html')
    else:
        return redirect("/accounts/login")



def register(request):
    # If already logged in → go to home
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Automatically log the user in after successful registration
            login(request, user)
            messages.success(request, "Account created successfully. Welcome!")
            return redirect('home')
        else:
            # If form invalid, show errors (they will appear in template)
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})


def user_login(request):
    # If already logged in → go to home
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Authenticate using email (because we use email as USERNAME_FIELD)
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.email}!")
            return redirect('/')
        else:
            messages.error(request, "Invalid email or password.")
    # GET request or failed login → show empty form
    return render(request, 'login.html')


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, "You have been logged out.")
    return redirect('home')