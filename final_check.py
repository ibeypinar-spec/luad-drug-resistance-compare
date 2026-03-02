"""
final_check.py — Tüm proje dosyaları için kapsamlı doğrulama
"""
import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import pandas as pd
import numpy as np

WORK_DIR = "G:\\Drive'\u0131m\\\u00c7al\u0131\u015fma\\Aktif \u00c7al\u0131\u015fmalar\\9. A\u00e7\u0131k eri\u015fim veri \u00e7al\u0131\u015fmalar\u0131\\LUAD Drug Resistance Study"
RES  = os.path.join(WORK_DIR, "results")
PUB  = os.path.join(RES, "publication_figures")
XL2  = os.path.join(RES, "LUAD_Faz2_Results.xlsx")
XL2B = os.path.join(RES, "LUAD_Faz2b_Results.xlsx")

OK  = "[OK] "
ERR = "[!!] "
INF = "[>>] "

issues = []

def check(cond, msg_ok, msg_fail):
    if cond:
        print(f"  {OK}{msg_ok}")
    else:
        print(f"  {ERR}{msg_fail}")
        issues.append(msg_fail)

# ─────────────────────────────────────────────────────────
print("\n" + "="*60)
print("  1. DOSYA ENVANTERİ")
print("="*60)

# Kök dizin dosyaları
root_files = {
    "manuscript_draft_v1.md":          "Makale taslağı (Markdown)",
    "LUAD_manuscript_v1.1.docx":       "Makale Word dosyası",
    "LUAD_manuscript_references.ris":  "Zotero RIS referanslar",
    "LUAD_reference_sentences.md":     "Referans–cümle eşleşmesi",
    "faz2_analysis.py":                "Faz 2 analiz scripti",
    "faz2b_improved.py":               "Faz 2b gelişmiş analiz scripti",
    "generate_figures_publication.py": "Figür üretim scripti",
    "generate_manuscript_docx.py":     "Word üretim scripti",
    "download_missing_data.py":        "Veri indirme scripti",
}

print()
for fname, desc in root_files.items():
    fpath = os.path.join(WORK_DIR, fname)
    if os.path.exists(fpath):
        sz = os.path.getsize(fpath)
        print(f"  {OK}{fname:45s}  {sz//1024:>6} KB   {desc}")
    else:
        print(f"  {ERR}{fname:45s}  BULUNAMADI!   {desc}")
        issues.append(f"Eksik dosya: {fname}")

# results/ altındaki Excel'ler
print()
for fname in ["LUAD_Faz2_Results.xlsx", "LUAD_Faz2b_Results.xlsx"]:
    fpath = os.path.join(RES, fname)
    check(os.path.exists(fpath),
          f"{fname}  ({os.path.getsize(fpath)//1024} KB)",
          f"Eksik: {fname}")

# ─────────────────────────────────────────────────────────
print("\n" + "="*60)
print("  2. FIGÜR DOSYALARI")
print("="*60)

pub_expected = [
    "Figure1_HubKinases.png",
    "Figure1_HubKinases.pdf",
    "Figure2_GDSC2_Correlations.png",
    "Figure2_GDSC2_Correlations.pdf",
    "Figure3_YES1_Survival.png",
    "Figure3_YES1_Survival.pdf",
    "Figure4_KAS_CPTAC.png",
    "Figure4_KAS_CPTAC.pdf",
    "Figure5_CoActivation_Validation.png",
    "Figure5_CoActivation_Validation.pdf",
    "FigureS1_KM_Median_Grid.png",
    "FigureS1_KM_Median_Grid.pdf",
]
print()
for fname in pub_expected:
    fpath = os.path.join(PUB, fname)
    if os.path.exists(fpath):
        sz = os.path.getsize(fpath)
        size_ok = sz > 50_000  # en az 50 KB bekleniyor
        tag = OK if size_ok else ERR
        note = "" if size_ok else " <- ÇOK KÜÇÜK?"
        print(f"  {tag}{fname:50s}  {sz//1024:>5} KB{note}")
        if not size_ok:
            issues.append(f"Figür çok küçük: {fname} ({sz} byte)")
    else:
        print(f"  {ERR}{fname:50s}  BULUNAMADI!")
        issues.append(f"Eksik figür: {fname}")

