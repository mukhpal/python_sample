from django.db import models
from decimal import Decimal
import uuid
from django.contrib.auth.models import AbstractUser
from django.db.models import CharField
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.db import models
from apps.users.api.serializers import generate_username
from django.conf import settings

#choice feild data 
METHOD_CHOICE_FIELDS= (
    ('POST', 'POST'),
    ('GET', 'GET'),
    ('PUT', 'PUT'),
    ('PATCH', 'PATCH'),
    ('DELETE', 'DELETE'),    
)

CONTENT_CHOICE_FIELDS= (
    ('application/json', 'application/json'),

)

#api model 
class APIDocs(models.Model):
    app_name    = models.CharField( default='', max_length=50)
    description = models.CharField( default='', max_length=50)
    method_type = models.CharField(choices=METHOD_CHOICE_FIELDS, default=None, max_length=50)
    parameter_content_type  =  models.CharField(choices=CONTENT_CHOICE_FIELDS, default=None, max_length=50)
    end_point       =   models.CharField(max_length=500, default=None)
    status_code     =   models.IntegerField(default=None, null=True)
    parameters      =   models.TextField( default=None, )
    api_response    =   models.TextField( default=None, )
    created         =   models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'app_api_docs'

    def __str__(self):
        return self.end_point

#api response model
class APIResponse(models.Model):
    api = models.ForeignKey(APIDocs, on_delete=models.CASCADE)

    class Meta:
        db_table = 'app_api_response'

    def __str__(self):
        return str(self.id)

#User Model 
class User(AbstractUser):

    # First Name and Last Name do not cover name patterns
    # around the globe.
    COACH = 'COACH'
    CLUB = 'CLUB'
    PLAYER = 'PLAYER'
    ADMIN = 'ADMIN'

    USER_TYPE_CHOICES = [
        (COACH, 'COACH'),
        (CLUB, 'CLUB'),
        (PLAYER, 'PLAYER'),
        (ADMIN, 'ADMIN'),
    ]

    uuid                    =   models.UUIDField( primary_key=False, default=uuid.uuid4, editable=False)
    name                    =   CharField(_("Name of User"), blank=True, max_length=255)
    photo                   =   models.ImageField(upload_to='media/users_photo/', default="users_photo/saheem1234xyzabcd.png", null=True, blank=True, verbose_name=_("photo"))
    user_type               =   CharField(blank=True, null=True, max_length=20, default=None, choices=USER_TYPE_CHOICES)
    club_code               =   CharField(blank=True, max_length=20, null=True,  default=None)
    phone_number            =   models.CharField(null=True, max_length=12)
    pwd_reset_code          =   models.CharField(max_length=10, default=None, null=True)
    pwd_reset_code_datetime =   models.DateTimeField(default=None, null=True)
    city                    =   CharField(blank=True, max_length=50)
    state                   =   CharField(blank=True, max_length=50)
    country                 =   CharField(blank=True, max_length=50)
    last_seen               =   models.DateTimeField(default=None, null=True)
    deviceToken             =   CharField(blank=True, max_length=500)
    is_online               =   models.BooleanField(null=True)
    plan                    =   models.CharField(null=True,max_length=255)
    zip                     =   models.IntegerField(null=True)
    is_social_auth          =   models.BooleanField(default=False)  # if social login account
    provider                =   CharField(blank=True, null=True, max_length=50,  default=0)
    social_id               =   CharField(blank=True, null=True, max_length=100,  default=0)
    # true if password changed after social login
    is_social_pwd_reset     =   models.BooleanField(default=False)
    totalusage              =   models.DecimalField(max_digits=20, decimal_places=2, default=Decimal(0.00))
    plan_id                 =   models.IntegerField(null=True)
    verified                =   models.BooleanField(null=True)
    reminder                =   models.BooleanField(null=True)
    applicableTax           =   models.IntegerField(null=True)
    country_id              =   models.IntegerField(null=True,default=0)
    state_id                =   models.IntegerField(null=True,default=0)
    is_admin_plan           =   models.BooleanField(null=True,default=0)

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})

    def save(self, *args, **kwargs):
        if getattr(self, '_image_changed', True):
            fullname    =   self.first_name + " " + self.last_name
            self.name   =   fullname.strip()


            if not self.username:
                first_name      = self.first_name
                last_name       = self.last_name
                self.username   = generate_username(first_name, last_name)

        super(User, self).save(*args, **kwargs)


