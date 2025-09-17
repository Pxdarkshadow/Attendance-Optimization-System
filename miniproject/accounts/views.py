import pprint
from datetime import datetime
from . import forms
from django.core.mail import EmailMessage
from . tokens import generate_token
from miniproject import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.utils.encoding import force_bytes,force_str
from django.contrib.auth.decorators import login_required
from .models import Subject, TimeTable, AcademicCalendar
import csv


# Create your views here.
def home(request):
    return render(request, 'accounts/index.html')

def signup(request):
    if request.method == "POST":
        pprint.pprint(vars(request)) # For my understanding
        username = request.POST.get('username')
        fname = request.POST['fname']
        lname = request.POST.get('lname')
        email = request.POST['email']
        pass1 = request.POST.get('pass1')
        pass2 = request.POST['pass2']

        if User.objects.filter(username=username):
            messages.error(request, "Username already exists! Please try some other username")
            return redirect('home')

        if User.objects.filter(email=email):
            messages.error(request, "Email already exists! Please try some other Email")
            return redirect('home')
        
        if len(username)>10:
            messages.error(request, "Username must be under 10 characters!")
            return redirect('home')
        
        if pass1!=pass2:
            messages.error(request, "Passwords didn't match!")
            return redirect('home')

        if not username.isalnum():
            messages.error(request, "Username must be alphanumeric!")
            return redirect('home')

        myuser = User.objects.create_user(username, email, pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.is_active = True

        myuser.save()

        messages.success(request, "Your Account has been successfully created.")

        # Welcome Email

        subject = "Welcome to AttendEase"
        message = f'Hello {myuser.first_name}! \n Welcome to AttendEase! \n Thank You for visiting our website! \n We have also sent you a confirmation email, please confirm your email address inorder to activate your account\n Thanking You - MegaTron'
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject, message, from_email, to_list, fail_silently=True)

        # Confirmation Email

        current_site = get_current_site(request)
        email_subject = "Activate your account by confirming your email"
        message2 = render_to_string('email_confirmation.html',{
            'name':myuser.first_name,
            'domain':current_site.domain,
            'uid':urlsafe_base64_encode(force_bytes(myuser.pk)),
            'token':generate_token.make_token(myuser),
        })

        email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [myuser.email],
        )

        email.fail_silently = True
        email.send()

        return redirect('signin')


    return render(request, 'accounts/signup.html')

def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        pass1 = request.POST.get('pass1')
        print("Username:", username)
        print("Password:", pass1)

        user = authenticate(request, username=username, password=pass1)
        print("User object:", user)

        # form = forms.InputTimeTable()

        if user is not None:
            login(request, user)
            # return render(request, "accounts/dashboard.html", {'fname': user.first_name, 'form':form})
            return render(request, "accounts/homepage.html", {'fname': user.first_name})
        else:
            return HttpResponse("Invalid credentials")
    
    return render(request, 'accounts/signin.html')


def signout(request):
    logout(request)
    messages.success(request, "Logged Out successfully")
    return redirect('home')

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        myuser = None

    if myuser is not None and generate_token.check_token(myuser, token):
        myuser.is_active = True
        myuser.save()
        login(request, myuser)
        return redirect('home')
    else:
        return render(request, 'activation_failed.html')
    
# def user_input(request):
#     if request.method == 'POST':
#         pass
#     return render(request, 'accounts/dashboard.html')



@login_required 
def upload_acdcalendar(request):
    if request.method == "POST" and request.FILES.get("file"):
        csv_file = request.FILES["file"]

        # Check if it’s a CSV
        if not csv_file.name.endswith('.csv'):
            return render(request, "accounts/dashboard2.html", {"error": "Please upload a CSV file"})
        
        file_data = csv_file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(file_data)


        for row in reader:
            date_str = row.get('date', '')
            # Convert '30-08-2025' to a Python date object
            date_obj = datetime.strptime(date_str, '%d-%m-%Y').date() if date_str else None
            AcademicCalendar.objects.create(
                user=request.user,
                date=date_obj,
                context=row.get('context', '')
            )

        messages.success(request,"Successfully entered Academic Calendar in the database.")

        return redirect('insights')

    return render(request, "accounts/dashboard2.html")

def userprofile(request):
    return render(request,"accounts/userprofile.html")

# Test
@login_required 
def homepage(request):
    return render(request,"accounts/homepage.html")

@login_required 
def userinput(request):
    if request.method == "POST":
        if request.POST.get('totalSubjects') is not None:
            # Step 1: show form for subjects
            return render(request, "accounts/db1.html", {
                'totalSubjects': range(1, int(request.POST.get('totalSubjects')) + 1)
            })
        else:
            total_subjects = len([k for k in request.POST.keys() if k.startswith("subject") and not k.endswith("Faculty")])

            for index in range(1, total_subjects + 1):
                subject_name = request.POST.get(f"subject{index}")
                faculty_name = request.POST.get(f"subject{index}Faculty")

                if subject_name and faculty_name:
                    Subject.objects.create(
                        subjectName=subject_name,
                        facultyName=faculty_name,
                        user=request.user
                    )

            return render(request, "accounts/db2.html")

    return render(request, "accounts/db1.html", {'totalSubjects': None})

@login_required  # ensures only signed-in users can access
def upload_timetable(request):
    if request.method == "POST" and request.FILES.get("file"):
        csv_file = request.FILES["file"]

        # Check if it’s a CSV
        if not csv_file.name.endswith('.csv'):
            return render(request, "accounts/db2.html")

        # Read CSV file
        file_data = csv_file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(file_data)

        # Loop through rows and create Timetable entries
        for row in reader:

            subject_name = row['Subject']  # string from CSV
            subject_instance = Subject.objects.get(subjectName=subject_name)
            TimeTable.objects.create(
                user=request.user, # link to logged-in user
                day=row['Day'],
                startTime=row['StartTime'],
                endTime=row['EndTime'],
                subject=subject_instance 
                        
                # time=row['Time'],           # ensure CSV has column 'time'
                # monday=row.get('Monday', ''),
                # tuesday=row.get('Tuesday', ''),
                # wednesday=row.get('Wednesday', ''),
                # thursday=row.get('Thursday', ''),
                # friday=row.get('Friday', '')
            )

        messages.success(request,"Successfully entered the timetable in the database. Upload Academic Calendar!")

        return render(request, "accounts/db3.html") 
    return render(request, "accounts/db2.html")


@login_required  # ensures only signed-in users can access
def upload_academiccalendar(request):
    if request.method == "POST" and request.FILES.get("file"):
        csv_file = request.FILES["file"]

        # Check if it’s a CSV
        if not csv_file.name.endswith('.csv'):
            return render(request, "accounts/db3.html")

        # Read CSV file
        file_data = csv_file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(file_data)

        # Loop through rows and create Timetable entries
        for row in reader:
            AcademicCalendar.objects.create(
                user=request.user, # link to logged-in user
                date=row['date'],
                context=row['context'])

        messages.success(request,"Successfully entered the Academic Calendar in the database!")

        return render(request, "accounts/db3.html") 
    return render(request, "accounts/db3.html")