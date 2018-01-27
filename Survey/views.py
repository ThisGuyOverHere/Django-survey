# Generic
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, render_to_response, redirect
from django.template import loader, RequestContext
from django.urls import reverse
from django.views.generic import DetailView, ListView, UpdateView
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum, Count, When, Case, F, Q, IntegerField
from django.db import models
# Survey
from .models import Survey
from .models import Topic
from .models import Question
from .models import SubscribedSurveyQuestion
from .models import Completed
#from .models import TopicSurvey
# User
from .models import CustomUser
from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import SignUpForm

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

# Generic   --------------------
def index(request):
    num_surveys = Survey.objects.all().count()
    # Render the HTML template index.html with the data in the context variable
    return render(
        request,
        'index.html',
        context={'num_surveys': num_surveys},
    )

def info(request):
    return render(
        request,
        'info.html'
    )


def handler404(request):
    response = render_to_response('404.html', {},
        context_instance = RequestContext(request)
    )
    response.status_code = 404
    return response


# User      --------------------
# @require_http_methods(['GET', 'POST'])
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST, request.FILES)
        if form.is_valid():
            # Salva
            form.save() # Per salvare il form senza scrivere nel db usare form.save(commit=False)
            # Recupera i dati del form
            id_card = form.cleaned_data.get('id_card')
            raw_password = form.cleaned_data.get('password1')
            # Effettua il login automatico
            user = authenticate(id_card=id_card, password=raw_password)
            login(request,user)
            return redirect('profile')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Passworc cambiata correttamente!')
            return redirect('profile')
        else:
            messages.error(request, 'Correggi gli errori.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {
        'form': form
    })

class CustomUserListView(ListView):
    model = CustomUser
    # template variable
    context_object_name = 'users_list'
    # filter (3 user with id card number containing '012')
    # queryset = CustomUser.objects.filter(id_card__contains='012')[:3]
    # template location
    template_name = 'accounts/custom_user_list.html'


class CustomUserDetailView(DetailView):
    model = CustomUser
    # template variable
    # context_object_name = 'users_list'
    # filter (3 user with id card number containing '012')
    # queryset = CustomUser.objects.filter(id_card__contains='012')[:3]
    # template location
    template_name = 'accounts/custom_user_detail.html'


class CurrentCustomUserDetailView(LoginRequiredMixin, DetailView):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'

    def get_object(self, queryset=None):
        return self.request.user
    template_name = 'accounts/custom_user_detail.html'


class UpdateProfileView(UpdateView):

    def get_object(self, queryset=None):
        return self.request.user

    model = CustomUser
    fields = ['first_name', 'last_name', 'email', 'date_of_birth', 'bio']
    template_name = 'accounts/customuser_update_form.html'


# Survey    --------------------
def survey(request):
    if request.user.is_authenticated():
        surveys = Survey.objects.exclude(completed__user = request.user).annotate(num_questions = Count('topic__question'))

        return render(request, 'survey.html', {'surveys': surveys})
    else:
        return HttpResponseRedirect(reverse('login'))

def survey_questions(request):
    #topics = TopicSurvey.objects.all()
    questions = Question.objects.all()
    return render(request, 'survey_questions.html' , {
        'questions': questions
        })


