import re
from io import BytesIO

import docx
import pypdf

# Canonical skill name -> lowercase aliases that count as a mention.
SKILLS = {
    "Python": ["python"],
    "Machine Learning": ["machine learning", "ml"],
    "Deep Learning": ["deep learning"],
    "NLP": ["nlp", "natural language processing"],
    "LLMs": ["llm", "llms", "large language model", "large language models"],
    "PyTorch": ["pytorch"],
    "TensorFlow": ["tensorflow"],
    "Scikit-learn": ["scikit-learn", "sklearn"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "FastAPI": ["fastapi"],
    "Flask": ["flask"],
    "Django": ["django"],
    "REST APIs": ["rest api", "rest apis", "restful"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "CI/CD": ["ci/cd", "cicd", "ci cd", "continuous integration"],
    "Git": ["git", "github", "gitlab"],
    "SQL": ["sql", "mysql", "sqlite"],
    "PostgreSQL": ["postgresql", "postgres"],
    "MongoDB": ["mongodb"],
    "Redis": ["redis"],
    "Spark": ["spark", "pyspark"],
    "Kafka": ["kafka"],
    "AWS": ["aws", "amazon web services"],
    "Azure": ["azure"],
    "GCP": ["gcp", "google cloud"],
    "Linux": ["linux"],
    "System Design": ["system design"],
    "Data Engineering": ["data engineering"],
    "Streamlit": ["streamlit"],
    "React": ["react", "reactjs"],
    "JavaScript": ["javascript"],
    "TypeScript": ["typescript"],
    "Java": ["java"],
    "C++": ["c++"],
    "Agile": ["agile", "scrum"],
}


def _mentions(text: str, aliases) -> bool:
    """Whole-word match, so 'git' does not hit 'digital' and 'sql' does not hit 'postgresql'."""
    for alias in aliases:
        if re.search(rf"(?<![a-z0-9+#]){re.escape(alias)}(?![a-z0-9+#])", text):
            return True
    return False


def extract_text_from_file(uploaded_file) -> str:
    """Extracts raw text from a PDF or DOCX upload. Raises ValueError with a readable message on failure."""
    filename = uploaded_file.name.lower()
    data = uploaded_file.getvalue()  # getvalue() is safe on every Streamlit rerun; read() is not

    try:
        if filename.endswith(".pdf"):
            reader = pypdf.PdfReader(BytesIO(data))
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    raise ValueError("This PDF is password-protected. Remove the password and upload it again.")
            return "\n".join((page.extract_text() or "") for page in reader.pages)

        if filename.endswith(".docx"):
            document = docx.Document(BytesIO(data))
            parts = [p.text for p in document.paragraphs]
            for table in document.tables:
                for row in table.rows:
                    parts.extend(cell.text for cell in row.cells)
            return "\n".join(parts)
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"Could not read this file ({type(e).__name__}). Try re-saving it as PDF or DOCX.")

    raise ValueError("Unsupported file type. Upload a PDF or DOCX.")


def parse_resume(uploaded_file, job_description: str) -> dict:
    """Compares a resume with a job description over a fixed skill vocabulary."""
    result = {
        "match_score": None,
        "matched_skills": [],
        "missing_skills": [],
        "raw_text_length": 0,
        "error": None,
        "note": None,
    }

    try:
        resume_text = extract_text_from_file(uploaded_file)
    except ValueError as e:
        result["error"] = str(e)
        return result

    resume = re.sub(r"\s+", " ", resume_text.lower())
    jd = re.sub(r"\s+", " ", job_description.lower())
    result["raw_text_length"] = len(resume_text.strip())

    if result["raw_text_length"] < 30:
        result["error"] = ("No readable text found. This looks like a scanned or image-only file. "
                           "Upload a text-based PDF or a DOCX.")
        return result

    required = [name for name, aliases in SKILLS.items() if _mentions(jd, aliases)]
    if not required:
        result["note"] = ("None of the skills I track were found in this job description. "
                          "Paste the full requirements section.")
        return result

    result["matched_skills"] = [s for s in required if _mentions(resume, SKILLS[s])]
    result["missing_skills"] = [s for s in required if s not in result["matched_skills"]]
    result["match_score"] = round(len(result["matched_skills"]) / len(required) * 100)
    return result
