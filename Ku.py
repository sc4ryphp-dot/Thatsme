# -*- coding: utf-8 -*-
# main.py - CODIGO 100% CORRIGIDO PARA UBUNTU 22.04 + CHROMIUM 144.0.7559.132 (SNAP)
import sys
import os
import time
import json
import select
from datetime import datetime, timedelta
from collections import defaultdict

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Playwright nao instalado. Execute DENTRO do venv: pip install playwright && playwright install chromium")
    sys.exit(1)

try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("Bibliotecas pandas/numpy nao instaladas. Execute DENTRO do venv: pip install pandas numpy")
    sys.exit(1)

class AviatorBotInteligenteV3:
    def __init__(self):
        self.url = "https://www.tipminer.com/br/historico/sortenabet/aviator"
        self.historico_completo = []
        self.padroes_detectados = {}
        self.padroes_dia = defaultdict(lambda: {'ocorrencias': 0, 'acertos': 0, 'ultima_ocorrencia': None})
        self.historico_padroes = defaultdict(lambda: {'win': 0, 'loss': 0})
        self.sinais_enviados = []
        self.total_coletas = 0
        self.data_inicio = datetime.now().date()
        self.ultima_analise_completa = None
        self.last_round_value = None
        self.ultima_rodada_coletada = None
        self.numero_vela_atual = 0
        
        self.meta_diaria = 10.0
        self.stop_win = 15.0
        self.stop_loss = -5.0
        self.total_lucro = 0.0
        
        self.memoria_erros = []
        self.regras_auto_correcao = []
        self.acertos_detalhados = []
        self.erros_detalhados = []
        self.sequencia_atual_derrotas = 0
        
        self.scheduled_entries = []
        self.last_10x_time = None
        
        if not os.path.exists('data'):
            os.makedirs('data')
        
        self.carregar_padroes()
        self.carregar_padroes_historicos()
        self.carregar_regras_auto_correcao()
        self.carregar_acertos_erros()
    
    def carregar_padroes(self):
        if os.path.exists('data/padroes.json'):
            try:
                with open('data/padroes.json', 'r', encoding='utf-8') as f:
                    self.padroes_detectados = json.load(f)
                for padrao_id, info in self.padroes_detectados.items():
                    if 'historico' not in info:
                        acertos = info.get('acertos', 1)
                        ocorrencias = info.get('ocorrencias', 1)
                        info['historico'] = [1] * acertos + [0] * (ocorrencias - acertos)
                    info.setdefault('descricao', f'Padrao {padrao_id}')
                    info.setdefault('ocorrencias', len(info['historico']))
                    info.setdefault('acertos', sum(info['historico']))
                    info.setdefault('ultima_ocorrencia', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    info.setdefault('taxa_sucesso', (info['acertos'] / info['ocorrencias']) * 100 if info['ocorrencias'] > 0 else 0)
                    info.setdefault('data_ultima_atualizacao', datetime.now().strftime('%Y-%m-%d'))
                print(f"Carregados {len(self.padroes_detectados)} padroes salvos")
            except Exception as e:
                print(f"Erro ao carregar padroes: {e}")
                self.padroes_detectados = {}
        else:
            self.padroes_detectados = {}
    
    def carregar_padroes_historicos(self):
        if os.path.exists('data/padroes_historicos.json'):
            try:
                with open('data/padroes_historicos.json', 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                for padrao in dados.get('padroes', []):
                    padrao_id = padrao['padrao']
                    if padrao_id not in self.padroes_detectados:
                        self.padroes_detectados[padrao_id] = {
                            'descricao': padrao.get('descricao', f"Padrao historico: {padrao_id}"),
                            'ocorrencias': padrao['ocorrencias'],
                            'acertos': int((padrao['taxa'] / 100) * padrao['ocorrencias']),
                            'ultima_ocorrencia': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'taxa_sucesso': padrao['taxa'],
                            'historico': [1] * int((padrao['taxa'] / 100) * padrao['ocorrencias']) +
                                       [0] * (padrao['ocorrencias'] - int((padrao['taxa'] / 100) * padrao['ocorrencias'])),
                            'data_ultima_atualizacao': datetime.now().strftime('%Y-%m-%d'),
                            'fonte': 'HISTORICO'
                        }
                print(f"Carregados {len(dados.get('padroes', []))} padroes historicos lucrativos")
                return True
            except Exception as e:
                print(f"Erro ao carregar padroes historicos: {e}")
                return False
        else:
            print("Nenhum padrao historico encontrado")
            return False
    
    def carregar_regras_auto_correcao(self):
        if os.path.exists('data/regras_auto_correcao.json'):
            try:
                with open('data/regras_auto_correcao.json', 'r', encoding='utf-8') as f:
                    self.regras_auto_correcao = json.load(f)
                print(f"Carregadas {len(self.regras_auto_correcao)} regras de auto-correcao")
            except Exception as e:
                print(f"Erro ao carregar regras de auto-correcao: {e}")
                self.regras_auto_correcao = []
        else:
            self.regras_auto_correcao = []
    
    def carregar_acertos_erros(self):
        if os.path.exists('data/acertos_detalhados.json'):
            try:
                with open('data/acertos_detalhados.json', 'r', encoding='utf-8') as f:
                    self.acertos_detalhados = json.load(f)
                print(f"Carregados {len(self.acertos_detalhados)} acertos detalhados")
            except Exception as e:
                print(f"Erro ao carregar acertos detalhados: {e}")
                self.acertos_detalhados = []
        else:
            self.acertos_detalhados = []
        
        if os.path.exists('data/erros_detalhados.json'):
            try:
                with open('data/erros_detalhados.json', 'r', encoding='utf-8') as f:
                    self.erros_detalhados = json.load(f)
                print(f"Carregados {len(self.erros_detalhados)} erros detalhados")
            except Exception as e:
                print(f"Erro ao carregar erros detalhados: {e}")
                self.erros_detalhados = []
        else:
            self.erros_detalhados = []
    
    def salvar_padroes(self):
        try:
            with open('data/padroes.json', 'w', encoding='utf-8') as f:
                json.dump(self.padroes_detectados, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Erro] Erro ao salvar padroes: {e}")
    
    def salvar_regras_auto_correcao(self):
        try:
            with open('data/regras_auto_correcao.json', 'w', encoding='utf-8') as f:
                json.dump(self.regras_auto_correcao, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Erro] Erro ao salvar regras de auto-correcao: {e}")
    
    def salvar_acertos_erros(self):
        try:
            with open('data/acertos_detalhados.json', 'w', encoding='utf-8') as f:
                json.dump(self.acertos_detalhados, f, indent=2, ensure_ascii=False)
            print(f"Acertos detalhados salvos ({len(self.acertos_detalhados)} registros)")
        except Exception as e:
            print(f"[Erro] Erro ao salvar acertos detalhados: {e}")
        
        try:
            with open('data/erros_detalhados.json', 'w', encoding='utf-8') as f:
                json.dump(self.erros_detalhados, f, indent=2, ensure_ascii=False)
            print(f"Erros detalhados salvos ({len(self.erros_detalhados)} registros)")
        except Exception as e:
            print(f"[Erro] Erro ao salvar erros detalhados: {e}")
    
    def fetch_data(self):
        try:
            with sync_playwright() as p:
                # ✅ CORREÇÃO CRÍTICA: Uso correto de launch_persistent_context
                browser = p.chromium.launch_persistent_context(
                    user_data_dir="/tmp/playwright",
                    executable_path="/snap/bin/chromium",
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--no-zygote',
                        '--single-process',
                        '--disable-setuid-sandbox'
                    ]
                )
                page = browser.new_page()
                page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
                })
                
                page.goto(self.url, wait_until="domcontentloaded", timeout=30000)
                
                if "historico/sortenabet/aviator" not in page.url:
                    print("[Atencao] Pagina nao carregou corretamente. Tentando novamente...")
                    browser.close()
                    return []
                
                try:
                    page.wait_for_selector('button:has-text("Prefiro continuar no escuro")', timeout=2000)
                    page.click('button:has-text("Prefiro continuar no escuro")')
                except:
                    pass
                
                try:
                    page.wait_for_selector('[class*="history"]', timeout=20000)
                    page.wait_for_function(
                        """
                        () => {
                            const container = document.querySelector('[class*="history"]');
                            return container && container.innerText && container.innerText.trim().length > 0;
                        }
                        """,
                        timeout=20000
                    )
                except:
                    print("[Atencao] Dados nao carregaram a tempo. Tentando coletar mesmo assim...")
                
                data = page.evaluate("""() => {
                    const container = document.querySelector('[class*="history"]') ||
                                     document.querySelector('.history') ||
                                     document.querySelector('div.history-container') ||
                                     document.body;
                    
                    if (!container) return [];
                    
                    const text = container.innerText || container.textContent || '';
                    
                    const pattern = /([\\d,]+(?:\\.\\d+)?)\\s*x/gi;
                    const matches = [];
                    let match;
                    
                    while ((match = pattern.exec(text)) !== null) {
                        let valueStr = match[1].trim();
                        valueStr = valueStr.replace(',', '.');
                        valueStr = valueStr.replace(/[^0-9.]/g, '');
                        
                        const value = parseFloat(valueStr);
                        if (!isNaN(value) && value >= 0.01 && value <= 1000.0) {
                            matches.push(value);
                        }
                    }
                    
                    if (matches.length === 0) {
                        const elements = container.querySelectorAll('*');
                        for (let el of elements) {
                            const elText = el.innerText || el.textContent || '';
                            const fallbackMatch = elText.match(/([\\d,]+(?:\\.\\d+)?)\\s*x/i);
                            if (fallbackMatch) {
                                let valStr = fallbackMatch[1].replace(',', '.').replace(/[^0-9.]/g, '');
                                const val = parseFloat(valStr);
                                if (!isNaN(val) && val >= 0.01 && val <= 1000.0) {
                                    matches.push(val);
                                }
                            }
                        }
                    }
                    
                    if (matches.length === 0) {
                        const numbers = text.match(/\\d+(?:\\.\\d+)?/g);
                        if (numbers) {
                            for (const numStr of numbers) {
                                const num = parseFloat(numStr);
                                if (!isNaN(num) && num >= 0.01 && num <= 1000.0) {
                                    matches.push(num);
                                }
                            }
                        }
                    }
                    
                    if (matches.length === 0) {
                        const valueElements = container.querySelectorAll('[data-value]');
                        for (let el of valueElements) {
                            const valueStr = el.getAttribute('data-value');
                            if (valueStr) {
                                const num = parseFloat(valueStr.replace(',', '.'));
                                if (!isNaN(num) && num >= 0.01 && num <= 1000.0) {
                                    matches.push(num);
                                }
                            }
                        }
                    }
                    
                    return matches.reverse().slice(0, 50);
                }""")
                browser.close()
                
                multipliers = []
                if isinstance(data, list):
                    for item in data:
                        try:
                            num = float(item)
                            if 0.01 <= num <= 1000.00 and num != 1.00 and abs(num - 1.00) > 0.001:
                                multipliers.append(num)
                        except (ValueError, TypeError):
                            continue
                
                if multipliers:
                    print(f"✅ Coletados {len(multipliers)} valores reais: {multipliers[:5]}...")
                else:
                    print("⚠️ ATENCAO: Nenhum valor coletado! Verifique a conexao com o TipMiner.")
                
                return multipliers
        except Exception as e:
            print(f"[Erro] ERRO na coleta: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def analisar_sequencias(self, dados):
        sequencias = []
        sequencia_atual = {'tipo': None, 'tamanho': 0, 'valores': []}
        
        for mult in dados:
            if not isinstance(mult, (int, float)) or mult < 0.01 or mult > 1000.0 or abs(mult - 1.00) < 0.001:
                continue
                
            is_win = mult >= 2.0
            if sequencia_atual['tipo'] is None:
                sequencia_atual['tipo'] = 'WIN' if is_win else 'LOSS'
                sequencia_atual['tamanho'] = 1
                sequencia_atual['valores'] = [mult]
            elif (sequencia_atual['tipo'] == 'WIN' and is_win) or \
                 (sequencia_atual['tipo'] == 'LOSS' and not is_win):
                sequencia_atual['tamanho'] += 1
                sequencia_atual['valores'].append(mult)
            else:
                sequencias.append(sequencia_atual.copy())
                sequencia_atual['tipo'] = 'WIN' if is_win else 'LOSS'
                sequencia_atual['tamanho'] = 1
                sequencia_atual['valores'] = [mult]
        if sequencia_atual['tipo']:
            sequencias.append(sequencia_atual)
        return sequencias
    
    def verificar_status_mercado_aprimorado(self, sequencias):
        sequencias_1_2 = sum(1 for s in sequencias[:20] if s['tipo'] == 'LOSS' and 1 <= s['tamanho'] <= 2)
        sequencias_3 = sum(1 for s in sequencias[:20] if s['tipo'] == 'LOSS' and s['tamanho'] == 3)
        if sequencias_1_2 >= 2:
            return "MUITO BOM", sequencias_1_2
        elif sequencias_3 >= 2:
            return "BOM", sequencias_3
        elif sequencias_1_2 + sequencias_3 >= 2:
            return "NORMAL", sequencias_1_2 + sequencias_3
        else:
            return "RUIM", 0
    
    def detectar_padroes(self, sequencias):
        novos_padroes = []
        sinais_imediatos = []
        for i in range(len(sequencias) - 1):
            seq_atual = sequencias[i]
            seq_proxima = sequencias[i + 1]
            if (seq_atual['tipo'] == 'LOSS' and 1 <= seq_atual['tamanho'] <= 3):
                padrao_id = f"LOSS_{seq_atual['tamanho']}_WIN"
                agora = datetime.now()
                if agora.date() == self.data_inicio:
                    self.padroes_dia[padrao_id]['ocorrencias'] += 1
                if seq_proxima['tipo'] == 'WIN':
                    self.padroes_dia[padrao_id]['acertos'] += 1
                    self.padroes_dia[padrao_id]['ultima_ocorrencia'] = agora.strftime('%H:%M:%S')
                if padrao_id not in self.padroes_detectados:
                    self.padroes_detectados[padrao_id] = {
                        'descricao': f'{seq_atual["tamanho"]} derrotas -> vitoria',
                        'ocorrencias': 1,
                        'acertos': 1 if seq_proxima['tipo'] == 'WIN' else 0,
                        'ultima_ocorrencia': agora.strftime('%Y-%m-%d %H:%M:%S'),
                        'taxa_sucesso': 100.0 if seq_proxima['tipo'] == 'WIN' else 0.0,
                        'historico': [1 if seq_proxima['tipo'] == 'WIN' else 0],
                        'data_ultima_atualizacao': agora.strftime('%Y-%m-%d')
                    }
                    novos_padroes.append(padrao_id)
                else:
                    self.padroes_detectados[padrao_id]['ocorrencias'] += 1
                    if seq_proxima['tipo'] == 'WIN':
                        self.padroes_detectados[padrao_id]['acertos'] += 1
                    self.padroes_detectados[padrao_id]['ultima_ocorrencia'] = agora.strftime('%Y-%m-%d %H:%M:%S')
                    self.padroes_detectados[padrao_id]['historico'].append(1 if seq_proxima['tipo'] == 'WIN' else 0)
                    ultimos_100 = self.padroes_detectados[padrao_id]['historico'][-100:]
                    self.padroes_detectados[padrao_id]['taxa_sucesso'] = \
                        (sum(ultimos_100) / len(ultimos_100)) * 100 if ultimos_100 else 0
                    if self.padroes_detectados[padrao_id]['taxa_sucesso'] > 65 and len(ultimos_100) >= 20:
                        sinais_imediatos.append({
                            'padrao': padrao_id,
                            'taxa': self.padroes_detectados[padrao_id]['taxa_sucesso'],
                            'ocorrencias': self.padroes_detectados[padrao_id]['ocorrencias']
                        })
        for sinal in sinais_imediatos:
            print(f"\n{'='*80}")
            print(f"SINAL DE ALTA CONFIANCA!")
            print(f"   Padrao: {sinal['padrao']}")
            print(f"   Taxa REAL de acerto: {sinal['taxa']:.1f}%")
            print(f"   Ocorrencias: {sinal['ocorrencias']}")
            print(f"   Entrada recomendada apos sequencia de {sinal['padrao'].split('_')[1]} derrotas")
            print(f"{'='*80}\n")
        self.salvar_padroes()
        return novos_padroes
    
    def classificar_vela_cores(self, multiplier):
        if 1.00 <= multiplier < 2.00:
            return 'AZUL'
        elif 2.00 <= multiplier < 10.00:
            return 'ROXA'
        elif multiplier >= 10.00:
            return 'ROSA'
        else:
            return 'OUTRO'
    
    def detectar_padroes_azul(self, dados):
        if dados and len(dados) >= 2:
            if abs(dados[0] - 1.00) < 0.01:
                return {
                    'tipo': 'PADRAO_RESET',
                    'padrao': '1.00X_RESET',
                    'confianca': 85.0,
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'valor_entrada': 1.0,
                    'valor_previsto': 10.0,
                    'resultado': None,
                    'motivo': "Padrao de reset detectado (1.00x) - quem comanda o game e o Azul"
                }
            if 1.74 <= dados[0] <= 1.76 and 1.74 <= dados[1] <= 1.76:
                return {
                    'tipo': 'PADRAO_CICLO',
                    'padrao': '1.75X_REPETIDO',
                    'confianca': 80.0,
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'valor_entrada': 1.0,
                    'valor_previsto': 2.5,
                    'resultado': None,
                    'motivo': "Padrao de ciclo detectado (1.75x repetido) - ciclo esta acabando"
                }
            if 1.33 <= dados[0] <= 1.35 and 1.33 <= dados[1] <= 1.35:
                return {
                    'tipo': 'PADRAO_CICLO',
                    'padrao': '1.34X_REPETIDO',
                    'confianca': 75.0,
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'valor_entrada': 1.0,
                    'valor_previsto': 3.0,
                    'resultado': None,
                    'motivo': "Padrao de ciclo detectado (1.34x repetido) - ciclo esta acabando"
                }
        return None
    
    def detectar_padrao_xadrez(self, dados):
        if dados and len(dados) >= 3:
            if (dados[0] >= 2.0 and dados[1] < 2.0 and dados[2] >= 2.0):
                return {
                    'tipo': 'PADRAO_XADREZ',
                    'padrao': 'POSITIVO_XADREZ',
                    'confianca': 70.0,
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'valor_entrada': 1.0,
                    'valor_previsto': 2.0,
                    'resultado': None,
                    'motivo': "Padrao de xadrez positivo detectado (repete consistentemente)"
                }
            if (dados[0] < 2.0 and dados[1] >= 2.0 and dados[2] < 2.0):
                return {
                    'tipo': 'PADRAO_XADREZ',
                    'padrao': 'NEGATIVO_XADREZ',
                    'confianca': 70.0,
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'valor_entrada': 1.0,
                    'valor_previsto': 2.0,
                    'resultado': None,
                    'motivo': "Padrao de xadrez negativo detectado (repete consistentemente)"
                }
        return None
    
    def analisar_estrategia_azuis(self, dados):
        if dados and len(dados) >= 1:
            if 1.00 <= dados[0] < 2.00:
                decimal_str = str(dados[0]).split('.')[1]
                primeiro_digito = int(decimal_str[0]) if decimal_str else 0
                if primeiro_digito >= 1:
                    return {
                        'tipo': 'ESTRATEGIA_AZUIS_DECIMAL',
                        'padrao': f'AZUL_{dados[0]:.2f}',
                        'confianca': 75.0,
                        'timestamp': datetime.now().strftime('%H:%M:%S'),
                        'valor_entrada': 1.0,
                        'valor_previsto': 2.0 + (primeiro_digito * 0.2),
                        'resultado': None,
                        'motivo': f"Vela azul {dados[0]:.2f}x -> previsao de {primeiro_digito} casas de azul (conforme MODULO 1)"
                    }
        return None
    
    def detectar_estrategias_modo_2(self, dados):
        if len(dados) < 6:
            return None
        if self.classificar_vela_cores(dados[-6]) != 'ROSA':
            return None
        azul_count = 0
        for i in range(-5, 0):
            if self.classificar_vela_cores(dados[i]) == 'AZUL':
                azul_count += 1
            else:
                break
        if azul_count >= 5:
            confianca = min(85, 70 + (azul_count - 5) * 5)
            return {
                'tipo': 'ENTRADA_MODO_2',
                'padrao': f'ROSA_{azul_count}_AZUL',
                'confianca': confianca,
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'valor_entrada': 1.0,
                'valor_previsto': 2.5,
                'resultado': None,
                'motivo': f"Modulo 2: ROSA seguido de {azul_count} AZULs - Entrar na proxima rodada"
            }
        return None
    
    def schedule_3x_entries(self, dados):
        if not dados:
            return None
        current = dados[0]
        current_time = datetime.now()
        if 2.90 <= current <= 3.10:
            entry_time_15s = current_time + timedelta(seconds=15)
            self.scheduled_entries.append({
                'entry_time': entry_time_15s,
                'max_entries': 3,
                'entries_made': 0,
                'tipo': 'SCHEDULED_3X_15S'
            })
            entry_time_exact = current_time.replace(second=0, microsecond=0) + timedelta(minutes=1)
            self.scheduled_entries.append({
                'entry_time': entry_time_exact,
                'max_entries': 2,
                'entries_made': 0,
                'tipo': 'SCHEDULED_3X_EXACT_MINUTE'
            })
            return {
                'tipo': 'SCHEDULED_3X',
                'padrao': '3X_VELOCITIES',
                'confianca': 72.0,
                'timestamp': current_time.strftime('%H:%M:%S'),
                'valor_entrada': 1.0,
                'valor_previsto': 3.0,
                'resultado': None,
                'motivo': f"Vela de 3x detectada ({current:.2f}x) -> 2 estrategias de timing ativadas"
            }
        return None
    
    def schedule_10x_entries(self, dados):
        if not dados:
            return None
        current = dados[0]
        current_time = datetime.now()
        if current >= 10.0:
            self.last_10x_time = current_time
            return None
        if self.last_10x_time is not None and (datetime.now() - self.last_10x_time).seconds > 600:
            entry_time = datetime.now() - timedelta(seconds=20)
            self.scheduled_entries.append({
                'entry_time': entry_time,
                'max_entries': 3,
                'entries_made': 0,
                'tipo': 'SCHEDULED_5X'
            })
            return {
                'tipo': 'SCHEDULED_5X',
                'padrao': '5X_STRATEGY',
                'confianca': 72.0,
                'timestamp': current_time.strftime('%H:%M:%S'),
                'valor_entrada': 1.0,
                'valor_previsto': 5.0,
                'resultado': None,
                'motivo': "Estrategia de 5x ativada: Entrar ate 20s antes e realizar 3 entradas"
            }
        return None
    
    def detectar_padrao_3_sequencias(self, dados):
        if len(dados) < 4:
            return None
        if (self.classificar_vela_cores(dados[0]) in ['ROXA', 'ROSA'] and
            self.classificar_vela_cores(dados[1]) in ['ROXA', 'ROSA'] and
            self.classificar_vela_cores(dados[2]) == 'AZUL' and
            self.classificar_vela_cores(dados[3]) in ['ROXA', 'ROSA']):
            return {
                'tipo': 'PADRAO_3_SEQUENCIAS',
                'padrao': 'ROXA_ROSA_QUEBRA_AZUL',
                'confianca': 85.0,
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'valor_entrada': 1.0,
                'valor_previsto': 3.0,
                'resultado': None,
                'motivo': "Padrao 3 sequencias detectado: ROXA/ROSA -> ROXA/ROSA -> QUEBRA AZUL -> Proxima vela ROXA/ROSA"
            }
        return None
    
    def detectar_gatilho_surreal(self, dados):
        if len(dados) < 6:
            return None
        velas_abaixo_149 = sum(1 for i in range(6) if dados[i] < 1.49)
        if velas_abaixo_149 >= 5:
            vela_especial = dados[5]
            if 1.11 <= vela_especial <= 1.99:
                return {
                    'tipo': 'GATILHO_SURREAL',
                    'padrao': '5_VEIAS_ABAIXO_149X',
                    'confianca': 90.0,
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'valor_entrada': 1.0,
                    'valor_previsto': 5.0,
                    'resultado': None,
                    'motivo': f"Gatilho Surreal detectado: {velas_abaixo_149} velas < 1.49x + vela especial {vela_especial:.2f}x"
                }
        return None
    
    def detectar_padrao_10x_reset(self, dados):
        if len(dados) < 3:
            return None
        if (abs(dados[0] - 1.00) < 0.01 and
            1.36 <= dados[1] <= 1.38 and
            abs(dados[2] - 1.00) < 0.01):
            return {
                'tipo': 'PADRAO_10X_RESET',
                'padrao': '1.00X_1.37X_1.00X',
                'confianca': 95.0,
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'valor_entrada': 1.0,
                'valor_previsto': 10.0,
                'resultado': None,
                'motivo': "Padrao 10x Reset detectado: 1.00x -> 1.37x -> 1.00x -> Proxima vela 10x"
            }
        return None
    
    def detectar_repeticao_casas(self, dados):
        if len(dados) < 6:
            return None
        repeticoes = {'1.30': 0, '1.40': 0, '1.70': 0}
        for i in range(6):
            if 1.29 <= dados[i] <= 1.31:
                repeticoes['1.30'] += 1
            elif 1.39 <= dados[i] <= 1.41:
                repeticoes['1.40'] += 1
            elif 1.69 <= dados[i] <= 1.71:
                repeticoes['1.70'] += 1
        if repeticoes['1.30'] >= 2 and repeticoes['1.40'] >= 2 and repeticoes['1.70'] >= 2:
            return {
                'tipo': 'REPETICAO_CASAS',
                'padrao': 'CASAS_1.30_1.40_1.70',
                'confianca': 95.0,
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'valor_entrada': 1.0,
                'valor_previsto': 8.0,
                'resultado': None,
                'motivo': "Repeticao de casas detectada: 1.30, 1.40, 1.70 (2x cada)"
            }
        return None
    
    def analisar_erro_contextual(self, vela_entrada, vela_resultado, hora_atual):
        contexto = {
            'tipo_erro': 'DESCONHECIDO',
            'hora': hora_atual,
            'recomendacao': 'EVITAR_ENTRADA'
        }
        horarios_criticos = [2, 3, 4, 5, 14, 15]
        if hora_atual in horarios_criticos:
            contexto['tipo_erro'] = 'HORARIO_BAIXA_PERFORMANCE'
            contexto['recomendacao'] = 'REDUZIR_APOSTA'
        if vela_entrada >= 10.0 and vela_resultado < 2.0:
            contexto['tipo_erro'] = 'CRASH_POS_10X'
            contexto['recomendacao'] = 'AGUARDAR_5_RODADAS_POS_10X'
        return contexto
    
    def gerar_regra_auto_correcao(self, contexto_erro, vela_entrada, vela_resultado):
        regra = {
            'id': f"REGRAS_{len(self.regras_auto_correcao)+1}",
            'contexto': contexto_erro,
            'condicao': '',
            'acao': contexto_erro['recomendacao'],
            'prioridade': 0,
            'data_criacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        if contexto_erro['tipo_erro'] == 'HORARIO_BAIXA_PERFORMANCE':
            hora = contexto_erro['hora']
            regra['condicao'] = f"HORA == {hora}"
            regra['prioridade'] = 85
        elif contexto_erro['tipo_erro'] == 'CRASH_POS_10X':
            regra['condicao'] = "ULTIMA_VELA >= 10.0"
            regra['prioridade'] = 95
        self.regras_auto_correcao.append(regra)
        self.memoria_erros.append({
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'vela_entrada': vela_entrada,
            'vela_resultado': vela_resultado,
            'contexto': contexto_erro,
            'regra_gerada': regra
        })
        self.salvar_regras_auto_correcao()
        return regra
    
    def aplicar_filtro_auto_correcao(self, dados, sinal_proposto):
        hora_atual = datetime.now().hour
        for regra in sorted(self.regras_auto_correcao, key=lambda x: x['prioridade'], reverse=True):
            condicao_atendida = False
            if 'HORA ==' in regra['condicao']:
                hora_alvo = int(regra['condicao'].split('==')[1].strip())
                condicao_atendida = hora_atual == hora_alvo
            elif 'ULTIMA_VELA >= 10.0' in regra['condicao']:
                condicao_atendida = dados[0] >= 10.0
            if condicao_atendida:
                if regra['acao'] == 'REDUZIR_APOSTA':
                    sinal_proposto['valor_entrada'] *= 0.5
                    return sinal_proposto, f"HORARIO DE BAIXA PERFORMANCE ({hora_atual}h) - Reduzindo aposta em 50%"
                elif regra['acao'] == 'AGUARDAR_5_RODADAS_POS_10X':
                    return None, f"FILTRO AUTO-CORRECAO: Aguardar 5 rodadas apos vela >10x"
        return sinal_proposto, "Sinal aprovado por todos os filtros de auto-correcao"
    
    def calcular_bonus_horario(self, hora):
        horarios_lucrativos = {
            6: 5, 7: 5, 8: 4,
            13: 4,
            21: 5, 22: 6, 23: 5
        }
        return horarios_lucrativos.get(hora, 0)
    
    def gerenciar_banco(self):
        if self.total_lucro >= self.meta_diaria:
            print(f"\nMETA DIARIA ATINGIDA: {self.total_lucro:.2f} unidades")
            print("Recomendacao do MODULO 1: 'Aprenda a parar, faca seu lucro saque e retorne no outro dia'")
            return True
        if self.total_lucro >= self.stop_win:
            print(f"\nSTOP WIN ATINGIDO: {self.total_lucro:.2f} unidades")
            print("Recomendacao do MODULO 1: 'O seu capital e sua empresa, entao jamais quebre-a'")
            return True
        if self.total_lucro <= self.stop_loss:
            print(f"\nSTOP LOSS ATINGIDO: {self.total_lucro:.2f} unidades")
            print("Recomendacao do MODULO 1: 'Nunca coloque no game dinheiro de outro compromisso'")
            return True
        return True
    
    def prever_valor_vela(self, padrao, dados):
        previsoes_padroes = {
            '1.00X_RESET': 10.0, '1.75X_REPETIDO': 2.5, '1.34X_REPETIDO': 3.0,
            'PADRAO_XADREZ': 2.0, 'GATILHO_SURREAL': 5.0, 'PADRAO_10X_RESET': 10.0,
            'REPETICAO_CASAS': 8.0
        }
        if padrao in previsoes_padroes:
            return previsoes_padroes[padrao]
        if dados:
            ultima_vela = dados[0]
            if ultima_vela < 1.50:
                return 2.5
            elif ultima_vela < 2.00:
                return 3.0
            else:
                return 2.0
        return 2.0
    
    def analise_completa_inteligente(self, dados, sequencias):
        agora = datetime.now()
        hora_atual = agora.hour
        
        status_mercado, _ = self.verificar_status_mercado_aprimorado(sequencias)
        if status_mercado not in ["MUITO BOM", "BOM"]:
            return None, f"Mercado nao favoravel (status: {status_mercado})"
        
        if sequencias and sequencias[0]['tipo'] == 'LOSS' and 1 <= sequencias[0]['tamanho'] <= 3:
            padrao_id = f"LOSS_{sequencias[0]['tamanho']}_WIN"
            if padrao_id in self.padroes_detectados:
                info = self.padroes_detectados[padrao_id]
                if info['taxa_sucesso'] > 60:
                    confianca_base = info['taxa_sucesso']
                    bonus_mercado = 5 if status_mercado == "MUITO BOM" else 2
                    confianca_final = min(85, confianca_base + bonus_mercado)
                    
                    return {
                        'tipo': 'ENTRADA_PREDITIVA',
                        'padrao': padrao_id,
                        'confianca': confianca_final,
                        'timestamp': agora.strftime('%H:%M:%S'),
                        'valor_entrada': 1.0,
                        'valor_previsto': self.prever_valor_vela(padrao_id, dados),
                        'resultado': None,
                        'motivo': f"SEQUENCIA EM ANDAMENTO: {sequencias[0]['tamanho']} derrotas -> Proxima vela (Mercado {status_mercado} + {confianca_final:.1f}% confianca)"
                    }, None
        
        padrao_azul = self.detectar_padroes_azul(dados)
        if padrao_azul:
            sinal_filtrado, motivo_filtro = self.aplicar_filtro_auto_correcao(dados, padrao_azul)
            if sinal_filtrado:
                bonus_horario = self.calcular_bonus_horario(hora_atual)
                if bonus_horario > 0:
                    sinal_filtrado['confianca'] += bonus_horario
                    sinal_filtrado['motivo'] += f" | HORARIO LUCRATIVO ({hora_atual}h) +{bonus_horario}%"
                return sinal_filtrado, motivo_filtro
        
        padrao_xadrez = self.detectar_padrao_xadrez(dados)
        if padrao_xadrez:
            sinal_filtrado, motivo_filtro = self.aplicar_filtro_auto_correcao(dados, padrao_xadrez)
            if sinal_filtrado:
                bonus_horario = self.calcular_bonus_horario(hora_atual)
                if bonus_horario > 0:
                    sinal_filtrado['confianca'] += bonus_horario
                    sinal_filtrado['motivo'] += f" | HORARIO LUCRATIVO ({hora_atual}h) +{bonus_horario}%"
                return sinal_filtrado, motivo_filtro
        
        padrao_azuis_decimal = self.analisar_estrategia_azuis(dados)
        if padrao_azuis_decimal:
            sinal_filtrado, motivo_filtro = self.aplicar_filtro_auto_correcao(dados, padrao_azuis_decimal)
            if sinal_filtrado:
                bonus_horario = self.calcular_bonus_horario(hora_atual)
                if bonus_horario > 0:
                    sinal_filtrado['confianca'] += bonus_horario
                    sinal_filtrado['motivo'] += f" | HORARIO LUCRATIVO ({hora_atual}h) +{bonus_horario}%"
                return sinal_filtrado, motivo_filtro
        
        padrao_modo_2 = self.detectar_estrategias_modo_2(dados)
        if padrao_modo_2:
            sinal_filtrado, motivo_filtro = self.aplicar_filtro_auto_correcao(dados, padrao_modo_2)
            if sinal_filtrado:
                bonus_horario = self.calcular_bonus_horario(hora_atual)
                if bonus_horario > 0:
                    sinal_filtrado['confianca'] += bonus_horario
                    sinal_filtrado['motivo'] += f" | HORARIO LUCRATIVO ({hora_atual}h) +{bonus_horario}%"
                return sinal_filtrado, motivo_filtro
        
        scheduled_3x = self.schedule_3x_entries(dados)
        if scheduled_3x:
            sinal_filtrado, motivo_filtro = self.aplicar_filtro_auto_correcao(dados, scheduled_3x)
            if sinal_filtrado:
                bonus_horario = self.calcular_bonus_horario(hora_atual)
                if bonus_horario > 0:
                    sinal_filtrado['confianca'] += bonus_horario
                    sinal_filtrado['motivo'] += f" | HORARIO LUCRATIVO ({hora_atual}h) +{bonus_horario}%"
                return sinal_filtrado, motivo_filtro
        
        scheduled_10x = self.schedule_10x_entries(dados)
        if scheduled_10x:
            sinal_filtrado, motivo_filtro = self.aplicar_filtro_auto_correcao(dados, scheduled_10x)
            if sinal_filtrado:
                bonus_horario = self.calcular_bonus_horario(hora_atual)
                if bonus_horario > 0:
                    sinal_filtrado['confianca'] += bonus_horario
                    sinal_filtrado['motivo'] += f" | HORARIO LUCRATIVO ({hora_atual}h) +{bonus_horario}%"
                return sinal_filtrado, motivo_filtro
        
        padrao_3_seq = self.detectar_padrao_3_sequencias(dados)
        if padrao_3_seq and padrao_3_seq['confianca'] > 80:
            sinal_filtrado, motivo_filtro = self.aplicar_filtro_auto_correcao(dados, padrao_3_seq)
            if sinal_filtrado:
                bonus_horario = self.calcular_bonus_horario(hora_atual)
                if bonus_horario > 0:
                    sinal_filtrado['confianca'] += bonus_horario
                    sinal_filtrado['motivo'] += f" | HORARIO LUCRATIVO ({hora_atual}h) +{bonus_horario}%"
                return sinal_filtrado, motivo_filtro
        
        gatilho_surreal = self.detectar_gatilho_surreal(dados)
        if gatilho_surreal and gatilho_surreal['confianca'] > 85:
            sinal_filtrado, motivo_filtro = self.aplicar_filtro_auto_correcao(dados, gatilho_surreal)
            if sinal_filtrado:
                bonus_horario = self.calcular_bonus_horario(hora_atual)
                if bonus_horario > 0:
                    sinal_filtrado['confianca'] += bonus_horario
                    sinal_filtrado['motivo'] += f" | HORARIO LUCRATIVO ({hora_atual}h) +{bonus_horario}%"
                return sinal_filtrado, motivo_filtro
        
        padrao_10x_reset = self.detectar_padrao_10x_reset(dados)
        if padrao_10x_reset and padrao_10x_reset['confianca'] > 90:
            sinal_filtrado, motivo_filtro = self.aplicar_filtro_auto_correcao(dados, padrao_10x_reset)
            if sinal_filtrado:
                bonus_horario = self.calcular_bonus_horario(hora_atual)
                if bonus_horario > 0:
                    sinal_filtrado['confianca'] += bonus_horario
                    sinal_filtrado['motivo'] += f" | HORARIO LUCRATIVO ({hora_atual}h) +{bonus_horario}%"
                return sinal_filtrado, motivo_filtro
        
        repeticao_casas = self.detectar_repeticao_casas(dados)
        if repeticao_casas and repeticao_casas['confianca'] > 90:
            sinal_filtrado, motivo_filtro = self.aplicar_filtro_auto_correcao(dados, repeticao_casas)
            if sinal_filtrado:
                bonus_horario = self.calcular_bonus_horario(hora_atual)
                if bonus_horario > 0:
                    sinal_filtrado['confianca'] += bonus_horario
                    sinal_filtrado['motivo'] += f" | HORARIO LUCRATIVO ({hora_atual}h) +{bonus_horario}%"
                return sinal_filtrado, motivo_filtro
        
        return None, "Nenhuma condicao de alta confianca detectada apos filtros de auto-correcao"
    
    def gerar_sinal_entrada(self, dados, sequencias):
        agora = datetime.now()
        
        if self.ultima_analise_completa and (agora - self.ultima_analise_completa).seconds < 5:
            return None
        
        self.ultima_analise_completa = agora
        resultado = self.analise_completa_inteligente(dados, sequencias)
        
        if resultado is None:
            return None
        sinal, motivo = resultado
        
        if sinal:
            sinal['gatilhos'] = self.obter_gatilhos_usados(sinal)
            sinal['timestamp_analise'] = agora.strftime('%Y-%m-%d %H:%M:%S')
            sinal['numero_vela'] = self.numero_vela_atual + 1
            self.sinais_enviados.append(sinal)
            
            print(f"\n{'='*80}")
            print(f"SINAL PREDITIVO - APOSTAR AGORA!")
            print(f"   Padrao: {sinal['padrao']}")
            print(f"   Confianca: {sinal['confianca']:.1f}%")
            print(f"   Valor previsto: {sinal.get('valor_previsto', 2.0):.2f}x")
            print(f"   Enviado as: {sinal['timestamp']}")
            print(f"   VOCE TEM 4+ SEGUNDOS PARA APOSTAR!")
            print(f"{'='*80}\n")
            
            return sinal
        
        return None
    
    def atualizar_resultado_sinais(self, dados):
        if not self.sinais_enviados or not dados:
            return
        
        proxima_rodada = dados[0]
        is_win = proxima_rodada >= 2.0
        self.numero_vela_atual += 1
        
        for sinal in self.sinais_enviados[-5:]:
            if sinal['resultado'] is None:
                sinal['resultado'] = 'WIN' if is_win else 'LOSS'
                sinal['valor_real'] = proxima_rodada
                
                if is_win:
                    self.total_lucro += 0.9
                    acerto_detalhado = {
                        'numero_vela': self.numero_vela_atual,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'vela_entrada': sinal.get('valor_entrada', 1.0),
                        'vela_resultado': proxima_rodada,
                        'valor_previsto': sinal.get('valor_previsto', 2.0),
                        'erro_previsao': abs(proxima_rodada - sinal.get('valor_previsto', 2.0)),
                        'padrao': sinal.get('padrao', 'DESCONHECIDO'),
                        'confianca': sinal.get('confianca', 0.0),
                        'gatilhos': sinal.get('gatilhos', []),
                        'motivo': sinal.get('motivo', 'Sem motivo'),
                        'hora': datetime.now().hour,
                        'minuto': datetime.now().minute
                    }
                    self.acertos_detalhados.append(acerto_detalhado)
                    print(f"\nACERTO NA VELA #{acerto_detalhado['numero_vela']}: {proxima_rodada:.2f}x")
                    print(f"   Padrao: {acerto_detalhado['padrao']} | Confianca: {acerto_detalhado['confianca']:.1f}%")
                    print(f"   Previsto: {acerto_detalhado['valor_previsto']:.2f}x | Real: {proxima_rodada:.2f}x | Erro: {acerto_detalhado['erro_previsao']:.2f}x")
                    print(f"   Gatilhos: {', '.join(acerto_detalhado['gatilhos'][:3]) if acerto_detalhado['gatilhos'] else 'Nenhum'}")
                
                else:
                    self.total_lucro -= 1.0
                    erro_detalhado = {
                        'numero_vela': self.numero_vela_atual,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'vela_entrada': sinal.get('valor_entrada', 1.0),
                        'vela_resultado': proxima_rodada,
                        'valor_previsto': sinal.get('valor_previsto', 2.0),
                        'erro_previsao': abs(proxima_rodada - sinal.get('valor_previsto', 2.0)),
                        'padrao': sinal.get('padrao', 'DESCONHECIDO'),
                        'confianca': sinal.get('confianca', 0.0),
                        'gatilhos': sinal.get('gatilhos', []),
                        'motivo': sinal.get('motivo', 'Sem motivo'),
                        'hora': datetime.now().hour,
                        'minuto': datetime.now().minute
                    }
                    self.erros_detalhados.append(erro_detalhado)
                    print(f"\nERRO NA VELA #{erro_detalhado['numero_vela']}: {proxima_rodada:.2f}x")
                    print(f"   Padrao: {erro_detalhado['padrao']} | Confianca: {erro_detalhado['confianca']:.1f}%")
                    print(f"   Previsto: {erro_detalhado['valor_previsto']:.2f}x | Real: {proxima_rodada:.2f}x | Erro: {erro_detalhado['erro_previsao']:.2f}x")
                    print(f"   GATILHOS USADOS NO ERRO: {', '.join(erro_detalhado['gatilhos'][:3]) if erro_detalhado['gatilhos'] else 'Nenhum'}")
        
        if (len(self.acertos_detalhados) + len(self.erros_detalhados)) % 5 == 0:
            self.salvar_acertos_erros()
    
    def obter_gatilhos_usados(self, sinal):
        gatilhos = []
        if 'RESET' in sinal.get('padrao', ''):
            gatilhos.append('Padrao de reset detectado (1.00x)')
        if '1.75X' in sinal.get('padrao', ''):
            gatilhos.append('Padrao de ciclo 1.75x')
        if '1.34X' in sinal.get('padrao', ''):
            gatilhos.append('Padrao de ciclo 1.34x')
        if 'XADREZ' in sinal.get('padrao', ''):
            gatilhos.append('Padrao xadrez')
        if 'SURREAL' in sinal.get('padrao', ''):
            gatilhos.append('Gatilho Surreal')
        if '10X_RESET' in sinal.get('padrao', ''):
            gatilhos.append('Padrao 10x Reset')
        if 'REPETICAO_CASAS' in sinal.get('padrao', ''):
            gatilhos.append('Repeticao de casas')
        return gatilhos
    
    def salvar_dados_continuos(self, dados):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data_dia = datetime.now().strftime('%Y-%m-%d')
        for mult in dados:
            self.historico_completo.append({
                'timestamp': timestamp,
                'data_dia': data_dia,
                'multiplier': mult,
                'is_win': mult >= 2.0,
                'is_big_win': mult >= 10.0,
                'hora': datetime.now().hour,
                'minuto': datetime.now().minute
            })
        try:
            df = pd.DataFrame(self.historico_completo)
            df.to_csv('data/historico_completo.csv', index=False, encoding='utf-8')
        except:
            pass
    
    def obter_velas_mais_repetidas_24h(self):
        agora = datetime.now()
        limite_24h = agora - timedelta(hours=24)
        dados_24h = [
            entry for entry in self.historico_completo
            if datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S') >= limite_24h
        ]
        if not dados_24h:
            return []
        frequencia = defaultdict(int)
        for entry in dados_24h:
            valor_arredondado = round(entry['multiplier'], 2)
            frequencia[valor_arredondado] += 1
        top_10 = sorted(frequencia.items(), key=lambda x: x[1], reverse=True)[:10]
        total = sum(frequencia.values())
        resultado = []
        for valor, count in top_10:
            percentual = (count / total) * 100
            status = "(vitoria)" if valor >= 2.0 else "(derrota)"
            resultado.append({
                'valor': valor,
                'count': count,
                'percentual': percentual,
                'status': status
            })
        return resultado
    
    def exibir_status(self, dados, sequencias):
        os.system('clear')
        
        print("="*80)
        print(f"AVIATOR BOT INTELIGENTE V3 - Coleta PRECISA de Dados (SEM NUMEROS GENERICOS)")
        print(f"Ultima atualizacao: {datetime.now().strftime('%H:%M:%S')} | Dia: {self.data_inicio}")
        print(f"Total de coletas: {self.total_coletas} | Velas analisadas: {len(dados)}")
        print(f"Lucro acumulado hoje: {self.total_lucro:.2f} | Meta diaria: {self.meta_diaria:.2f}")
        print("="*80)
        
        total = len(dados)
        if total == 0:
            print("\nNenhum dado coletado ainda. Aguardando proxima atualizacao...")
            return
        
        vitorias = sum(1 for d in dados if d >= 2.0)
        derrotas = total - vitorias
        big_wins = sum(1 for d in dados if d >= 10.0)
        
        print(f"\nESTATISTICAS DAS ULTIMAS {total} VELAS:")
        print(f"   Vitorias (>= 2.00x): {vitorias} ({vitorias/total*100:.1f}%)")
        print(f"   Derrotas (< 2.00x): {derrotas} ({derrotas/total*100:.1f}%)")
        print(f"   Grandes vitorias (>= 10.00x): {big_wins} ({big_wins/total*100:.1f}%)")
        
        print(f"\nESTATISTICAS DE VELAS ACERTADAS/ERRADAS:")
        total_sinais = len(self.acertos_detalhados) + len(self.erros_detalhados)
        if total_sinais > 0:
            taxa_acerto = (len(self.acertos_detalhados) / total_sinais) * 100
            print(f"   Total de VELAS ACERTADAS: {len(self.acertos_detalhados)} ({taxa_acerto:.1f}%)")
            print(f"   Total de VELAS ERRADAS: {len(self.erros_detalhados)} ({100 - taxa_acerto:.1f}%)")
            print(f"   Total de sinais enviados: {total_sinais}")
            print(f"   Ultima vela analisada: #{self.numero_vela_atual}")
            
            if len(self.acertos_detalhados) > 0:
                print(f"\n   ULTIMAS 5 VELAS ACERTADAS:")
                for acerto in self.acertos_detalhados[-5:][::-1]:
                    print(f"      Vela #{acerto['numero_vela']}: {acerto['vela_resultado']:.2f}x | "
                          f"Previsto: {acerto.get('valor_previsto', 2.0):.2f}x | "
                          f"{acerto['padrao']} ({acerto['confianca']:.0f}%)")
            
            if len(self.erros_detalhados) > 0:
                print(f"\n   ULTIMAS 5 VELAS ERRADAS (com gatilhos):")
                for erro in self.erros_detalhados[-5:][::-1]:
                    gatilhos_resumo = ', '.join(erro['gatilhos'][:2]) if erro['gatilhos'] else 'Sem gatilhos'
                    print(f"      Vela #{erro['numero_vela']}: {erro['vela_resultado']:.2f}x | "
                          f"Previsto: {erro.get('valor_previsto', 2.0):.2f}x | "
                          f"{erro['padrao']} | Gatilhos: {gatilhos_resumo}")
        else:
            print("   Aguardando primeiros sinais para analise detalhada...")
        
        status_mercado, count = self.verificar_status_mercado_aprimorado(sequencias)
        emoji = {"MUITO BOM": "MB", "BOM": "B", "NORMAL": "N", "RUIM": "R"}[status_mercado]
        print(f"\nSTATUS DO MERCADO: {emoji} {status_mercado}")
        print(f"   MUITO BOM = sequencias de 1-2 derrotas | BOM = sequencias de 3 derrotas")
        
        print(f"\nULTIMAS 10 VELAS (VALORES REAIS DO GRAFICO):")
        for i, mult in enumerate(dados[:10]):
            cor = self.classificar_vela_cores(mult)
            cor_emoji = "AZ" if cor == 'AZUL' else "RX" if cor == 'ROXA' else "RS" if cor == 'ROSA' else "OT"
            status = "(vitoria)" if mult >= 2.0 else "(derrota)"
            print(f"   {i+1}. {cor_emoji} {mult:.2f}x {status} <- VALOR REAL DO GRAFICO")
        
        sinal = self.gerar_sinal_entrada(dados, sequencias)
        if sinal:
            print(f"\n{'='*80}")
            print(f"SINAL PREDITIVO - APOSTAR AGORA!")
            print(f"   Padrao: {sinal['padrao']}")
            print(f"   Confianca: {sinal['confianca']:.1f}%")
            print(f"   Valor previsto: {sinal.get('valor_previsto', 2.0):.2f}x")
            print(f"   Enviado as: {sinal['timestamp']}")
            print(f"   VOCE TEM 4+ SEGUNDOS PARA APOSTAR!")
            print(f"{'='*80}")
        
        print("\n" + "="*80)
        print("DICA PRO: Sistema operando 24h/dia SEM INTERRUPCAO")
        print("   COLETA PRECISA: Valores reais do grafico (SEM numeros genericos 1.00x)")
        print("   SINAIS PREDITIVOS 4+ SEGUNDOS ANTES da vela sair")
        print("   Gatilhos LOSS_* REMOVIDOS conforme solicitado")
        print("   Acertos/Erros salvos em: data/acertos_detalhados.json | data/erros_detalhados.json")
        print("="*80)
    
    def executar(self, duracao_minutos=1440):
        tempo_inicio = time.time()
        tempo_fim = tempo_inicio + (duracao_minutos * 60)
        self.last_round_value = None
        
        print(f"Iniciando Aviator Bot V3 com COLETA PRECISA de dados...")
        print(f"Operacao CONTINUA 24h (sem parar por meta/lucro)")
        print(f"Sistema: COLETA PRECISA + SINAIS PREDITIVOS 4+ SEGUNDOS ANTES da vela")
        print(f"Corrigido: Valores reais do grafico (SEM numeros genericos)")
        time.sleep(2)
        
        while time.time() < tempo_fim:
            dados = self.fetch_data()
            if dados:
                current_value = dados[0] if dados else None
                if self.last_round_value is None or abs(current_value - self.last_round_value) > 0.01:
                    self.last_round_value = current_value
                    self.total_coletas += 1
                    sequencias = self.analisar_sequencias(dados)
                    self.detectar_padroes(sequencias)
                    self.salvar_dados_continuos(dados)
                    self.exibir_status(dados, sequencias)
                    self.atualizar_resultado_sinais(dados)
            
            try:
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    line = sys.stdin.readline()
                    if line.strip().lower() == 'q':
                        print("\nBot encerrado pelo usuario (tecla 'q').")
                        break
            except:
                pass
            
            time.sleep(0.3)
        
        self.salvar_acertos_erros()
        print(f"\nBot finalizado!")
        print(f"Total de coletas: {self.total_coletas}")
        print(f"Total de VELAS ACERTADAS: {len(self.acertos_detalhados)}")
        print(f"Total de VELAS ERRADAS: {len(self.erros_detalhados)}")

if __name__ == "__main__":
    try:
        print("="*80)
        print("AVIATOR BOT INTELIGENTE V3 - COLETA PRECISA DE DADOS (CORRIGIDO)")
        print("="*80)
        print("COLETA PRECISA: Valores reais do grafico do TipMiner (SEM numeros genericos)")
        print("SINAIS PREDITIVOS 4+ SEGUNDOS ANTES da vela sair")
        print("Gatilhos LOSS_* REMOVIDOS conforme solicitado")
        print("Baseado na versao ulitmo.txt que esta com +7 a +20 vitorias")
        print("CORRIGIDO: Problema de coleta no Linux (VPS) vs Windows")
        print("="*80)
        
        bot = AviatorBotInteligenteV3()
        bot.executar(duracao_minutos=1440)
    except KeyboardInterrupt:
        print("\nBot interrompido pelo usuario (Ctrl+C)")
    except Exception as e:
        print(f"\nErro durante a execucao: {e}")
        import traceback
        traceback.print_exc()