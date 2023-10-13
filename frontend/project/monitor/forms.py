from datetime import datetime, timedelta
# from dateutil.relativedelta import relativedelta
from django import forms

class MyDateInput(forms.widgets.DateInput):
    input_type = 'date'

class SelectDateForm(forms.Form):
    im_start_date = forms.DateField(label="start date", widget=MyDateInput, initial=datetime.now()-timedelta(days=3))
    im_end_date = forms.DateField(label="end date", widget=MyDateInput, initial=datetime.now())
    # start_date = forms.DateField(label="start date", widget=forms.SelectDateWidget, initial=datetime.now())
    # time_hours_list = [(h, h) for h in range(0, 24)]
    # time_minuts_list = [(min, min) for min in range(0, 60, 5)]
    # start_date = forms.DateField(label="start date", widget=forms.SelectDateWidget, initial=datetime.now())
    # start_time_h =  forms.ChoiceField(label='', choices=time_hours_list)
    # start_time_m =  forms.ChoiceField(label='', choices=time_minuts_list)
    im_start_time = forms.DateField(widget=forms.DateInput(attrs={'class':'timepicker', 'style':'width:65px', 'placeholder': '00:00:00', 'value': '00:00:00'}))
    im_end_time = forms.DateField(widget=forms.DateInput(attrs={'class':'timepicker', 'style':'width:65px', 'placeholder': '23:59:59', 'value': '23:59:59'}))
    
    sm_start_date = forms.DateField(label="start date", widget=MyDateInput, initial=datetime.now()-timedelta(days=3))
    sm_end_date = forms.DateField(label="end date", widget=MyDateInput, initial=datetime.now())
    sm_start_time = forms.DateField(widget=forms.DateInput(attrs={'class':'timepicker', 'style':'width:65px', 'placeholder': '00:00:00', 'value': '00:00:00'}))
    sm_end_time = forms.DateField(widget=forms.DateInput(attrs={'class':'timepicker', 'style':'width:65px', 'placeholder': '23:59:59', 'value': '23:59:59'}))

    sys_start_date = forms.DateField(label="start date", widget=MyDateInput, initial=datetime.now()-timedelta(days=3))
    sys_end_date = forms.DateField(label="end date", widget=MyDateInput, initial=datetime.now())
    sys_start_time = forms.DateField(widget=forms.DateInput(attrs={'class':'timepicker', 'style':'width:65px', 'placeholder': '00:00:00', 'value': '00:00:00'}))
    sys_end_time = forms.DateField(widget=forms.DateInput(attrs={'class':'timepicker', 'style':'width:65px', 'placeholder': '23:59:59', 'value': '23:59:59'}))

    all_start_date = forms.DateField(label="start date", widget=MyDateInput, initial=datetime.now()-timedelta(days=3))
    all_end_date = forms.DateField(label="end date", widget=MyDateInput, initial=datetime.now())
    all_start_time = forms.DateField(widget=forms.DateInput(attrs={'class':'timepicker', 'style':'width:65px', 'placeholder': '00:00:00', 'value': '00:00:00'}))
    all_end_time = forms.DateField(widget=forms.DateInput(attrs={'class':'timepicker', 'style':'width:65px', 'placeholder': '23:59:59', 'value': '23:59:59'}))