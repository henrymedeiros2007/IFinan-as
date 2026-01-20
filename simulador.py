import locale


try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    
    locale.setlocale(locale.LC_ALL, '')

def calcular_investimento(investimento_inicial, aporte_mensal, taxa_anual, prazo_meses):
    
    taxa_mensal = (taxa_anual / 100) / 12

    taxas_ir = [0.225, 0.20, 0.175, 0.15]
    limites_dias = [180, 360, 720] 


    dados_mensais = []
    montante_bruto = investimento_inicial
    total_investido = investimento_inicial
    
    for mes in range(1, prazo_meses + 1):
       
        if mes > 1:
            montante_bruto += aporte_mensal
            total_investido += aporte_mensal

        rendimento_bruto_mes = montante_bruto * taxa_mensal
        montante_bruto += rendimento_bruto_mes

        lucro_bruto_total = montante_bruto - total_investido

        dias = mes * 30 
        if dias <= limites_dias[0]:
            aliquota_ir = taxas_ir[0]
        elif dias <= limites_dias[1]:
            aliquota_ir = taxas_ir[1]
        elif dias <= limites_dias[2]:
            aliquota_ir = taxas_ir[2]
        else:
            aliquota_ir = taxas_ir[3]
        
        imposto_devido = lucro_bruto_total * aliquota_ir
        montante_liquido = montante_bruto - imposto_devido

        dados_mensais.append({
            'mes': mes,
            'total_investido': total_investido,
            'montante_bruto': montante_bruto,
            'lucro_bruto': lucro_bruto_total,
            'imposto_devido': imposto_devido,
            'montante_liquido': montante_liquido
        })
    
    resumo = {
        'valor_final_bruto': montante_bruto,
        'valor_final_liquido': montante_liquido,
        'total_investido': total_investido,
        'total_ganho_bruto': lucro_bruto_total,
        'total_imposto': imposto_devido
    }

    return {'mensal': dados_mensais, 'resumo': resumo}

def format_currency(value):
    return locale.currency(value, grouping=True)


def calcular_financiamento(valor_total, valor_entrada, taxa_juros_anual, prazo_meses):
   

    valor_financiado = valor_total - valor_entrada
    taxa_juros_mensal = (taxa_juros_anual / 100) / 12

   
    try:
        parcela = valor_financiado * ( (taxa_juros_mensal * (1 + taxa_juros_mensal) ** prazo_meses) / ( (1 + taxa_juros_mensal) ** prazo_meses - 1) )
    except ZeroDivisionError:
        return None 

    tabela_amortizacao = []
    saldo_devedor = valor_financiado
    total_juros = 0

    for mes in range(1, prazo_meses + 1):
        juros_mes = saldo_devedor * taxa_juros_mensal
        amortizacao_mes = parcela - juros_mes
        saldo_devedor -= amortizacao_mes
        total_juros += juros_mes
        
        if mes == prazo_meses:
            saldo_devedor = 0.0

        tabela_amortizacao.append({
            'mes': mes,
            'parcela': parcela,
            'juros': juros_mes,
            'amortizacao': amortizacao_mes,
            'saldo_devedor': saldo_devedor
        })

    total_pago = (parcela * prazo_meses) + valor_entrada
    
    resumo = {
        'valor_parcela': parcela,
        'valor_financiado': valor_financiado,
        'total_juros': total_juros,
        'total_pago': total_pago
    }
    
    return {'mensal': tabela_amortizacao, 'resumo': resumo}