def question(request, survey_id, topic_id, question_id):
    if request.user.is_authenticated():


        survey = get_object_or_404(Survey, pk = survey_id)
    
        try:
            topic = survey.topic_set.get(pk = topic_id)
            newtopics = survey.topic_set.filter(pk__gt = topic_id)
        except Topic.DoesNotExist:
            raise Http404("No Topic matches the given query")
    
        try:
            question = topic.question_set.get(id = question_id)
    
            #filtriamo le domande appartenenti allo stesso topic con id maggiore della domanda corrente
            remaining_questions = topic.question_set.filter(id__gt = question_id).exclude(Q(subscribedsurveyquestion__questionId = question_id) | Q(subscribedsurveyquestion__username = request.user))
            newtopic = False
            if remaining_questions.exists():
                nextquestion = remaining_questions[0]
            else:
                #Se esiste un altro topic ma non ci sono più domande nel topic corrente preleva la prima domanda del successivo
                if newtopics.exists():
                    for i in range(0, newtopics.count()):
                        newtopic   = Topic.objects.get(pk = newtopics[i].id)
                        nextquestion = newtopic.question_set.filter(id__gt = question_id).exclude(Q(subscribedsurveyquestion__questionId = question_id) | Q(subscribedsurveyquestion__username = request.user))
                        if nextquestion.exists():
                            nextquestion = nextquestion[0]
                            break
                else:
                    nextquestion = False
        except Question.DoesNotExist:
            raise Http404("No Question matches the given query")
        
        if(SubscribedSurveyQuestion.objects.filter(username = request.user, questionId = question_id, surveyId = survey_id).exists()):
            if not newtopic:
                return HttpResponseRedirect(reverse('question', args=(survey.id, topic.id, nextquestion.id,)))
            else:
                return HttpResponseRedirect(reverse('question', args=(survey.id, newtopic.id, nextquestion.id,)))

        return render (request, 'question.html', {
            'survey'       : survey,
            'topic'        : topic,
            'question'     : question,
            'nextquestion' : nextquestion,
            'newtopic'     : newtopic
            })
    else:
        return HttpResponseRedirect(reverse('login'))


def vote(request, question_id):
    question = get_object_or_404(Question, pk = question_id)
    """
    if(request.session.get(str(question_id), False) == True):
        return HttpResponse("You already voted for this question before.")
    """
    answer = request.POST.get('answer', 0)
    survey = request.POST.get('survey', 0)
    topic  = request.POST.get('topic' , 0)
    nextquestion = request.POST.get('nextquestion', 0)
    surveyObject = get_object_or_404(Survey, pk = survey)

    if(SubscribedSurveyQuestion.objects.filter(username = request.user, questionId = question, surveyId = surveyObject).exists()):
        if(nextquestion == '0'):
            return HttpResponseRedirect(reverse('survey'))
    
        return HttpResponseRedirect(reverse('question', args=(survey, topic, nextquestion,)))

    relation = SubscribedSurveyQuestion(username = request.user, questionId = question, surveyId = surveyObject)


    if(answer == '1'):
        question.votes_1 += 1
        relation.choice = question.answer_1
    elif(answer == '2'):
        question.votes_2 += 1
        relation.choice = question.answer_2
    elif(answer == '3'):
        question.votes_3 += 1
        relation.choice = question.answer_3
    else:
        return HttpResponse("You didn't vote anything")
    
    relation.save()
    request.session[str(question_id)] = True
    question.save()
    if(nextquestion == '0'):
        completed = Completed(user = request.user, surveyId = surveyObject)
        completed.save()
        return HttpResponseRedirect(reverse('survey'))

    return HttpResponseRedirect(reverse('question', args=(survey, topic, nextquestion,)))

def skip(request, survey_id):
    survey = get_object_or_404(Survey, pk = survey_id)
    Completed(user = request.user, surveyId= survey).save()
    return HttpResponseRedirect(reverse('survey'))


class ReportData:

    def __init__(self, question, total_votes, percentage_1, percentage_2, percentage_3):
        self.question = question
        self.total_votes   = total_votes
        self.percentage_1  = percentage_1
        self.percentage_2  = percentage_2
        self.percentage_3  = percentage_3

@user_passes_test(lambda u: u.is_superuser)
def report(request, survey_id):
    
    survey = get_object_or_404(Survey, pk = survey_id)
    questions = []
    data = {}
    for topic in survey.topic_set.all():
        questions.append(topic.question_set.all())
        data[topic.topic_title] = []

    for querySet in questions:
        for question in querySet:
            total_votes = question.votes_1 + question.votes_2 + question.votes_3
        
            if(total_votes == 0):
                percentage_1 = 0
                percentage_2 = 0
                percentage_3 = 0
            else:
                percentage_1 = round(100 * float(question.votes_1)/float(total_votes), 2)
                percentage_2 = round(100 * float(question.votes_2)/float(total_votes), 2)
                percentage_3 = round(100 * float(question.votes_3)/float(total_votes), 2)
    
            data[question.topic_id.topic_title].append(ReportData(question, total_votes, percentage_1, percentage_2, percentage_3))
        
    return render(request, 'report.html',{
        'data': data,
        })

