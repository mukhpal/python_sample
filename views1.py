
from django.db.models   import  Sum
from apps.users.models  import Notification
import boto3
import mimetypes
from datetime import datetime, timedelta, date, timedelta, datetime
from dateutil.relativedelta import relativedelta
from django.shortcuts import render, redirect
from django.db import transaction
from django.contrib.auth import  logout
from django.contrib import messages
from django.contrib.auth import get_user_model
from .forms import  UploadVideoForm
from .models import CoachVideo,  Sport
from apps.users.models import CoachDetails,  SubscriptionPlan, UserSubscriptionPlan, 
from apps.editor.api.utils import get_video_thumbnail, get_video_duration
from django.conf import settings

UserModel = get_user_model()
session = boto3.Session(
        settings.AWS_ACCESS_KEY_ID,
        settings.AWS_SECRET_ACCESS_KEY
)

#video filter according to date
def get_coach_videos(request, coach):
    tournament  = request.GET.get('tournament', None)
    age_group   = request.GET.get('age_group', None)
    created     = request.GET.get('created', None)
    sports      = request.GET.get('sports', None)

    kwarge = {}
    if tournament:
        kwarge['tournament']    = tournament
    if age_group:
        kwarge['age_group']     = age_group
    if created == "t_w":
        kwarge['created__gte']  = date.today() + relativedelta(days=-7)
    if created == "l_w":
        kwarge['created__gte']  = date.today() + relativedelta(days=-14)
        kwarge['created__lt']   = date.today() + relativedelta(days=-7)
    if created == "t_m":
        kwarge['created__gte']  = date.today() + relativedelta(days=-30)
    if created == "l_m":
        kwarge['created__gte']  = date.today() + relativedelta(days=-60)
        kwarge['created__lt']   = date.today() + relativedelta(days=-30)
    if sports:
        kwarge['sports'] = sports

    try:
        coach_video = CoachVideo.objects.filter( caoch=coach, completed=1, **kwarge).order_by("-created")
        for item in coach_video:
            item.length = str(timedelta(seconds=round(item.length)))
    except CoachVideo.DoesNotExist:
        coach_video = None

    return coach_video

#Notifications function
def notificationview(request):
    notification = Notification.objects.filter( user_id=request.user.id, is_read=False).order_by("-id")

    return notification


