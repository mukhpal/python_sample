
import threading
from rest_framework import serializers
from django.db.models import Q
from django.contrib.auth import get_user_model
from dj_rest_auth.registration.serializers import RegisterSerializer
from apps.base.send_email import send_welcome_create_mail, verification_mail
from apps.users.utils import generate_username
from apps.users.models import  UserSubscriptionPlan
from django.core import serializers as SERIAL
User = get_user_model()

def serializeData(data):
    return SERIAL.serialize('json', [data, ])

#Custom register serializer
class CustomRegisterSerializer(RegisterSerializer):
    name            = serializers.CharField()
    username        = serializers.CharField(read_only=True)
    user_type       = serializers.CharField(required=False)
    club_code       = serializers.CharField(required=False)
    applicableTax   = serializers.IntegerField(required=True)
    country         = serializers.CharField(required=True)
    country_id      = serializers.IntegerField(required=True)
    state_id        = serializers.IntegerField(required=True)
    def validate(self, data):
        if data['user_type']=="COACH":
            if not data['club_code']:
                raise serializers.ValidationError("Club code not provided.")
            if not ClubDetails.objects.filter(club_code=data['club_code']).exists():
                raise serializers.ValidationError("club_code not valid.")
        return data
    #cleaning data serializer
    def get_cleaned_data(self):
        super(CustomRegisterSerializer, self).get_cleaned_data()
        name            = self.validated_data.get('name', '')
        new_name        = name.split()
        first_name      = new_name[0]
        user_type       = self.validated_data.get('user_type', '')
        club_code       = self.validated_data.get('club_code', '')
        applicableTax   = self.validated_data.get('applicableTax', '')
        country         = self.validated_data.get('country', '')
        country_id      = self.validated_data.get('country_id','')
        state_id        = self.validated_data.get('applicableTax', '')

        try:
            last_name = new_name[1]
        except IndexError:
            last_name = ''

        username = generate_username(first_name, last_name)

        return {
            'username'      : username,
            'password1'     : self.validated_data.get('password1', ''),
            'password2'     : self.validated_data.get('password2', ''),
            'email'         : self.validated_data.get('email', ''),
            'name'          : name,
            'first_name'    : first_name,
            'last_name'     : last_name,
            'user_type'     : user_type,
            'club_code'     : club_code,
            'applicableTax' : applicableTax,
            'country'       : country,
            'country_id'    : country_id,
            'state_id'      : state_id
        }

    def custom_signup(self, request, user):
        context = {
                    "subject": "Welcome to Athleta Media",
                    "email":user.email,
                    'user':user.name,
                    'url': request._current_scheme_host
                }
        t = threading.Thread(target=send_welcome_create_mail, args=[
                                user.email, context])
        t.setDaemon(True)
        t.start()
        context1 = {
                        "subject": "Verification mail",
                        "email":user.email,
                        "name":user.name,
                        'url': request._current_scheme_host+'/verifyuser/'+str(user.id)
                    }
        t = threading.Thread(target=verification_mail, args=[
                                            user.email, context1])
        t.setDaemon(True)
        t.start()
         
        user.club_code      =   self.validated_data.get('club_code', '')
        user.verified       =   0
        user.user_type      =   self.validated_data.get('user_type', '').upper()
        user.country        =   self.validated_data.get('country', '')
        user.applicableTax  =   self.validated_data.get('applicableTax', '')
        user.state_id       =   self.validated_data.get('applicableTax', '')
        user.country_id     =   self.validated_data.get('country_id','')
        user.save()
        


class UploadUserPhotoSerializer(serializers.Serializer):
    photo = serializers.FileField(
        max_length=100000,
        required=True,
        allow_empty_file=False,
        use_url=True
    )


class UserSerializer(serializers.ModelSerializer):
    date_joined = serializers.DateTimeField(format="%m-%d-%Y")
    paid_status = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", 'uuid', 'last_name', 'name', 'photo',
                  'user_type', 'is_active',"club_code", 'city', 'state', 'country', 'date_joined', "name", 'phone_number','plan','totalusage','plan_id','applicableTax','is_admin_plan','paid_status']

    def get_paid_status(self, obj):
        try:          
            data = UserSubscriptionPlan.objects.filter(user_id = obj.id,is_active=True).exists()
            if data:
                check_status =UserSubscriptionPlan.objects.get(user_id = obj.id,is_active=True)
                if int(check_status.amount) == 0:
                    status = 'Free'
                else:
                    status ='paid'
            else: 
                status= 'Free'
           
        except:
            status = 'Free'
        return status