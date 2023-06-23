from django.shortcuts import redirect
from django.http import HttpRequest

def main_index(request: HttpRequest):
    return redirect("/monitor/")