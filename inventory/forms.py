from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth.models import User
from .models import (
    ModelIndent, GPR, ConsumableRegister, Instructor, Trade,
    DemandNote, DemandItem, FINANCIAL_YEAR_CHOICES,
)


# ─── Instructor Registration ────────────────────────────────────────────────

# ─── User Profile ───────────────────────────────────────────────────────────

class UserUpdateForm(forms.ModelForm):
    """Form for users to update their profile information."""
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_first_name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_last_name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'id': 'id_email',
            }),
        }


# ─── Demand Note (Header) ───────────────────────────────────────────────────

class DemandNoteForm(forms.ModelForm):
    """Form for the demand note header (semester, FY, remarks)."""

    class Meta:
        model = DemandNote
        fields = ['semester_no', 'financial_year', 'remarks']
        widgets = {
            'semester_no': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'id': 'id_semester_no',
            }),
            'financial_year': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_financial_year',
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Optional notes or justification',
                'id': 'id_remarks',
            }),
        }


# ─── Demand Item (Line Item) ────────────────────────────────────────────────

class DemandItemForm(forms.ModelForm):
    """Form for a single line item within a demand note."""

    class Meta:
        model = DemandItem
        fields = ['item', 'quantity_required']
        widgets = {
            'item': forms.Select(attrs={
                'class': 'form-select item-select',
            }),
            'quantity_required': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Qty',
            }),
        }


# Inline formset: multiple DemandItems within a DemandNote
DemandItemFormSet = inlineformset_factory(
    DemandNote,
    DemandItem,
    form=DemandItemForm,
    extra=3,          # Start with 3 empty rows
    min_num=1,        # At least 1 item required
    validate_min=True,
    can_delete=True,
)


# ─── StoreKeeper: Edit Demand Note ──────────────────────────────────────────

class EditDemandNoteForm(forms.ModelForm):
    """StoreKeeper can edit status + header of any demand note."""

    class Meta:
        model = DemandNote
        fields = ['semester_no', 'financial_year', 'status', 'remarks']
        widgets = {
            'semester_no': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
            }),
            'financial_year': forms.Select(attrs={
                'class': 'form-select',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
            }),
        }


# ─── GPR ─────────────────────────────────────────────────────────────────────

class GPRForm(forms.ModelForm):
    """Form for store-keepers to add a GPR (purchase) entry."""

    class Meta:
        model = GPR
        fields = [
            'inward_date', 'supplier_name', 'item',
            'item_qty', 'bill_no', 'gpr_no', 'financial_year',
            'register_no', 'page_no', 'item_no', 'sub_entry'
        ]
        widgets = {
            'inward_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'supplier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'item': forms.Select(attrs={'class': 'form-select'}),
            'item_qty': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'bill_no': forms.TextInput(attrs={'class': 'form-control'}),
            'gpr_no': forms.TextInput(attrs={'class': 'form-control'}),
            'financial_year': forms.Select(attrs={'class': 'form-select'}),
            'register_no': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'GPR No'}),
            'page_no': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Page'}),
            'item_no': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Index'}),
            'sub_entry': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Sub'}),
        }


# ─── CR Allocation ───────────────────────────────────────────────────────────

class AllocateToCRForm(forms.ModelForm):
    """Form to allocate GPR stock to an instructor via CR."""

    class Meta:
        model = ConsumableRegister
        fields = ['instructor', 'opening_bal', 'register_no', 'page_no', 'item_no', 'sub_entry']
        widgets = {
            'instructor': forms.Select(attrs={'class': 'form-select'}),
            'opening_bal': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'placeholder': 'Quantity'}),
            'register_no': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'CR No'}),
            'page_no': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Page'}),
            'item_no': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Index'}),
            'sub_entry': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Sub'}),
        }
        labels = {
            'opening_bal': 'Quantity to Allocate',
        }

    def __init__(self, *args, item=None, **kwargs):
        super().__init__(*args, **kwargs)
        if item:
            instructor_ids = DemandItem.objects.filter(
                item=item,
                demand_note__status__in=['SUBMITTED', 'MERGED']
            ).values_list('demand_note__instructor_id', flat=True).distinct()
            if instructor_ids:
                self.fields['instructor'].queryset = Instructor.objects.filter(
                    pk__in=instructor_ids
                )
