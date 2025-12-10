import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import unicodedata
import traceback

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print(f"\n🚀 SERVIDOR ONLINE: {BASE_DIR}")

# --- ARQUIVOS ---
FILE_GDP = 'API_NY.GDP.MKTP.CD_DS2_en_csv_v2_2463.csv'
FILE_IMP = 'API_NE.IMP.GNFS.CD_DS2_en_csv_v2_2474.csv'
FILE_RES = 'API_FI.RES.TOTL.CD_DS2_en_csv_v2_2475.csv' 
FILE_TRADE = 'comercio.csv'

# --- CARREGAMENTO ---
def carregar_wb(nome):
    path = os.path.join(BASE_DIR, nome)
    try: return pd.read_csv(path, skiprows=4)
    except: return pd.DataFrame()

def carregar_simples(nome):
    path = os.path.join(BASE_DIR, nome)
    try:
        df = pd.read_csv(path)
        if len(df.columns) < 2: df = pd.read_csv(path, sep=';')
        df.columns = [str(c).strip().lower() for c in df.columns]
        return df
    except: return pd.DataFrame()

df_gdp = carregar_wb(FILE_GDP)
df_imp = carregar_wb(FILE_IMP)
df_res = carregar_wb(FILE_RES) 
df_trade = carregar_simples(FILE_TRADE)

KEYWORDS = {
    'NEORREALISMO': ['soberania', 'segurança', 'defesa', 'militar', 'ameaça', 'guerra', 'território', 'inimigo', 'nuclear', 'poder', 'força', 'balança', 'coerção', 'autonomia'],
    'LIBERALISMO': ['comércio', 'acordo', 'parceria', 'cooperação', 'investimento', 'global', 'regras', 'lei', 'instituições', 'negociação', 'ganhos', 'mercado', 'omc'],
    'CONSTRUTIVISMO': ['identidade', 'justiça', 'história', 'valores', 'tradição', 'humilhação', 'imperialismo', 'povo', 'nação', 'legitimidade', 'cultura', 'orgulho']
}

# --- FUNÇÕES ---
def buscar_iso(termo):
    if not termo: return None
    termo = str(termo).strip().upper()
    if len(termo) == 3: return termo
    
    if not df_gdp.empty:
        try:
            match = df_gdp[df_gdp['Country Name'].astype(str).str.upper().str.contains(termo, na=False)]
            if not match.empty: return match.iloc[0]['Country Code']
        except: pass
    return None

def get_valor_historico(df, iso, ano):
    if df.empty or not iso: return 0
    try:
        row = df[df['Country Code'] == iso]
        if row.empty: return 0
        for i in range(6):
            y = str(int(ano) - i)
            if y in row.columns and pd.notna(row.iloc[0][y]): return float(row.iloc[0][y])
    except: pass
    return 0

def get_trade(iso_a, iso_b, ano):
    if df_trade.empty: return 0
    try:
        cols = df_trade.columns
        c_exp = next((c for c in cols if 'exp' in c), cols[0])
        c_imp = next((c for c in cols if 'imp' in c), cols[1])
        c_val = next((c for c in cols if 'val' in c), cols[-1])
        c_year = next((c for c in cols if 'year' in c), None)
        
        df_trade[c_exp] = df_trade[c_exp].astype(str).str.upper().str.strip()
        df_trade[c_imp] = df_trade[c_imp].astype(str).str.upper().str.strip()
        
        mask = ((df_trade[c_exp] == iso_a) & (df_trade[c_imp] == iso_b)) | \
               ((df_trade[c_exp] == iso_b) & (df_trade[c_imp] == iso_a))
        
        if c_year: mask = mask & (df_trade[c_year].astype(str).str.contains(str(ano)))
            
        return float(df_trade[mask][c_val].sum())
    except: return 0

def analisar_retorica(texto):
    if not texto: return "Neutro", []
    try:
        texto = unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode("utf-8").lower()
        scores = {'NEORREALISMO': 0, 'LIBERALISMO': 0, 'CONSTRUTIVISMO': 0}
        encontradas = []
        for teoria, lista in KEYWORDS.items():
            for p in lista:
                if p in texto:
                    scores[teoria] += 1
                    encontradas.append(p)
        vencedor = max(scores, key=scores.get)
        return (vencedor if scores[vencedor] > 0 else "Neutro"), list(set(encontradas))
    except: return "Neutro", []

def gerar_diagnostico_detalhado(teoria_final, asym, dep, resil, rhet_tone, words, alvo, sancionador):
    argumentos = []
    
    argumentos.append(f"A projeção da <b>resposta de {alvo}</b> baseia-se nos seguintes incentivos estruturais:")

    if asym > 10:
        argumentos.append(f"Devido à <b>assimetria de poder extrema ({asym:.1f}x)</b> a favor de {sancionador}, a sobrevivência do Estado torna-se a prioridade. A teoria prevê que {alvo} buscará resistir para garantir sua soberania (Lógica Neorrealista).")
    elif dep > 5:
        argumentos.append(f"Devido à <b>alta dependência comercial ({dep:.1f}% do PIB)</b>, o custo de uma ruptura seria catastrófico. A teoria Liberal prevê que {alvo} tenderá a ceder ou negociar.")
    else:
        argumentos.append(f"Com uma dependência baixa ({dep:.1f}%) e assimetria moderada, {alvo} possui margem de manobra para resistir sem riscos imediatos (Realismo Clássico).")

    if resil > 15:
        argumentos.append(f"Além disso, a <b>alta resiliência ({resil:.1f} meses de reservas)</b> fornece um 'escudo financeiro', permitindo que {alvo} sustente uma postura de confrontação (Realismo Defensivo).")
    elif resil < 3:
        argumentos.append(f"Contudo, a <b>escassez de reservas ({resil:.1f} meses)</b> limita drasticamente a capacidade de {alvo} de sustentar uma guerra comercial.")

    if rhet_tone != "Neutro":
        termos = ", ".join([f"'{w}'" for w in words[:3]])
        argumentos.append(f"Politicamente, o discurso oficial sinaliza uma postura <b>{rhet_tone.title()}</b> (ex: {termos}), reforçando a direção apontada pelos dados.")
    
    if "DIVERGENTE" in teoria_final:
        argumentos.append(f"<b>Previsão:</b> O cenário é DIVERGENTE. Economicamente, {alvo} deveria negociar, mas politicamente sinaliza confronto ({rhet_tone}).")
    else:
        argumentos.append(f"<b>Previsão:</b> Todos os indicadores convergem para uma reação guiada pelo <b>{teoria_final}</b>.")

    return " ".join(argumentos)