# function component for coach panel
def index(request):
    template_name = "coach/index.html"

    if not request.user.is_authenticated:
        return redirect('login')
    if not request.user.plan:
        coach = CoachDetails.objects.get(user=request.user.id)
        if coach.club_id:
            return redirect('clubCoach')
        else:
            return redirect('coach-plans')
    else:
        plan_sub    = SubscriptionPlan.objects.get(id=request.user.plan_id)
        plan        = UserSubscriptionPlan.objects.get(plan=plan_sub, is_active=True,user=request.user)
        time        = datetime.utcnow()
        endtime     = plan.plan_end_date+timedelta(minutes=30)
        if time.replace(tzinfo=None) >= endtime.replace(tzinfo=None): 
            plan.is_active = 0
            plan.save()
            messages.success(
                request, "Plan has been Expired Please upgrade plan")

            return redirect('coach-plans')
        else:
            pass

    if not request.user.user_type == "COACH":
        messages.success(request, "Session Expired")
        logout(request)
        return redirect('login')

    coach = None
    try:
        coach = CoachDetails.objects.get(user_id=request.user.pk)
        # print(coach)
    except CoachDetails.DoesNotExist:
        coach = None 

    if coach:
        coach_video = get_coach_videos(request, coach)
    else:
        coach_video = None

    try:
        tournaments = CoachVideo.objects.filter( caoch=coach, completed=1).order_by().values('tournament').distinct()
    except CoachVideo.DoesNotExist:
        tournaments = None
    try:
        age_group = CoachVideo.objects.filter( caoch=coach, completed=1,).order_by().values('age_group').distinct()
    except CoachVideo.DoesNotExist:
        age_group = None

    try:
        sports = CoachVideo.objects.filter(caoch=coach, completed=1, sports__isnull=False).order_by().values('sports').distinct()
    except CoachVideo.DoesNotExist:
        sports = None

    if request.method == "POST":
        form = UploadVideoForm(request.POST, request.FILES)

        if form.is_valid():
            with transaction.atomic():
                new_voideo          = form.save(commit=False)
                new_voideo.caoch    = coach
                new_voideo.save()

                path                = new_voideo.file.path
                filename            = new_voideo.file.name
                upload_to           = '/coach/thumbnail/'

                file_mime           = mimetypes.guess_type(path)
                content_type        = file_mime[0]
                type                = content_type.split('/')[0]

                new_voideo.file_extension   = content_type.split('/')[1]
                new_voideo.content_type     = content_type
                new_voideo.file_size        = new_voideo.file.size

                if type == "video":
                    n_thumbnai                  = get_video_thumbnail(path, filename, upload_to)
                    new_voideo.thumbnail.name   = n_thumbnai[1:]

                    new_voideo.length           = get_video_duration(path)
                    new_voideo.save()
                else:
                    new_voideo.thumbnail        = file
                    new_voideo.save()
                messages.success(request, "video uploaded successfully.")
            return redirect('coach-index')

        else:
            messages.error(request, "form is not validate")
            print(form.errors)
            return render(request, template_name, {
                "coach_video"   : coach_video,
                "age_group"     : age_group,
                'tournaments'   : tournaments,
                "sports"        : sports,
                "form"          : form.errors
            })

    form            = UploadVideoForm()
    sport1          = Sport.objects.filter(user=request.user)
    coach_video1    = CoachVideo.objects.filter( caoch=coach, completed=1, created__gte=date.today() + relativedelta(days=-7)).order_by("-created")
    
    for item in coach_video1:
        item.length = str(timedelta(seconds=round(item.length)))

    coach_video2    = CoachVideo.objects.filter(caoch=coach, completed=1, created__gte=date.today() + relativedelta(days=-90)).order_by("-created")
    for item in coach_video2:
        item.length = str(timedelta(seconds=round(item.length)))

    data            = notificationview(request)
    coachVideos     = CoachVideo.objects.filter(caoch=coach, completed=0)
    balance         = list(coachVideos.values_list('pk', flat=True))
    if not balance:
        balance     = 0
    try:
        totalPageall    = coach_video.count()/settings.pageLimit
        remainder       = coach_video.count()%settings.pageLimit

        if isinstance(totalPageall, float):
            if round(totalPageall) != 1 and round(totalPageall) != 0 or (remainder!=0 and remainder<5):
                if((remainder!=0 and remainder<5)):
                    pagesCount =  round(totalPageall)+1
                else:
                    pagesCount =  round(totalPageall)
            else:
                    pagesCount =  round(1)
        else:
            pagesCount =  round(totalPageall)
    except Exception as err:
        pass
    try:
        totalPageall    = coach_video1.count()/settings.pageLimit
        remainder       = coach_video1.count()%settings.pageLimit
        if isinstance(totalPageall, float):
            if round(totalPageall) != 1 and round(totalPageall) != 0 or (remainder!=0 and remainder<5):
                if((remainder!=0 and remainder<5)):
                    pagesCounttw =  round(totalPageall)+1
                else:
                    pagesCounttw =  round(totalPageall)     
            else:
                    pagesCounttw =  round(1)
        else:
            pagesCounttw =  round(totalPageall)
    except Exception as err:
        pass
    try:
        totalPageall    = coach_video2.count()/settings.pageLimit
        remainder       = coach_video2.count()%settings.pageLimit
        if isinstance(totalPageall, float):
            if round(totalPageall) != 1 and round(totalPageall) != 0 or (remainder!=0 and remainder<int(settings.reminderTime)):
                if((remainder!=0 and remainder<5)):
                    pagesCountlm =  round(totalPageall)+1
                else:
                    pagesCountlm =  round(totalPageall)
            else:
                    pagesCountlm =  round(1)
        else:
            pagesCountlm =  round(totalPageall)
    except Exception as err:
        pass
  
    try:
        coach       = CoachDetails.objects.get(user=request.user)
        usages      = CoachVideo.objects.filter( caoch=coach).aggregate(Sum('file_size'))
        if usages:
            user            = request.user
            user.totalusage = usages['file_size__sum']
            user.save()   
    except:
        pass
    return render(request, template_name, {
        "coach_video"           :   coach_video,
        "pagesCount"            :   range(pagesCount),
        "filter_coach_video"    :   coach_video1,
        "pagesCounttw"          :   range(pagesCounttw),
        "get_last_month"        :   coach_video2,
        "pagesCountlm"          :   range(pagesCountlm),
        "age_group"             :   age_group,
        'tournaments'           :   tournaments,
        "sports"                :   sports,
        "sports1"               :   sport1,
        "form"                  :   form,
        "notification"          :   data,
        "process"               :   balance
    })