# ─────────────────────────────────────────────────────────
print("\n" + "="*60)
print("  3. EXCEL VERİ DOĞRULAMA")
print("="*60)

# Faz 2 Excel
print(f"\n  >> LUAD_Faz2_Results.xlsx")
try:
    # Hub kinases
    hub = pd.read_excel(XL2, sheet_name='1_Hub_Kinazlar')
    kin_col = [c for c in hub.columns if 'kinase' in c.lower() or 'kinaz' in c.lower()][0]
    sub_col = [c for c in hub.columns if 'sub' in c.lower() or 'n_' in c.lower()][0]
    top = hub.sort_values(sub_col, ascending=False).head(1)
    ptk2_n = hub[hub[kin_col]=='PTK2'][sub_col].values
    check(len(ptk2_n)>0 and ptk2_n[0]==195,
          f"PTK2 = 195 substrat [doğru]",
          f"PTK2 substrat sayısı hatalı: {ptk2_n}")
    focal = hub[hub[sub_col]>=100]
    check(len(focal)==9,
          f"9 odak kinaz (>=100 substrat) [doğru]",
          f"Odak kinaz sayısı hatalı: {len(focal)}")

    # Cox regression
    cox = pd.read_excel(XL2, sheet_name='4_Cox_Regression')
    cov = cox.columns[0]
    hr_col = [c for c in cox.columns if 'exp' in c.lower() and 'coef' in c.lower()
              and 'lower' not in c.lower() and 'upper' not in c.lower()][0]
    p_col = [c for c in cox.columns if c.lower()=='p' or
             (c.lower().startswith('p') and len(c)<=2)][0]
    yes1_row = cox[cox[cov]=='YES1']
    if len(yes1_row) > 0:
        hr_val  = float(yes1_row[hr_col].values[0])
        p_val   = float(yes1_row[p_col].values[0])
        check(1.25 <= hr_val <= 1.31,
              f"YES1 HR = {hr_val:.3f} (beklenen ~1.28) [doğru]",
              f"YES1 HR hatalı: {hr_val:.3f}")
        check(p_val < 0.05,
              f"YES1 p = {p_val:.4f} < 0.05 [anlamlı]",
              f"YES1 p değeri beklenmedik: {p_val:.4f}")
    else:
        print(f"  {ERR}YES1 satırı bulunamadı!")
        issues.append("Cox tablosunda YES1 yok")

    # pARACNe validation
    val = pd.read_excel(XL2, sheet_name='6_pARACNe_Validation')
    fdr_col = [c for c in val.columns if 'fdr' in c.lower()][0]
    n_sig = (val[fdr_col] < 0.05).sum()
    check(n_sig == 37,
          f"pARACNe doğrulama: {n_sig} çift FDR<0.05 [doğru]",
          f"pARACNe doğrulama sayısı hatalı: {n_sig} (beklenen 37)")

    # CPTAC KAS
    kas = pd.read_excel(XL2, sheet_name='5_CPTAC_KAS')
    kinases = [k for k in ['PTK2','MET','EGFR','DDR1','LCK','YES1','FYN','LYN','SRC']
               if k in kas.columns]
    check(len(kinases)==9,
          f"CPTAC KAS: 9 kinaz mevcut [doğru]",
          f"CPTAC KAS eksik kinazlar: {set(['PTK2','MET','EGFR','DDR1','LCK','YES1','FYN','LYN','SRC'])-set(kinases)}")
    check(len(kas)==110,
          f"CPTAC KAS: 110 hasta [doğru]",
          f"CPTAC KAS hasta sayısı hatalı: {len(kas)}")

except Exception as e:
    print(f"  {ERR}Faz2 Excel okuma hatası: {e}")
    issues.append(f"Faz2 Excel hatası: {e}")

