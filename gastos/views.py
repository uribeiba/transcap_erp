from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Gasto, GastoRecurrente, CategoriaGasto
from .forms import CategoriaGastoForm
from .forms import GastoForm, GastoRecurrenteForm

# gastos/views.py
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta, date
from calendar import monthrange
import json




class GastoListView(LoginRequiredMixin, ListView):
    model = Gasto
    template_name = 'gastos/gasto_list.html'
    context_object_name = 'gastos'

class GastoCreateView(LoginRequiredMixin, CreateView):
    model = Gasto
    form_class = GastoForm
    template_name = 'gastos/gasto_form.html'
    success_url = reverse_lazy('gastos:lista')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Gasto registrado correctamente.')
        return response

class GastoUpdateView(LoginRequiredMixin, UpdateView):
    model = Gasto
    form_class = GastoForm
    template_name = 'gastos/gasto_form.html'
    success_url = reverse_lazy('gastos:lista')

class GastoDeleteView(LoginRequiredMixin, DeleteView):
    model = Gasto
    success_url = reverse_lazy('gastos:lista')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Gasto eliminado.')
        return super().delete(request, *args, **kwargs)

class GastoDetailView(LoginRequiredMixin, DetailView):
    model = Gasto
    template_name = 'gastos/gasto_detail.html'

# Recurrentes
class RecurrenteListView(LoginRequiredMixin, ListView):
    model = GastoRecurrente
    template_name = 'gastos/recurrente_list.html'
    context_object_name = 'recurrentes'

class RecurrenteCreateView(LoginRequiredMixin, CreateView):
    model = GastoRecurrente
    form_class = GastoRecurrenteForm
    template_name = 'gastos/recurrente_form.html'
    success_url = reverse_lazy('gastos:recurrentes')

class RecurrenteUpdateView(LoginRequiredMixin, UpdateView):
    model = GastoRecurrente
    form_class = GastoRecurrenteForm
    template_name = 'gastos/recurrente_form.html'
    success_url = reverse_lazy('gastos:recurrentes')

class RecurrenteDeleteView(LoginRequiredMixin, DeleteView):
    model = GastoRecurrente
    success_url = reverse_lazy('gastos:recurrentes')
    



# ============================================================
# CRUD Categorías de Gastos
# ============================================================

class CategoriaListView(LoginRequiredMixin, ListView):
    model = CategoriaGasto
    template_name = 'gastos/categoria_list.html'
    context_object_name = 'categorias'
    ordering = ['codigo']

class CategoriaCreateView(LoginRequiredMixin, CreateView):
    model = CategoriaGasto
    form_class = CategoriaGastoForm
    template_name = 'gastos/categoria_form.html'
    success_url = reverse_lazy('gastos:categorias')

    def form_valid(self, form):
        messages.success(self.request, 'Categoría creada correctamente.')
        return super().form_valid(form)

class CategoriaUpdateView(LoginRequiredMixin, UpdateView):
    model = CategoriaGasto
    form_class = CategoriaGastoForm
    template_name = 'gastos/categoria_form.html'
    success_url = reverse_lazy('gastos:categorias')

    def form_valid(self, form):
        messages.success(self.request, 'Categoría actualizada correctamente.')
        return super().form_valid(form)

class CategoriaDeleteView(LoginRequiredMixin, DeleteView):
    model = CategoriaGasto
    success_url = reverse_lazy('gastos:categorias')
    template_name = 'gastos/categoria_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Categoría eliminada correctamente.')
        return super().delete(request, *args, **kwargs)
    

def dashboard_gastos(request):
    hoy = timezone.localdate()
    primer_dia_mes = hoy.replace(day=1)
    mes_anterior = (primer_dia_mes - timedelta(days=1)).replace(day=1)
    
    # Totales del mes actual
    gastos_mes = Gasto.objects.filter(fecha__gte=primer_dia_mes, fecha__lte=hoy)
    total_mes = gastos_mes.aggregate(total=Sum('monto_total'))['total'] or 0
    
    # Totales del mes anterior
    ultimo_dia_mes_anterior = mes_anterior.replace(day=monthrange(mes_anterior.year, mes_anterior.month)[1])
    gastos_mes_anterior = Gasto.objects.filter(fecha__gte=mes_anterior, fecha__lte=ultimo_dia_mes_anterior)
    total_mes_anterior = gastos_mes_anterior.aggregate(total=Sum('monto_total'))['total'] or 0
    
    # Porcentaje de cambio
    if total_mes_anterior > 0:
        cambio = ((total_mes - total_mes_anterior) / total_mes_anterior) * 100
    else:
        cambio = 100 if total_mes > 0 else 0
    
    # Gastos por categoría (mes actual)
    gastos_por_categoria = gastos_mes.values('categoria__nombre').annotate(total=Sum('monto_total')).order_by('-total')
    categorias_labels = [item['categoria__nombre'] for item in gastos_por_categoria]
    categorias_data = [float(item['total']) for item in gastos_por_categoria]
    
    # Evolución últimos 6 meses
    meses = []
    montos_mensuales = []
    for i in range(5, -1, -1):
        fecha = hoy.replace(day=1) - timedelta(days=30*i)
        primer_dia = fecha.replace(day=1)
        ultimo_dia = primer_dia.replace(day=monthrange(primer_dia.year, primer_dia.month)[1])
        total = Gasto.objects.filter(fecha__gte=primer_dia, fecha__lte=ultimo_dia).aggregate(Sum('monto_total'))['monto_total__sum'] or 0
        meses.append(primer_dia.strftime('%b %Y'))
        montos_mensuales.append(float(total))
    
    # Últimos 10 gastos
    ultimos_gastos = Gasto.objects.select_related('categoria').order_by('-fecha')[:10]
    
    context = {
        'total_mes': total_mes,
        'total_mes_anterior': total_mes_anterior,
        'cambio': cambio,
        'categorias_labels': json.dumps(categorias_labels),
        'categorias_data': json.dumps(categorias_data),
        'meses_labels': json.dumps(meses),
        'montos_mensuales': json.dumps(montos_mensuales),
        'ultimos_gastos': ultimos_gastos,
        'fecha_inicio': primer_dia_mes,
        'fecha_fin': hoy,
    }
    return render(request, 'gastos/dashboard.html', context)