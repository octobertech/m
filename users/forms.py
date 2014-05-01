#import uuid
from django import forms
#from django.forms.formsets import BaseFormSet

from mikiapp import models

class LoginForm(forms.Form):
    username = forms.CharField(max_length=30, required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    def clean(self):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        try:
            user = models.get_user_by_username(username)
        except models.DatabaseError:
            raise forms.ValidationError(u'Invalid username and/or password')
        if user.get('password') != password:
            raise forms.ValidationError(u'Invalid username and/or password')
        return self.cleaned_data

    def get_username(self):
        return self.cleaned_data['username']


class RegistrationForm(forms.Form):
    username = forms.RegexField(regex=r'^\w+$', max_length=30)
    password = forms.CharField(widget=forms.PasswordInput(render_value=False))
    repeat_password = forms.CharField(widget=forms.PasswordInput(render_value=False))

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            models.get_user_by_username(username)
            raise forms.ValidationError(u'Username is already taken')
        except models.DatabaseError:
            pass
        return username

    def clean(self):
        if ('password' in self.cleaned_data and 'repeat_password' in
            self.cleaned_data):
            password = self.cleaned_data['password']
            repeat_password = self.cleaned_data['repeat_password']
            if password != repeat_password:
                raise forms.ValidationError(
                    u'You must type the same password each time')
        return self.cleaned_data

    def save(self):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        models.save_user(username, password)
        return username


class SettingsForm(forms.Form):
    username = forms.RegexField(regex=r'^\w+$', max_length=30, required=True)
    new_username = forms.RegexField(regex=r'^\w+$', max_length=30)
    password = forms.CharField(widget=forms.PasswordInput(render_value=True), required=True)
    new_password = forms.CharField(widget=forms.PasswordInput(render_value=False))
    name = forms.CharField(max_length=40)
    about = forms.CharField(max_length=140)
    pic = forms.ImageField()
    url = forms.URLField()

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            models.get_user_by_username(username)
            raise forms.ValidationError(u'Username is already taken')
        except models.DatabaseError:
            pass
        return username

    def clean(self):
        if 'password' in self.cleaned_data:
            password = self.cleaned_data['password']
        if 'new_password' in self.cleaned_data:
            new_password = self.cleaned_data['new_password']
        if password == new_password:
            raise forms.ValidationError(u'You have typed the same password')
        return self.cleaned_data

    def get_username(self):
        return self.cleaned_data['username']

    def save(self):
        username = self.cleaned_data['username']
        password = self.cleaned_data['password']
        new_password = self.cleaned_data['new_password']
        name = self.cleaned_data['name']
        about = self.cleaned_data['about']
        pic = self.cleaned_data['pic']
        url = self.cleaned_data['url']

        if new_password:
            password = new_password

        models.save_profile(username, password, name, about, pic, url)
        return username