# Faz 2b Excel
print(f"\n  >> LUAD_Faz2b_Results.xlsx")
try:
    # Tertile KM
    tkm = pd.read_excel(XL2B, sheet_name='3_KM_Tertile')
    kin_col2 = tkm.columns[0]
    p_cols = [c for c in tkm.columns if 'p' in c.lower() and 'fdr' not in c.lower()]
    fdr_cols = [c for c in tkm.columns if 'fdr' in c.lower()]
    if p_cols and fdr_cols:
        lck_row  = tkm[tkm[kin_col2]=='LCK']
        yes1_row2 = tkm[tkm[kin_col2]=='YES1']
        if len(lck_row)>0:
            lck_fdr = float(lck_row[fdr_cols[0]].values[0])
            check(lck_fdr < 0.05,
                  f"LCK tertile FDR = {lck_fdr:.4f} < 0.05 [anlamlı]",
                  f"LCK tertile FDR beklenmedik: {lck_fdr:.4f}")
        if len(yes1_row2)>0:
            yes1_fdr = float(yes1_row2[fdr_cols[0]].values[0])
            check(yes1_fdr < 0.05,
                  f"YES1 tertile FDR = {yes1_fdr:.4f} < 0.05 [anlamlı]",
                  f"YES1 tertile FDR beklenmedik: {yes1_fdr:.4f}")

    # PCA
    pca = pd.read_excel(XL2B, sheet_name='4_KAS_PCA')
    pc1_col = [c for c in pca.columns if 'pc1' in c.lower()][0]
    # PC1 explained variance should be ~80.8%
    # (might be stored as metadata or first row)
    print(f"  {INF}PCA sheet sütunları: {list(pca.columns[:5])}")

    # Co-activation
    coact = pd.read_excel(XL2B, sheet_name='5_CoActivation_CPTAC')
    print(f"  {INF}Co-activation boyutu: {coact.shape}")
    # Try to find YES1-FYN correlation
    if 'YES1' in coact.columns and 'FYN' in coact.index or 'YES1' in coact.index:
        mat = coact.set_index(coact.columns[0]) if coact.index.dtype!=object else coact
        if 'YES1' in mat.index and 'FYN' in mat.columns:
            rho = float(mat.loc['YES1','FYN'])
            check(rho > 0.99,
                  f"YES1-FYN co-activation rho = {rho:.3f} (beklenen ~0.999) [doğru]",
                  f"YES1-FYN rho beklenmedik: {rho:.3f}")

    # GDSC2 full scan
    gdsc = pd.read_excel(XL2B, sheet_name='1_GDSC2_Full_Scan')
    check(len(gdsc) == 2574,
          f"GDSC2 tam tarama: {len(gdsc)} test (beklenen 2574) [doğru]",
          f"GDSC2 test sayısı hatalı: {len(gdsc)}")

except Exception as e:
    print(f"  {ERR}Faz2b Excel okuma hatası: {e}")
    issues.append(f"Faz2b Excel hatası: {e}")

# ─────────────────────────────────────────────────────────
print("\n" + "="*60)
print("  4. MANUSCRIPT PLACEHOLDER TARAMASI")
print("="*60)

import re
md_path = os.path.join(WORK_DIR, "manuscript_draft_v1.md")
with open(md_path, encoding='utf-8') as f:
    md_text = f.read()

# Sayısal placeholder'lar
numeric_ph = re.findall(r'\[X\]|\[N\]|\[n\]|\[value\]|\[results.*?\]|\[TO UPDATE.*?\]', md_text)
# Referans placeholder'lar
cite_ph = re.findall(r'\[CITE[^\]]*\]', md_text)
# Yazar bilgisi
author_ph = re.findall(r'\[Author.*?\]|\[email\]|\[GitHub.*?\]|\[To be completed\]|\[Bansal.*?\]', md_text)

print(f"\n  Sayısal placeholder: {len(numeric_ph)}")
for ph in set(numeric_ph):
    print(f"    - {ph}")

print(f"\n  Referans [CITE] placeholder: {len(cite_ph)}")
for ph in set(cite_ph):
    print(f"    - {ph}")

print(f"\n  Yazar/Kişisel bilgi placeholder: {len(author_ph)}")
for ph in list(set(author_ph))[:10]:
    print(f"    - {ph}")

