import os
import re
import subprocess
import shutil
from pathlib import Path

# --------- SETTINGS ----------
PROJECT_DIR = Path(__file__).parent      # folder where script lives
OUTPUT_DIR = PROJECT_DIR / "PDFs"       # folder to save PDFs
# -----------------------------

# Regex to find pdftitle in hypersetup
TITLE_RE = re.compile(r"pdftitle\s*=\s*\{([^}]*)\}")

def extract_pdftitle(tex_file: Path) -> str | None:
    """Return the pdftitle from a .tex file, or None if not found."""
    text = tex_file.read_text(encoding="utf-8", errors="ignore")
    match = TITLE_RE.search(text)
    if match:
        return match.group(1).strip()
    return None

def build_pdf(tex_file: Path, pdf_title: str, output_dir: Path):
    """Compile tex_file into PDF named after pdf_title and clean aux files."""
    safe_name = pdf_title.replace(" ", "_")  # safe filename
    jobname = safe_name
    print(f"▶ Building {tex_file} → {safe_name}.pdf")

    # Compile with latexmk
    subprocess.run(
        ["latexmk", "-pdf", f"-jobname={jobname}", str(tex_file)],
        cwd=tex_file.parent,
        check=True
    )

    # Move the PDF to output folder
    generated_pdf = tex_file.parent / f"{safe_name}.pdf"
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(generated_pdf), output_dir / f"{safe_name}.pdf")

    # Clean auxiliary files
    subprocess.run(
        ["latexmk", "-c", f"-jobname={jobname}", str(tex_file)],
        cwd=tex_file.parent,
        check=False
    )

def main():
    # Only include .tex files outside the output folder
    tex_files = [f for f in PROJECT_DIR.rglob("*.tex") if OUTPUT_DIR not in f.parents]
    print(f"Found {len(tex_files)} .tex files")

    for tex_file in tex_files:
        pdftitle = extract_pdftitle(tex_file)
        if pdftitle:
            try:
                build_pdf(tex_file, pdftitle, OUTPUT_DIR)
            except subprocess.CalledProcessError:
                print(f"❌ Failed to compile {tex_file}")
        else:
            print(f"⚠ No pdftitle in {tex_file}, skipping")

    print(f"\n✅ All PDFs saved to: {OUTPUT_DIR.resolve()}")

if __name__ == "__main__":
    main()