class StripeCustomer(models.Model):
    user = models.OneToOneField(to=User, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255)

    def __str__(self):
        return self.user.username


def create_stripe_plans(product_id, plan_name, description, price, interval):
    stripe_id = stripe.Plan.create(
                                amount      =   price,
                                currency    =   "CAD",
                                interval    =   interval,
                                product     =   product_id,
                                # trial_period_days=30
                            )

    return stripe_id


def update_stripe_plans(product_id, is_active):
    stripe_id = stripe.Plan.modify(
        product     =   product_id,
        # trial_period_days=30
    )

    return stripe_id

#creating Subscriptions 
def create_subscribe(stripe_cust_id, plan_id):
    stripe.api_key = settings.STRIPE_API_KEY

    subscribe = stripe.Subscription.create(
        customer                =   stripe_cust_id,
        cancel_at_period_end    =   True,
        items=[
            {"price": plan_id},
        ],
    )
    return subscribe


class SubscriptionPlan(SafeDeleteModel):
    """
    subscription plan 
    """

    Monthly = 'month'
    Yearly = 'year'

    INTERVAL_CHOISES = (
        (Monthly, 'month'),
        (Yearly, 'year'),
    )

    name                    =   models.CharField(max_length=100, default=None, null=True)
    basic_detail            =   models.CharField(max_length=100, default=None, null=True)
    description             =   models.TextField(default=None, null=True)
    additionDescription     =   models.TextField(default=None, null=True)
    monthly_price           =   models.FloatField(default=0)
    yearly_price            =   models.FloatField(default=0)
    stripe_month_plan_id    =   models.CharField( max_length=100, default=None, null=True)
    stripe_year_plan_id     =   models.CharField( max_length=100, default=None, null=True)
    stripe_product_id       =   models.CharField( max_length=100, default=None, null=True)
    is_popular              =   models.BooleanField(default=False)
    is_active               =   models.BooleanField(default=True)
    is_default              =   models.BooleanField(default=False)
    uuid                    =   models.UUIDField( primary_key=False, default=uuid.uuid4, editable=False)
    is_club_plan            =   models.BooleanField(default=False)
    is_coach_plan           =   models.BooleanField(default=False)
    is_player_plan          =   models.BooleanField(default=False)
    storage                 =   models.IntegerField(default=0)
    userCount               =   models.IntegerField(default=0)
    is_meet                 =   models.BooleanField(default=False)
    class Meta:
        db_table            =   'subscription_plan'
        verbose_name        =   'subscription plan'
        verbose_name_plural =   'subscription plans'

    def __str__(self):
        return str(self.name)

    #Creating Price and plans
    def save(self, *args, **kwargs):
        if not self.id:
            stripe.api_key = settings.STRIPE_API_KEY

            product     = stripe.Product.create(
                name=self.name,
                description=self.description
            )
            product_id                  = product['id']
            self.stripe_product_id      = product_id
            monthly_price               = round(float(self.monthly_price)*100)
            yearly_price                = round(float(self.yearly_price)*100)
            stripe_plan_month           = create_stripe_plans( product_id, self.name, self.description, monthly_price, 'month' )
            stripe_plan_year            = create_stripe_plans( product_id, self.name, self.description, yearly_price, 'year')
            self.stripe_month_plan_id   = stripe_plan_month['id']
            self.stripe_year_plan_id    = stripe_plan_year['id']

            if not self.is_default:
                return super(SubscriptionPlan, self).save(*args, **kwargs)
            with transaction.atomic():
                SubscriptionPlan.objects.filter(
                    is_default=True).update(is_default=False)
                return super(SubscriptionPlan, self).save(*args, **kwargs)
        else:

            return super(SubscriptionPlan, self).save(*args, **kwargs)