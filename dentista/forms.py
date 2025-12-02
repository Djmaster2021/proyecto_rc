# dentista/forms.py
from django import forms
from .models import Pago
from django import forms
from domain.models import Paciente

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = "__all__"

class FinalizarConsultaForm(forms.Form):
    monto = forms.DecimalField(
        label="Monto a cobrar",
        max_digits=10,
        decimal_places=2,
    )
    metodo = forms.ChoiceField(
        label="Método de pago",
        choices=Pago.METODOS,
    )
    pagado = forms.BooleanField(
        label="Pago realizado",
        required=False,
        initial=True,
        help_text="Desmarca si el paciente aún no ha pagado."
    )
    notas = forms.CharField(
        label="Notas",
        widget=forms.Textarea(attrs={"rows": 3}),
        required=False,
    )
