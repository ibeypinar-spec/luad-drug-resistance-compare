"""
LUAD Drug Resistance Study — Eksik Veri İndirme Scripti
=======================================================
Hedef dosyalar:
  1. GDSC2_fitted_dose_response_27Oct23.xlsx    (~25 MB)   — GDSC v2 IC50 matrisi
  2. luad_tcga_pan_can_atlas_2018.tar.gz        (~150 MB)  — TCGA-LUAD PanCancer Atlas
  3. HS_CPTAC_LUAD_proteome_*_TUMOR.cct         (~10 MB)   — CPTAC proteom
  4. HS_CPTAC_LUAD_phosphoproteome_*_TUMOR.cct  (~30 MB)   — CPTAC fosforproteom
  5. HS_CPTAC_LUAD_cli.tsi                      (<1 MB)    — CPTAC klinik
  6. OmicsExpressionProteinCodingGenesTPMLogp1.csv (~200 MB) — DepMap 23Q4 expression
  7. Model.csv                                  (~1 MB)    — DepMap hücre hattı metadata

Kullanım: python download_missing_data.py
"""

import os
import sys
import time
import requests

# Windows CP1254 encoding fix — force UTF-8 output
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DOWNLOADS = [
    {
        "name": "GDSC2 IC50 (fitted dose response)",
        "url": "https://cog.sanger.ac.uk/cancerrxgene/GDSC_release8.5/GDSC2_fitted_dose_response_27Oct23.xlsx",
        "filename": "GDSC2_fitted_dose_response_27Oct23.xlsx",
        "subdir": "",
    },
    {
        "name": "TCGA-LUAD PanCancer Atlas (cBioPortal)",
        "url": "https://datahub.assets.cbioportal.org/luad_tcga_pan_can_atlas_2018.tar.gz",
        "filename": "luad_tcga_pan_can_atlas_2018.tar.gz",
        "subdir": "TCGA LUAD",
    },
    {
        "name": "CPTAC-LUAD Proteome (LinkedOmics)",
        "url": "https://linkedomics.org/data_download/CPTAC-LUAD/HS_CPTAC_LUAD_proteome_ratio_NArm_TUMOR.cct",
        "filename": "HS_CPTAC_LUAD_proteome_ratio_NArm_TUMOR.cct",
        "subdir": "CPTAC-LUAD",
    },
    {
        "name": "CPTAC-LUAD Phosphoproteome (LinkedOmics)",
        "url": "https://linkedomics.org/data_download/CPTAC-LUAD/HS_CPTAC_LUAD_phosphoproteome_ratio_norm_NArm_TUMOR.cct",
        "filename": "HS_CPTAC_LUAD_phosphoproteome_ratio_norm_NArm_TUMOR.cct",
        "subdir": "CPTAC-LUAD",
    },
    {
        "name": "CPTAC-LUAD Clinical (LinkedOmics)",
        "url": "https://linkedomics.org/data_download/CPTAC-LUAD/HS_CPTAC_LUAD_cli.tsi",
        "filename": "HS_CPTAC_LUAD_cli.tsi",
        "subdir": "CPTAC-LUAD",
    },
    {
        "name": "CPTAC-LUAD Mutation (LinkedOmics)",
        "url": "https://linkedomics.org/data_download/CPTAC-LUAD/HS_CPTAC_LUAD_somatic_mutation_gene.cbt",
        "filename": "HS_CPTAC_LUAD_somatic_mutation_gene.cbt",
        "subdir": "CPTAC-LUAD",
    },
    {
        "name": "DepMap 23Q4 — Expression (protein-coding genes, TPM log2p1)",
        "url": "https://ndownloader.figshare.com/files/43347204",
        "filename": "OmicsExpressionProteinCodingGenesTPMLogp1.csv",
        "subdir": "DepMap",
    },
    {
        "name": "DepMap 23Q4 — Model metadata (cell line info)",
        "url": "https://ndownloader.figshare.com/files/43746708",
        "filename": "Model.csv",
        "subdir": "DepMap",
    },
    {
        "name": "DepMap 23Q4 — Somatic mutations",
        "url": "https://ndownloader.figshare.com/files/43346730",
        "filename": "OmicsSomaticMutations.csv",
        "subdir": "DepMap",
    },
    {
        "name": "DepMap 23Q4 — Copy number (gene level)",
        "url": "https://ndownloader.figshare.com/files/43346631",
        "filename": "OmicsCNGene.csv",
        "subdir": "DepMap",
    },
]


