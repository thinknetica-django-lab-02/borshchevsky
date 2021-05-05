import logging

from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models.query import QuerySet
from django.forms.models import ModelForm
from django.http import HttpResponseRedirect
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from django.views.generic import DetailView, ListView, UpdateView, CreateView
from django.views.generic.base import ContextMixin

from market.settings import DEFAULT_GROUP_NAME, STATICFILES_URL
from . import email_messages
from .forms import UserForm, ProfileFormSet
from .models import Product, Profile, SMSLog
from .tasks import send_novelty_task
from .utils import send_sms, search_product

logger = logging.getLogger(__name__)


def index(request: HttpRequest) -> HttpResponse:
    search_text = request.GET.get('search')
    queryset = None
    if search_text:
        queryset = search_product(search_text)

    return render(request, 'index.html', {
        'queryset': queryset,
    })


class ProductListView(ListView):
    model = Product
    paginate_by = 10

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()
        tag = self.request.GET.get('tag')
        if tag:
            return queryset.filter(tags__tag_name=tag)
        return queryset

    def get_context_data(self, *, object_list: ContextMixin = None, **kwargs) -> dict:
        data = super().get_context_data()
        tag = self.request.GET.get('tag')
        data['tag'] = tag
        return data


class ProductDetailView(DetailView):
    model = Product

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        page_id_views = f'{context["product"].id}_views'
        current_page_views = cache.get(page_id_views, 0)
        current_page_views += 1
        cache.set(page_id_views, current_page_views, timeout=60)
        context['page_views'] = current_page_views
        return self.render_to_response(context)


class ProfileUpdate(UpdateView):
    model = User
    form_class = UserForm
    template_name = 'main/profile_form.html'
    success_url = '/accounts/profile/'

    def get_object(self, request):
        return request.user

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['profile_form'] = ProfileFormSet(instance=self.get_object(kwargs['request']))
        return context

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        self.object = self.get_object(request)
        return self.render_to_response(self.get_context_data(request=request))

    def form_valid_formset(self, form: ModelForm, formset: ProfileFormSet) -> HttpResponseRedirect:
        if formset.is_valid():
            formset.save(commit=False)
            formset.save()
        else:
            return HttpResponseRedirect(self.get_success_url())
        form.save()
        return HttpResponseRedirect(self.get_success_url())

    def post(self, request, *args, **kwargs):
        if request.POST.get('verify'):
            self._verify_number(request)
        self.object = self.get_object(request)
        form = self.get_form()
        profile_form = ProfileFormSet(self.request.POST, self.request.FILES, instance=self.object)
        if form.is_valid():
            return self.form_valid_formset(form, profile_form)
        else:
            return self.form_invalid(form)

    def _verify_number(self, request: HttpRequest) -> None:
        user = User.objects.get(username=request.user.username)
        profile = Profile.objects.get(user=user)
        phone_number = profile.phone_number
        if phone_number:
            code, response_data = send_sms(phone_number)
            messages.success(request, 'A message with a verification code has been sent to your phone number.')
            try:
                code_query = SMSLog.objects.get(user=user)
                code_query.delete()
            finally:
                SMSLog.objects.create(user=user, code=code, server_response=response_data)


class CreateProduct(CreateView):
    model = Product
    fields = ['category', 'tags', 'title', 'description', 'width', 'height', 'depth', 'weight', 'image']
    template_name_suffix = '_create_form'


class UpdateProduct(UpdateView):
    model = Product
    fields = '__all__'
    template_name_suffix = '_update_form'


# @receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Group.objects.get_or_create(name=DEFAULT_GROUP_NAME)
        instance.groups.add(Group.objects.get(name=DEFAULT_GROUP_NAME))
        Profile.objects.create(user=User.objects.get(username=instance))

        if instance.email:
            send_mail(
                subject='Welcome.',
                message='Hello.',
                from_email='admin@example.com',
                recipient_list=[instance.email],
                fail_silently=False,
                html_message=email_messages.welcome
            )


# @receiver(post_save, sender=Product)
def send_novelty(instance, **kwargs):
    send_novelty_task.delay(instance.id)


def robots_view(request):
    return render(request, 'robots.txt')
