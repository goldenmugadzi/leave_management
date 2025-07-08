from django.db import models
from django.contrib.auth.hashers import make_password, check_password

from it.users.models import UserProfile

# Create your models here.
        
class Question(models.Model):
    question = models.CharField(max_length=255)
    question_name = models.CharField(max_length=255)

    def __str__(self):
        return self.question

class SecurityQuestions(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    security_question = models.ForeignKey(Question, on_delete=models.CASCADE)
    security_answer = models.CharField(max_length=255)

    def set_security_answers(self, answer):
        self.security_answer = make_password(answer)

    def check_security_answers(self, answer):
        return check_password(answer, self.security_answer)
