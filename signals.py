
from flask import request
import stripe
import threading
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.conf import settings
from pyfcm import FCMNotification
from .models import User, StripeCustomer, UserSubscriptionPlan, SubscriptionPlan, create_subscribe
from django.contrib.auth import get_user_model
User = get_user_model()

from django.conf import settings



@receiver(pre_save, sender  =   User, dispatch_uid="add_user_info")
def add_user_info_during_creation(sender, instance, **kwargs):
    if not instance.pk:
        return False
    t = threading.Thread(target=update_user,args=[sender, instance])
    t.setDaemon(True)
    t.start()

#update user and creating subscription plan
def update_user(sender, instance):
    try:
        # if not instance.user_type=="PLAYER":
            try:
                customer    = StripeCustomer.objects.get(user=instance)
            except StripeCustomer.DoesNotExist:
                try:
                    stripe_customer_id  = get_stripe_customer_id(instance)
                except Exception as e:
                    print(str(e))
                stripe_customer_id = get_stripe_customer_id(instance)
                # stripe API
                StripeCustomer.objects.create(
                    stripe_customer_id=stripe_customer_id,
                    user=instance
                )
                default_plan = SubscriptionPlan.objects.get(is_default=True)# This is trial plan

                # Creating default Trial plan for register user.
                result =  create_subscribe(stripe_customer_id, default_plan.stripe_month_plan_id)
                print(result)
                try:
                    UserSubscriptionPlan.objects.create(
                        user        =   instance,
                        plan        =   default_plan,
                        plan_name   =   default_plan.name,
                        amount      =   default_plan.monthly_price,
                        plan_interval           =   'month',
                        stripe_subscription_id  =   result['id'],
                        stripe_customer_id      =   stripe_customer_id,
                        stripe_plan_id          =   default_plan.stripe_month_plan_id,
                        plan_amount_currency    =   settings.STRIPE_CURRENCY
                        
                        )
                except Exception as e:
                    print(str(e))
    except Exception as e:
        print(str(e))

def get_stripe_customer_id(instance):
    # stripe.api_key = settings.STRIPE_SECRET_KEY
    # stripe API
    stripe.api_key = settings.STRIPE_API_KEY
    stripe_obj =  stripe.Customer.create(
            email= instance.email,
            name=instance.name,
            shipping = {
                    'name':'default',
                    'address':{
                            'line1':'default',
                            'country':'us'
                        }
                    }            
        )
    return stripe_obj['id']