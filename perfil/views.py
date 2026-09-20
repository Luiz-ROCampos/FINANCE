from django.shortcuts import render, redirect
from .models import Conta, Categoria
from extrato.models import Valores
from contas.models import ContaPagar, ContaPaga
from django.contrib import messages
from django.contrib.messages import constants
from .utils import calcula_total, calcula_equilibrio_financeiro
from datetime import datetime

def home(request):
    contas = Conta.objects.all()
    valores = Valores.objects.filter(data__month=datetime.now().month)
    entradas = valores.filter(tipo='E')
    saidas = valores.filter(tipo='S')
    
    total_entradas = calcula_total(entradas, 'valor')
    total_saidas = calcula_total(saidas, 'valor')
    total_livre = total_entradas - total_saidas
    
    saldo_total = calcula_total(contas, 'valor')
    
    percentual_essenciais, percentual_nao_essenciais = calcula_equilibrio_financeiro()
    
    MES_ATUAL = datetime.now().month
    DIA_ATUAL = datetime.now().day
       
    contas_pagar = ContaPagar.objects.all()
   
    contas_pagas = ContaPaga.objects.filter(data_pagamento__month=MES_ATUAL).values('conta')
   
    contas_vencidas = contas_pagar.filter(dia_pagamento__lt=DIA_ATUAL).exclude(id__in=contas_pagas).count()
    
    contas_proximas_vencimento = contas_pagar.filter(dia_pagamento__lte = DIA_ATUAL + 5).filter(dia_pagamento__gte=DIA_ATUAL).exclude(id__in=contas_pagas).count()

    return render(request, 'home.html', {'contas': contas, 
                                         'saldo_total': saldo_total, 
                                         'total_entradas': total_entradas, 
                                         'total_saidas': total_saidas,
                                         'total_livre': total_livre,
                                         'percentual_essenciais': int(percentual_essenciais),
                                         'percentual_nao_essenciais': int(percentual_nao_essenciais),
                                         'contas_vencidas': contas_vencidas, 
                                         'contas_proximas_vencimento': contas_proximas_vencimento })

def gerenciar(request):
    contas = Conta.objects.all()
    categorias = Categoria.objects.all()
    total_contas = calcula_total(contas, 'valor')
    
    return render(request, 'gerenciar.html', {'contas': contas, 'total_contas': total_contas, 
                                              'banco_choices': Conta.banco_choices, 'tipo_choices': Conta.tipo_choices, 
                                              'categorias': categorias })

def cadastrar_banco(request):
    apelido = request.POST.get('apelido')
    banco = request.POST.get('banco')
    tipo = request.POST.get('tipo')
    valor = request.POST.get('valor')
    icone = request.FILES.get('icone')
    
    if (len(apelido.strip()) == 0 or len(valor.strip()) == 0) or icone is None:
        messages.add_message(request, constants.ERROR, 'Preencha todos os campos')
        return redirect('/perfil/gerenciar/')
    
    conta = Conta(
        apelido = apelido,
        banco=banco,
        tipo=tipo,
        valor=valor,
        icone=icone
    )

    conta.save()
    messages.add_message(request, constants.SUCCESS, 'Conta cadastrada com sucesso')
    return redirect('/perfil/gerenciar/')

def deletar_banco(request, id):
    conta = Conta.objects.get(id=id)
    conta.delete()
    messages.add_message(request, constants.SUCCESS, 'Conta deletada com sucesso')
    return redirect('/perfil/gerenciar/')

def cadastrar_categoria(request):
    nome = request.POST.get('categoria')
    essencial = bool(request.POST.get('essencial'))

    if len(nome.strip()) == 0 or essencial is None:
        messages.add_message(request, constants.ERROR, 'Preencha todos os campos')
        return redirect('/perfil/gerenciar/')
    
    categoria = Categoria(
        categoria=nome,
        essencial=essencial
    )

    categoria.save()
    messages.add_message(request, constants.SUCCESS, 'Categoria cadastrada com sucesso')
    return redirect('/perfil/gerenciar/')

def update_categoria(request, id):
    categoria = Categoria.objects.get(id=id)
    categoria.essencial = not categoria.essencial
    categoria.save()
    return redirect('/perfil/gerenciar/')

def dashboard(request):
    dados = {}
    
    categorias = Categoria.objects.all().exclude(categoria='Pagamento')
    for categoria in categorias:
        total = 0
        valores = Valores.objects.filter(categoria=categoria).filter(tipo='S')
        for valor in valores:
            total += valor.valor
        
        dados[categoria.categoria] = total

    return render (request, 'dashboard.html', {'labels': list(dados.keys()), 'values': list(dados.values())})


