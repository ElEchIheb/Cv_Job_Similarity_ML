"""Donnees fictives de demonstration (aucune personne reelle)."""
JOB_TITLE = "Machine Learning Engineer"
JOB_DESC = (
    "We are looking for a Machine Learning Engineer to design, train and deploy "
    "production ML models. You will build data and training pipelines, expose models "
    "through REST APIs, containerize services and monitor them in the cloud. "
    "Required: strong Python, PyTorch or TensorFlow, Docker and Kubernetes, FastAPI, "
    "PostgreSQL, MLflow, AWS and CI/CD. Minimum 3 years of experience. "
    "Good communication and teamwork skills are mandatory."
)
JOB_SKILLS = "Python, PyTorch, TensorFlow, Docker, Kubernetes, FastAPI, PostgreSQL, MLflow, AWS, CI/CD"

CVS = {
    "Amira_Khelifi": {
        "name": "Amira Khelifi", "email": "amira.khelifi@example.com",
        "headline": "Senior Machine Learning Engineer",
        "sections": [
            ("PROFILE", ["Senior Machine Learning Engineer with 6 years of experience designing, training and deploying production ML models and data pipelines."]),
            ("SKILLS", ["Python, PyTorch, TensorFlow, scikit-learn, MLflow, Docker, Kubernetes, FastAPI, PostgreSQL, AWS, CI/CD, Git, Linux.",
                        "Strong communication, teamwork and mentoring skills."]),
            ("EXPERIENCE", ["2021 - 2026: Senior ML Engineer, DataNova. Built and deployed deep learning models with PyTorch, served through FastAPI on Kubernetes (AWS). Tracked experiments with MLflow and automated releases with CI/CD.",
                            "2019 - 2021: ML Engineer, Insight Labs. Developed training pipelines in Python and TensorFlow, containerized services with Docker, stored features in PostgreSQL."]),
            ("EDUCATION", ["Engineering degree in Computer Science - Data Science track."]),
            ("CERTIFICATIONS", ["AWS Certified Machine Learning - Specialty."]),
            ("LANGUAGES", ["Arabic (native), French (fluent), English (fluent)."]),
        ],
    },
    "Mehdi_Gharbi": {
        "name": "Mehdi Gharbi", "email": "mehdi.gharbi@example.com",
        "headline": "Data Scientist",
        "sections": [
            ("PROFILE", ["Data Scientist with 3 years of experience in predictive modelling and analytics for retail and finance."]),
            ("SKILLS", ["Python, scikit-learn, TensorFlow, pandas, SQL, PostgreSQL, Docker (basics), Git.", "Communication and teamwork."]),
            ("EXPERIENCE", ["2023 - 2026: Data Scientist, RetailMetrics. Built forecasting and churn models in Python and TensorFlow, delivered dashboards and reports.",
                            "2022 - 2023: Junior Data Analyst, FinData. SQL reporting on PostgreSQL and exploratory analysis."]),
            ("EDUCATION", ["Master's degree in Statistics and Data Analysis."]),
            ("LANGUAGES", ["Arabic (native), French (fluent), English (intermediate)."]),
        ],
    },
    "Lina_Mansour": {
        "name": "Lina Mansour", "email": "lina.mansour@example.com",
        "headline": "Ingenieure logiciel backend",
        "sections": [
            ("PROFIL", ["Ingenieure logiciel backend avec 4 ans d'experience dans la conception d'API et de services conteneurises."]),
            ("COMPETENCES", ["Python, FastAPI, PostgreSQL, Docker, CI/CD, Git, Linux, tests automatises.", "Travail en equipe, communication, autonomie."]),
            ("EXPERIENCE", ["2022 - 2026 : Ingenieure backend, CloudWare. Developpement d'API REST avec FastAPI et PostgreSQL, conteneurisation Docker, pipelines CI/CD.",
                            "2021 - 2022 : Developpeuse Python, WebSoft. Services web et automatisation des tests."]),
            ("FORMATION", ["Diplome d'ingenieur en genie logiciel."]),
            ("LANGUES", ["Arabe (langue maternelle), francais (courant), anglais (professionnel)."]),
        ],
    },
    "Karim_Jaziri": {
        "name": "Karim Jaziri", "email": "karim.jaziri@example.com",
        "headline": "Marketing & Graphic Designer",
        "sections": [
            ("PROFILE", ["Creative marketing specialist and graphic designer with 5 years of experience in branding and social media campaigns."]),
            ("SKILLS", ["Adobe Photoshop, Illustrator, Figma, content writing, social media management, SEO basics.", "Creativity, communication."]),
            ("EXPERIENCE", ["2021 - 2026: Marketing Designer, BrandUp Agency. Designed visual identities and managed advertising campaigns.",
                            "2020 - 2021: Freelance graphic designer."]),
            ("EDUCATION", ["Bachelor's degree in Graphic Design."]),
            ("LANGUAGES", ["Arabic (native), French (fluent), English (intermediate)."]),
        ],
    },
}

def cv_text(key):
    c = CVS[key]
    out = [c["name"], c["headline"], ""]
    for title, lines in c["sections"]:
        out.append(title); out.extend(lines); out.append("")
    return "\n".join(out)
