from django import forms

class MikiForm(forms.Form):
    body = forms.CharField(max_length=200)