from django import forms
from .models import Producto


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        # Solo pedimos estos datos; el negocio lo asignaremos en automático
        fields = ['nombre', 'descripcion', 'precio', 'categoria']

        # Le damos diseño a las casillas para que combinen con ComidITA
        widgets = {
            'nombre': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Ej. Fresas con crema (Vaso grande)'}),
            'descripcion': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe los ingredientes...'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'min': '0', 'step': '0.01'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
        }