# Kritik sayılar — manuscript'te doğru mu?
print(f"\n  Kritik sayı kontrolleri:")
checks_text = [
    ("195", "PTK2 195 substrat"),
    ("1.28", "YES1 HR=1.28"),
    ("1.03", "YES1 95%CI lower"),
    ("1.60", "YES1 95%CI upper"),
    ("0.028", "YES1 p=0.028"),
    ("0.018", "LCK FDR=0.018"),
    ("0.027", "YES1 FDR=0.027"),
    ("4.9%", "pARACNe doğrulama 4.9%"),
    ("80.8%", "PCA PC1=80.8%"),
    ("0.999", "YES1-FYN rho=0.999"),
    ("0.912", "LYN-YES1 rho=0.912"),
    ("3.06", "Osimertinib effect size"),
    ("62", "GDSC2 hücre hattı sayısı"),
    ("497", "TCGA-LUAD hasta sayısı"),
    ("110", "CPTAC hasta sayısı"),
    ("2,574", "GDSC2 test sayısı"),
]
for val, desc in checks_text:
    found = val in md_text
    tag = OK if found else ERR
    note = "" if found else " <- BULUNAMADI!"
    print(f"    {tag}{desc}: '{val}'{note}")
    if not found:
        issues.append(f"Manuscript'te bulunamadı: {val} ({desc})")

# ─────────────────────────────────────────────────────────
print("\n" + "="*60)
print("  5. RIS DOSYASI KONTROLÜ")
print("="*60)

ris_path = os.path.join(WORK_DIR, "LUAD_manuscript_references.ris")
with open(ris_path, encoding='utf-8') as f:
    ris_text = f.read()

n_refs = ris_text.count('TY  - JOUR')
check(n_refs == 12,
      f"RIS: {n_refs} referans [doğru]",
      f"RIS referans sayısı hatalı: {n_refs} (beklenen 12)")

# DOI kontrolü
dois = re.findall(r'DO  - (.+)', ris_text)
check(len(dois) == 12,
      f"RIS: {len(dois)} DOI mevcut [doğru]",
      f"RIS eksik DOI: {len(dois)}/12")

# Anahtar referanslar
key_refs = {
    'Bansal': '10.1371/journal.pone.0208646',
    'Koga':   '10.1158/1078-0432.CCR-19-3228',
    'Iorio':  '10.1016/j.cell.2016.06.017',
}
for author, doi in key_refs.items():
    check(doi in ris_text,
          f"  {author} DOI doğru",
          f"  {author} DOI hatalı/eksik: {doi}")

# ─────────────────────────────────────────────────────────
print("\n" + "="*60)
print("  6. WORD DOSYASI KONTROLÜ")
print("="*60)

docx_path = os.path.join(WORK_DIR, "LUAD_manuscript_v1.1.docx")
docx_size  = os.path.getsize(docx_path) if os.path.exists(docx_path) else 0
check(os.path.exists(docx_path),
      f"LUAD_manuscript_v1.1.docx mevcut ({docx_size//1024} KB)",
      "LUAD_manuscript_v1.1.docx bulunamadı!")
check(docx_size > 2_000_000,
      f"Word boyutu {docx_size//1024} KB (figürler dahil, yeterli)",
      f"Word dosyası çok küçük ({docx_size//1024} KB) — figürler eksik olabilir")

# python-docx ile içerik kontrolü
try:
    from docx import Document
    doc = Document(docx_path)
    full_text = ' '.join(p.text for p in doc.paragraphs)
    word_checks = [
        ("YES1", "YES1 adı geçiyor"),
        ("1.28", "YES1 HR=1.28 geçiyor"),
        ("80.8%", "PC1=80.8% geçiyor"),
        ("REFERENCES", "Referanslar bölümü mevcut"),
        ("FIGURES", "Figürler bölümü mevcut"),
        ("Table 1", "Tablo 1 mevcut"),
        ("Table 2", "Tablo 2 mevcut"),
    ]
    # Count images
    from docx.oxml.ns import qn
    n_images = len(doc.inline_shapes)
    check(n_images >= 6,
          f"Word içinde {n_images} gömülü resim (≥6 bekleniyor)",
          f"Word içinde yalnızca {n_images} resim — figürler eksik olabilir")
    for val, desc in word_checks:
        check(val in full_text,
              desc,
              f"Word'de bulunamadı: '{val}'")
except Exception as e:
    print(f"  {ERR}Word içerik kontrolü hatası: {e}")

# ─────────────────────────────────────────────────────────
print("\n" + "="*60)
print("  ÖZET")
print("="*60)
if issues:
    print(f"\n  Toplam sorun: {len(issues)}")
    for i, iss in enumerate(issues, 1):
        print(f"  {i:2d}. {iss}")
else:
    print(f"\n  Tüm kontroller başarılı! Sorun tespit edilmedi.")

print("\n  Tamamlandı.\n")
