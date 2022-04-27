from django.contrib.auth import logout, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.generic import CreateView, DetailView, UpdateView, ListView
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.db.models import Q

from .forms import *
from .models import *
from django.contrib.messages.views import *
from .serializers import CountrySerializer


class GenerateContentMixin:
    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.pk:
            # to find user's profile id
            try:
                profile_id = Profile.objects.get(user_id=self.request.user.pk).id
            except ObjectDoesNotExist:
                pass
            context['profile_id'] = profile_id
        return context


class PartnerDataGenerateMixin:
    def get_partners_queryset(self):
        logined_id = Profile.objects.get(user_id=self.request.user.pk).id
        partners1 = Partner.objects.filter(followed_id=logined_id, response_date__isnull=False).values('follower_id')
        partners2 = Partner.objects.filter(follower_id=logined_id, response_date__isnull=False).values('followed_id')
        partners = partners1.union(partners2)
        partners = Profile.objects.filter(pk__in=partners)
        return partners


class ProfilesView(GenerateContentMixin, ListView):
    model = Profile
    template_name = 'mainapp/index.html'
    paginate_by = 20
    extra_context = {'title': 'Would talk with you'}

    # def get_queryset(self):
    #     queryset = super().get_queryset()
    #     print(queryset)
    #     print(self.request.GET)
    #     queryset = queryset.filter(gender__in=['m', 'f', 'n'],
    #                                study__name__in=['English', 'Greek', 'Italian', 'Turkish'],
    #                                tags__tag__in=['Youtube']).distinct()
    #     return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)

        profiles = []
        for profile in context['profile_list']:
            study = [lang.name for lang in profile.study.all()]
            tags = [tag.tag for tag in profile.tags.all()]
            profiles.append({'id': profile.id,
                             'age': profile.age,
                             'gender': profile.get_gender_display(),
                             'study': study,
                             'tags': tags
                             })
        context['profiles'] = profiles

        # uniq list of languages:
        languages = [profile['study'] for profile in profiles]
        languages = [item for sublist in languages for item in sublist]
        languages = list(set(languages))
        context['languages'] = languages

        # uniq list of tags:
        tags = [profile['tags'] for profile in profiles]
        tags = [item for sublist in tags for item in sublist]
        tags = list(set(tags))
        context['tags'] = tags

        # uniq list of genders:
        genders = [profile['gender'] for profile in profiles]
        genders = list(set(genders))
        context['genders'] = genders

        # uniq list of ages:
        ages = [profile['age'] for profile in profiles]
        ages = [x for x in ages if x is not None]
        ages.sort()
        context['ages'] = ages
        age_groups = {}
        for age in ages:
            if age <= 25:
                age_groups['<25'] = True
            elif age <= 35:
                age_groups['25-35'] = True
            elif age <= 45:
                age_groups['35-45'] = True
            elif age <= 60:
                age_groups['45-60'] = True
            elif age > 60:
                age_groups['60+'] = True
        age_groups = age_groups.keys()
        context['age_groups'] = age_groups

        return context


