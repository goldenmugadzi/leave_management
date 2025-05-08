from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.conf import settings

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

class LoginAttempt(models.Model):
    username = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    successful = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        
    @classmethod
    def get_recent_attempts(cls, username, window_minutes=30):
        """Get login attempts within the specified time window"""
        cutoff = timezone.now() - timezone.timedelta(minutes=window_minutes)
        return cls.objects.filter(username=username, timestamp__gt=cutoff)
        
    @classmethod
    def is_user_locked_out(cls, username, max_attempts=5, window_minutes=30):
        """Check if a user is locked out due to too many failed attempts"""
        recent_attempts = cls.get_recent_attempts(username, window_minutes)
        failed_attempts = recent_attempts.filter(successful=False).count()
        return failed_attempts >= max_attempts

class PasswordResetAttempt(models.Model):
    """Track password reset requests for rate limiting"""
    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    successful = models.BooleanField(default=False)  # If email exists in system
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']

class PasswordResetToken(models.Model):
    """Track password reset tokens for single-use and expiry"""
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    token = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    expiry = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created']

class PasswordHistory(models.Model):
    """Track password history to prevent reuse"""
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    password_hash = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created']

class SecurityQuestionAttempt(models.Model):
    """Track security question verification attempts for rate limiting"""
    username = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=500, blank=True, null=True)
    successful = models.BooleanField(default=False)
    question_id = models.IntegerField(default=0)  # Store which question was attempted
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']

class SecurityVerificationToken(models.Model):
    """Track security question verification tokens for limited-time password reset"""
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    token = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    expiry = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created']

def check_password_history(user, new_password, history_limit=5):
    """Check if password has been used before (within history limit)"""
    # Get recent password history entries
    history_entries = PasswordHistory.objects.filter(user=user).order_by('-created')[:history_limit]
    
    # Check if the new password matches any in history
    for entry in history_entries:
        if check_password(new_password, entry.password_hash):
            return True  # Password found in history
    
    return False  # Password not found in history
