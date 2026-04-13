from django import forms
from .models import ProjectStage, Project
from accounts.models import User


class ProjectStageForm(forms.ModelForm):
    class Meta:
        model = ProjectStage
        fields = ['name', 'description', 'status', 'notes', 'started_at', 'completed_at']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'started_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'completed_at': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if not isinstance(field.widget, (forms.Textarea, forms.DateTimeInput)):
                field.widget.attrs.update({'class': 'form-control'})
        self.fields['status'].widget.attrs.update({'class': 'form-select'})


class AssignStaffForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['assigned_staff', 'start_date', 'expected_end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'expected_end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_staff'].queryset = User.objects.filter(role__in=['staff', 'admin'])
        self.fields['assigned_staff'].widget.attrs.update({'class': 'form-select'})