class RegisterUser(CreateView):
    form_class = RegisterUserForm
    template_name = 'mainapp/register.html'
    success_url = reverse_lazy('login')

    def form_valid(self, form):
        user = form.save()  # creating a user
        login(self.request, user)  # login with new account
        # creating new profile:
        # (old version, now profile creates through signal post_save of User model)
        # profile = Profile(user=user)
        # profile.save()
        return redirect('index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Регистрация'
        return context


class LoginUser(SuccessMessageMixin, LoginView):
    form_class = AuthenticationForm
    template_name = 'mainapp/login.html'
    success_message = 'You were successfully logged in'

    def get_success_url(self):
        return reverse_lazy('index')


def logout_user(request):
    logout(request)
    return redirect('index')


class ProfileView(GenerateContentMixin, PartnerDataGenerateMixin, DetailView):
    model = Profile
    template_name = 'mainapp/profile.html'
    pk_url_kwarg = 'profile_id'
    context_object_name = 'profile'

    def age(self):
        self.model

    extra_context = {'title': 'profile', 'age': age}

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        followed = Profile.objects.get(pk=self.request.POST['followed'])
        follower = Profile.objects.get(pk=self.request.POST['follower'])

        # add following request
        if 'follow_request' in request.POST:
            obj, created = Partner.objects.update_or_create(
                followed=followed, follower=follower)
            if created:
                messages.success(request, 'Request was sent. You will be able to chat after confirming the request')
            else:
                messages.success(request, """You have already sent request. 
                                             Request was updated. 
                                             You will be able to chat after confirming the request""")
        if 'follow_accept' in request.POST:
            Partner.objects.filter(followed=followed, follower=follower).update(response_date=now())
            Partner.objects.filter(follower=followed, followed=follower).update(response_date=now())
        if 'follow_reject' in request.POST:
            Partner.objects.filter(followed=followed, follower=follower).delete()
            Partner.objects.filter(follower=followed, followed=follower).delete()

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_pk = context['object'].pk  # id of seek profile

        # make queryset of visited profiles
        if 'visited_profiles' in self.request.session:
            if profile_pk in self.request.session['visited_profiles']:
                self.request.session['visited_profiles'].remove(profile_pk)
            profiles = self.model.objects.filter(pk__in=self.request.session['visited_profiles'])
            viewed_profiles = sorted(profiles,
                                     key=lambda x: self.request.session['visited_profiles'].index(x.pk))
            context['viewed_profiles'] = viewed_profiles[:5]

            self.request.session['visited_profiles'].insert(0, profile_pk)
            if len(self.request.session['visited_profiles']) > 6:
                self.request.session['visited_profiles'].pop()
        else:
            self.request.session['visited_profiles'] = [profile_pk]
        self.request.session.modified = True

        # make queryset of following requests:
        followers_requests_queryset = Partner.objects.filter(followed_id=profile_pk, response_date__isnull=True)
        context['followers_requests_queryset'] = followers_requests_queryset

        # queryset of partners:
        context['partners'] = self.get_partners_queryset()

        # check if profile sent request to logined profile:
        try:
            logined_id = context['profile_id']
            if Partner.objects.get(follower_id=profile_pk, followed_id=logined_id, response_date__isnull=True):
                context['is_requested'] = True
        except:
            context['is_requested'] = False

        # check if user is follower:
        if context.get('profile_id'):
            is_follower = Partner.objects.filter(follower_id=profile_pk,
                                                 followed_id=logined_id,
                                                 response_date__isnull=False)
            is_followed = Partner.objects.filter(followed_id=profile_pk,
                                                 follower_id=logined_id,
                                                 response_date__isnull=False)
            if is_follower.exists() or is_followed.exists():
                context['is_follower'] = True

        return context


class ProfileUpdateView(LoginRequiredMixin, GenerateContentMixin, UpdateView):
    model = Profile
    form_class = ProfileEditForm
    pk_url_kwarg = 'profile_id'
    template_name = 'mainapp/profile-redacting.html'
    login_url = 'login'
    redirect_field_name = 'profile-redacting'
    context_object_name = 'profile'
    extra_context = {'title': 'redacting'}

    def get_object(self, queryset=None):
        edit_profile_id = self.model.objects.get(user_id=self.request.user.pk).id

        if queryset is None:
            queryset = self.get_queryset()
        queryset = queryset.filter(pk=edit_profile_id)

        try:
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404()
        return obj


class LanguageLevelUpdateView(LoginRequiredMixin, GenerateContentMixin, UpdateView):
    model = LanguageLevel
    form_class = LanguageLevelForm
    pk_url_kwarg = 'profile_id'
    slug_url_kwarg = 'language'
    template_name = 'mainapp/profile-language-level.html'
    login_url = 'login'
    extra_context = {'title': 'language-redacting'}

    def get_object(self, queryset=None):
        language_id = self.kwargs['language']
        profile_id = Profile.objects.get(user=self.request.user.pk).pk
        obj = self.model.objects.get(language=language_id, profile=profile_id)
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile_id'] = Profile.objects.get(user=self.request.user.pk).pk
        context['language_id'] = self.kwargs['language']

        return context


# APIs:
class CountryAPIViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