def format_size(n_bytes):
    """Bayt cinsinden okunabilir boyut."""
    for unit in ["B", "KB", "MB", "GB"]:
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.1f} TB"


def download_file(url, dest_path, name):
    """
    Dosyayı streaming ile indir; progress göster.
    Mevcut dosya varsa ve sıfır boyutlu değilse atla.
    """
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        print(f"  ✔  Zaten mevcut ({format_size(os.path.getsize(dest_path))}): {os.path.basename(dest_path)}")
        return True

    print(f"  ⬇  İndiriliyor: {name}")
    print(f"     URL: {url}")

    try:
        with requests.get(url, stream=True, timeout=60,
                          headers={"User-Agent": "Mozilla/5.0"}) as r:
            r.raise_for_status()
            total = int(r.headers.get("Content-Length", 0))
            downloaded = 0
            start = time.time()

            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 256):  # 256 KB chunks
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / total * 100
                        elapsed = time.time() - start
                        speed = downloaded / elapsed if elapsed > 0 else 0
                        bar = "#" * int(pct / 5) + "-" * (20 - int(pct / 5))
                        print(
                            f"\r     [{bar}] {pct:5.1f}%  "
                            f"{format_size(downloaded)}/{format_size(total)}  "
                            f"{format_size(speed)}/s   ",
                            end="",
                            flush=True,
                        )
            print()  # newline after progress bar
            size = os.path.getsize(dest_path)
            print(f"     ✅ Tamamlandı: {format_size(size)}")
            return True

    except requests.exceptions.RequestException as e:
        print(f"\n     ❌ HATA: {e}")
        if os.path.exists(dest_path) and os.path.getsize(dest_path) == 0:
            os.remove(dest_path)
        return False


def main():
    print("=" * 65)
    print("  LUAD Drug Resistance — Eksik Veri İndirme")
    print("=" * 65)
    print(f"Hedef klasör: {BASE_DIR}\n")

    results = []
    for item in DOWNLOADS:
        # Hedef klasörü oluştur
        subdir = item["subdir"]
        dest_dir = os.path.join(BASE_DIR, subdir) if subdir else BASE_DIR
        os.makedirs(dest_dir, exist_ok=True)

        dest_path = os.path.join(dest_dir, item["filename"])
        ok = download_file(item["url"], dest_path, item["name"])
        results.append((item["name"], item["filename"], ok))
        print()

    # Özet
    print("=" * 65)
    print("  İNDİRME ÖZETİ")
    print("=" * 65)
    success = [r for r in results if r[2]]
    failed  = [r for r in results if not r[2]]

    for name, fname, ok in results:
        icon = "✅" if ok else "❌"
        print(f"  {icon}  {fname}")

    print(f"\nBaşarılı: {len(success)}/{len(results)}")

    if failed:
        print("\nBAŞARISIZ OLANLAR — Manuel indirme gerekebilir:")
        for name, fname, _ in failed:
            print(f"  - {name}")

    # TCGA tarball'u extract et
    tcga_tar = os.path.join(BASE_DIR, "TCGA LUAD", "luad_tcga_pan_can_atlas_2018.tar.gz")
    if os.path.exists(tcga_tar) and os.path.getsize(tcga_tar) > 0:
        print("\n📦 TCGA tarball extract ediliyor...")
        import tarfile
        extract_dir = os.path.join(BASE_DIR, "TCGA LUAD", "luad_tcga_pan_can_atlas_2018")
        os.makedirs(extract_dir, exist_ok=True)
        try:
            with tarfile.open(tcga_tar, "r:gz") as tar:
                tar.extractall(path=extract_dir)
            print(f"  ✅ Extract tamamlandı: {extract_dir}")
            extracted = os.listdir(extract_dir)
            print(f"  Dosyalar: {extracted[:10]}")
        except Exception as e:
            print(f"  ❌ Extract hatası: {e}")

    print("\n✅ Script tamamlandı.")


if __name__ == "__main__":
    main()