@app.route('/api/country/<term>')
def get_country_route(term):
    year = request.args.get('year', default=2023, type=int)
    iso = buscar_iso(term)
    if not iso: return jsonify({"error": "País não encontrado"}), 404
    
    return jsonify({
        "iso_code": iso,
        "gdp_nominal": get_valor_historico(df_gdp, iso, year),
        "imports_total": get_valor_historico(df_imp, iso, year),
        "international_reserves": get_valor_historico(df_res, iso, year) 
    })

@app.route('/api/trade')
def get_trade_route():
    t, s = request.args.get('target'), request.args.get('sanctioner')
    year = request.args.get('year', default=2023, type=int)
    return jsonify({"total_trade": get_trade(buscar_iso(t), buscar_iso(s), year)})

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        d = request.json
        year = int(d.get('year', 2023))
        
        iso_t = buscar_iso(d.get('target'))
        iso_s = buscar_iso(d.get('sanctioner'))

        def resolver_valor(key_manual, df, iso, ano):
            val_manual = d.get(key_manual)
            if val_manual is not None and str(val_manual).strip() != "":
                return float(val_manual)
            return get_valor_historico(df, iso, ano)

        gdp_t = resolver_valor('manual_gdp_target', df_gdp, iso_t, year)
        gdp_s = resolver_valor('manual_gdp_sanctioner', df_gdp, iso_s, year)
        imp_t = resolver_valor('manual_imports_target', df_imp, iso_t, year)
        res_t = resolver_valor('manual_reserves_target', df_res, iso_t, year)

        trade = d.get('manual_trade_val')
        if trade is not None and str(trade).strip() != "":
            trade = float(trade)
        else:
            trade = get_trade(iso_t, iso_s, year)

        asym = (gdp_s / gdp_t) if gdp_t > 0 else 0
        dep = ((trade / gdp_t) * 100) if gdp_t > 0 else 0
        burn_rate = (imp_t / 12) if imp_t > 0 else 0
        resil = (res_t / burn_rate) if burn_rate > 0 else 0

        t_mat = "INCONCLUSIVO"
        expl_mat = "Dados insuficientes."
        
        if gdp_t > 0:
            if asym > 10: t_mat, expl_mat = "NEORREALISMO (Resistência)", f"Assimetria Extrema ({asym:.1f}x) força foco em sobrevivência."
            elif dep > 5: t_mat, expl_mat = "LIBERALISMO (Acomodação)", f"Custo de ruptura insustentável (Dep. {dep:.1f}%)."
            elif dep > 2: t_mat, expl_mat = "INSTITUCIONALISMO (Negociação)", f"Dependência Moderada ({dep:.1f}%)."
            elif resil > 15: t_mat, expl_mat = "REALISMO DEFENSIVO (Resistência)", f"Alta Resiliência ({resil:.1f}m) permite suportar custos."
            else: t_mat, expl_mat = "REALISMO CLASSICO", "Baixa dependência permite autonomia relativa."

        t_ret, words = analisar_retorica(d.get('rhetoric', ''))
        expl_ret = f"Discurso foca em: {', '.join(words)}." if words else "Tom Neutro/Técnico."

        final = t_mat
        conclusao = "Baseada em incentivos materiais."
        if t_ret != "Neutro":
            if t_mat.split()[0] == t_ret: conclusao = "Convergência (Discurso e Dados alinham)."
            elif "REALISMO" in t_mat and t_ret == "CONSTRUTIVISMO": final = "REALISMO CONSTRUTIVISTA"
            else: final = "DIVERGENTE (Risco de Erro)"

        narrativa = gerar_diagnostico_detalhado(final, asym, dep, resil, t_ret, words, d.get('target'), d.get('sanctioner'))

        return jsonify({
            "data": { 
                "gdp_target": gdp_t, 
                "gdp_sanctioner": gdp_s,  # NOVO CAMPO ADICIONADO
                "resilience_months": resil, 
                "trade": trade, 
                "reserves": res_t 
            },
            "metrics": { "asymmetry": asym, "dependency": dep, "rhetoric_tone": t_ret },
            "analysis": {
                "material_theory": t_mat, 
                "material_explanation": expl_mat,
                "rhetoric_theory": t_ret,
                "rhetoric_explanation": expl_ret,
                "final_theory": final, 
                "conclusion": conclusao,
                "narrative": narrativa, 
                "words": words
            }
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
