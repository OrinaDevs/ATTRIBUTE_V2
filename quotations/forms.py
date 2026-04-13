from django import forms
from .models import Quotation
from services.models import Service


class QuotationRequestForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ['service', 'property_location', 'property_size', 'description', 'urgency', 'additional_notes']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'additional_notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, service=None, **kwargs):
        super().__init__(*args, **kwargs)
        if service:
            self.fields['service'].initial = service
            self.fields['service'].widget = forms.HiddenInput()
        for field in self.fields.values():
            if not isinstance(field.widget, forms.HiddenInput):
                field.widget.attrs.update({'class': 'form-control'})
        self.fields['urgency'].widget.attrs.update({'class': 'form-select'})
        self.fields['service'].widget.attrs.update({'class': 'form-select'})


class QuotationReviewForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ['quoted_amount', 'staff_notes', 'status', 'valid_until']
        widgets = {
            'staff_notes': forms.Textarea(attrs={'rows': 4}),
            'valid_until': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Staff can only set these statuses
        self.fields['status'].choices = [
            ('under_review', 'Under Review'),
            ('awaiting_client', 'Send to Client (Approved)'),
            ('rejected', 'Reject'),
        ]
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        self.fields['status'].widget.attrs.update({'class': 'form-select'})


class ClientResponseForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ['client_response_notes']
        widgets = {
            'client_response_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
