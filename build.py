import os
import re
import subprocess
import shutil
import shlex
from pathlib import Path

# --------- SETTINGS ----------
PROJECT_DIR = Path(__file__).parent / "latex"         # folder where .tex files live
OUTPUT_DIR = (PROJECT_DIR / "../PDFs").resolve()      # folder to save PDFs
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


def sanitize_for_jobname(name: str) -> str:
    """
    Sanitize the jobname for LaTeX:
    - Remove or replace characters that latexmk/biber can't handle in jobnames.
    - Keep a mapping so the final PDF can still use the original name.
    """
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return safe[:100]  # latexmk jobname limit


def build_pdf(tex_file: Path, pdf_title: str, output_dir: Path):
    """Compile tex_file into PDF named exactly after pdf_title and clean aux files."""
    safe_jobname = sanitize_for_jobname(pdf_title)
    final_pdf_name = f"{pdf_title}.pdf"

    print(f"▶ Building {tex_file.name} → {final_pdf_name}")

    # Compile with latexmk (Biber will be called automatically)
    cmd = [
        "latexmk",
        "-pdf",
        f"-jobname={safe_jobname}",
        str(tex_file)
    ]

    # Run latexmk safely (no shell interpretation issues)
    subprocess.run(cmd, cwd=tex_file.parent, check=True)

    # Move PDF to output folder with the pretty name
    generated_pdf = tex_file.parent / f"{safe_jobname}.pdf"
    if not generated_pdf.exists():
        raise FileNotFoundError(f"Expected PDF not found: {generated_pdf}")

    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(generated_pdf), output_dir / final_pdf_name)

    # Clean auxiliary files
    subprocess.run(
        ["latexmk", "-c", f"-jobname={safe_jobname}", str(tex_file)],
        cwd=tex_file.parent,
        check=False
    )

    # Extra cleanup
    for ext in [".aux", ".log", ".fdb_latexmk", ".fls", ".toc", ".out"]:
        aux_file = tex_file.parent / f"{safe_jobname}{ext}"
        if aux_file.exists():
            aux_file.unlink()


def main():
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
