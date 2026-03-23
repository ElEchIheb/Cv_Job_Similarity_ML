from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

import pandas as pd

from generate_skills_dictionary import write_skills_dictionary


ROOT = Path(__file__).resolve().parent
SKILLS_PATH = ROOT / "skills_dictionary.json"
OUTPUT_PATH = ROOT / "cv_job_dataset.csv"
DEFAULT_SIZE = 12000
DEFAULT_SEED = 42

DOMAIN_BLUEPRINTS: Dict[str, Dict[str, object]] = {
    "Data Science / ML Engineering": {
        "titles": ["Data Scientist", "ML Engineer", "Applied Scientist"],
        "categories": ["programming_languages", "machine_learning", "data_engineering", "analytics_bi"],
        "anchors": ["python", "scikit-learn", "tensorflow", "pytorch", "mlflow", "feature engineering"],
        "soft": ["communication", "critical thinking", "analytical thinking", "experimentation"],
        "related": ["AI / NLP / LLM Engineering", "Data Engineering / Analytics Engineering", "BI / Analytics / Visualization"],
    },
    "AI / NLP / LLM Engineering": {
        "titles": ["NLP Engineer", "LLM Engineer", "Generative AI Engineer"],
        "categories": ["programming_languages", "llm_ai", "machine_learning", "backend_frameworks"],
        "anchors": ["python", "llm", "rag", "transformers", "hugging face", "langchain", "vector database"],
        "soft": ["communication", "curiosity", "documentation", "collaboration"],
        "related": ["Data Science / ML Engineering", "Data Engineering / Analytics Engineering", "Software Architecture / Technical Leadership"],
    },
    "Data Engineering / Analytics Engineering": {
        "titles": ["Data Engineer", "Analytics Engineer", "ETL Developer"],
        "categories": ["programming_languages", "data_engineering", "databases_sql", "cloud_aws", "cloud_gcp"],
        "anchors": ["apache spark", "airflow", "dbt", "snowflake", "bigquery", "etl", "sql"],
        "soft": ["organization", "communication", "ownership", "systems thinking"],
        "related": ["Data Science / ML Engineering", "BI / Analytics / Visualization", "DevOps / Cloud Engineering"],
    },
    "BI / Analytics / Visualization": {
        "titles": ["BI Developer", "Product Analyst", "Analytics Specialist"],
        "categories": ["analytics_bi", "databases_sql", "data_engineering", "collaboration_tools"],
        "anchors": ["power bi", "tableau", "looker", "dashboards", "cohort analysis", "retention analysis"],
        "soft": ["storytelling", "communication", "customer focus", "presentation"],
        "related": ["Data Engineering / Analytics Engineering", "Data Science / ML Engineering", "ERP / CRM / Enterprise Apps"],
    },
    "Full Stack Web Development": {
        "titles": ["Full Stack Developer", "Product Engineer", "Software Engineer"],
        "categories": ["frontend_frameworks", "backend_frameworks", "databases_sql", "api_integration", "devops_ci_cd"],
        "anchors": ["react", "next.js", "node.js", "typescript", "postgresql", "rest api", "docker"],
        "soft": ["teamwork", "communication", "adaptability", "ownership"],
        "related": ["Frontend Development", "Backend Development", "Software Architecture / Technical Leadership"],
    },
    "Frontend Development": {
        "titles": ["Frontend Engineer", "React Developer", "UI Engineer"],
        "categories": ["frontend_frameworks", "design_product", "qa_testing"],
        "anchors": ["react", "typescript", "tailwind css", "storybook", "accessibility", "figma"],
        "soft": ["creativity", "communication", "attention to detail", "teamwork"],
        "related": ["Full Stack Web Development", "Mobile Development", "Product / UX Engineering"],
    },
    "Backend Development": {
        "titles": ["Backend Engineer", "API Engineer", "Java Developer"],
        "categories": ["backend_frameworks", "databases_sql", "databases_nosql", "messaging_streaming", "architecture_patterns"],
        "anchors": ["fastapi", "spring boot", "nestjs", "postgresql", "redis", "grpc", "microservices"],
        "soft": ["ownership", "problem solving", "planning", "systems thinking"],
        "related": ["Full Stack Web Development", "Software Architecture / Technical Leadership", "DevOps / Cloud Engineering"],
    },
    "DevOps / Cloud Engineering": {
        "titles": ["DevOps Engineer", "Cloud Engineer", "Infrastructure Engineer"],
        "categories": ["cloud_aws", "cloud_azure", "cloud_gcp", "containers_platform", "devops_ci_cd", "infrastructure_as_code"],
        "anchors": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "github actions", "linux"],
        "soft": ["ownership", "resilience", "problem solving", "incident management"],
        "related": ["Platform / SRE / Observability", "Backend Development", "Cybersecurity / AppSec"],
    },
    "Platform / SRE / Observability": {
        "titles": ["Platform Engineer", "SRE", "Observability Engineer"],
        "categories": ["containers_platform", "devops_ci_cd", "observability", "infrastructure_as_code", "operating_systems"],
        "anchors": ["platform engineering", "sre", "prometheus", "grafana", "opentelemetry", "argocd", "helm"],
        "soft": ["communication", "systems thinking", "resilience", "ownership"],
        "related": ["DevOps / Cloud Engineering", "Software Architecture / Technical Leadership", "Cybersecurity / AppSec"],
    },
    "Cybersecurity / AppSec": {
        "titles": ["Security Engineer", "Application Security Engineer", "SOC Analyst"],
        "categories": ["security_appsec", "security_offsec", "security_governance", "networking", "containers_platform"],
        "anchors": ["owasp", "iam", "sast", "dast", "penetration testing", "siem", "incident response"],
        "soft": ["attention to detail", "critical thinking", "communication", "risk management"],
        "related": ["DevOps / Cloud Engineering", "Platform / SRE / Observability", "Networking / Systems Administration"],
    },
    "Mobile Development": {
        "titles": ["Mobile Engineer", "Android Developer", "iOS Developer"],
        "categories": ["mobile_frameworks", "frontend_frameworks", "backend_frameworks"],
        "anchors": ["android", "ios", "kotlin", "swift", "react native", "flutter", "jetpack compose"],
        "soft": ["creativity", "teamwork", "communication", "quality mindset"],
        "related": ["Frontend Development", "Full Stack Web Development", "Game Development / AR / VR"],
    },
    "QA / Test Automation": {
        "titles": ["QA Automation Engineer", "SDET", "Test Engineer"],
        "categories": ["qa_testing", "backend_frameworks", "frontend_frameworks", "devops_ci_cd"],
        "anchors": ["pytest", "playwright", "cypress", "selenium", "k6", "contract testing", "testcontainers"],
        "soft": ["quality mindset", "communication", "attention to detail", "organization"],
        "related": ["Frontend Development", "Backend Development", "Platform / SRE / Observability"],
    },
    "Blockchain / Web3": {
        "titles": ["Blockchain Engineer", "Smart Contract Developer", "Web3 Engineer"],
        "categories": ["blockchain_web3", "programming_languages", "backend_frameworks", "security_appsec"],
        "anchors": ["blockchain", "web3", "ethereum", "solidity", "smart contracts", "hardhat", "foundry"],
        "soft": ["curiosity", "problem solving", "ownership", "research"],
        "related": ["Backend Development", "Cybersecurity / AppSec", "Game Development / AR / VR"],
    },
    "Embedded / IoT / Robotics": {
        "titles": ["Embedded Engineer", "IoT Engineer", "Firmware Engineer"],
        "categories": ["embedded_iot", "robotics_industrial", "programming_languages", "operating_systems"],
        "anchors": ["embedded c", "rtos", "arm", "stm32", "firmware", "iot", "ros2", "sensor fusion"],
        "soft": ["problem solving", "attention to detail", "systems thinking", "documentation"],
        "related": ["Networking / Systems Administration", "Game Development / AR / VR", "Cybersecurity / AppSec"],
    },
    "Game Development / AR / VR": {
        "titles": ["Game Developer", "Graphics Engineer", "AR/VR Engineer"],
        "categories": ["game_ar_vr", "programming_languages", "design_product", "mobile_frameworks"],
        "anchors": ["unity", "unreal engine", "godot", "shader programming", "ar/vr", "spatial computing"],
        "soft": ["creativity", "teamwork", "problem solving", "innovation"],
        "related": ["Frontend Development", "Mobile Development", "Embedded / IoT / Robotics"],
    },
    "ERP / CRM / Enterprise Apps": {
        "titles": ["Salesforce Developer", "CRM Engineer", "ERP Consultant"],
        "categories": ["erp_crm", "backend_frameworks", "api_integration", "analytics_bi", "collaboration_tools"],
        "anchors": ["salesforce", "servicenow", "sap", "workday", "microsoft dynamics", "power platform"],
        "soft": ["stakeholder management", "communication", "consulting", "organization"],
        "related": ["BI / Analytics / Visualization", "Software Architecture / Technical Leadership", "Backend Development"],
    },
    "Networking / Systems Administration": {
        "titles": ["Systems Administrator", "Network Engineer", "IT Operations Engineer"],
        "categories": ["networking", "operating_systems", "security_governance", "devops_ci_cd"],
        "anchors": ["linux", "windows server", "tcp/ip", "dns", "load balancer", "cisco", "vpn", "ssh"],
        "soft": ["incident management", "communication", "organization", "adaptability"],
        "related": ["Cybersecurity / AppSec", "DevOps / Cloud Engineering", "Platform / SRE / Observability"],
    },
    "Product / UX Engineering": {
        "titles": ["UX Engineer", "Design Technologist", "Product Designer"],
        "categories": ["design_product", "frontend_frameworks", "analytics_bi", "collaboration_tools"],
        "anchors": ["figma", "design systems", "accessibility", "prototyping", "wireframing", "storybook"],
        "soft": ["creativity", "communication", "customer focus", "facilitation"],
        "related": ["Frontend Development", "Full Stack Web Development", "BI / Analytics / Visualization"],
    },
    "Software Architecture / Technical Leadership": {
        "titles": ["Software Architect", "Solutions Architect", "Technical Lead"],
        "categories": ["architecture_patterns", "backend_frameworks", "containers_platform", "observability", "api_integration"],
        "anchors": ["software architecture", "system design", "domain-driven design", "event-driven architecture", "distributed systems", "microservices", "caching"],
        "soft": ["leadership", "stakeholder management", "mentoring", "strategic thinking"],
        "related": ["Backend Development", "Platform / SRE / Observability", "DevOps / Cloud Engineering"],
    },
}

OBSOLETE_SKILLS = [
    "adobe flash", "silverlight", "jquery mobile", "soap ui", "actionscript", "apache struts", "svn",
    "classic asp", "visual basic 6", "webforms", "dreamweaver", "coldfusion", "lotus notes"
]

INDUSTRIES = [
    "fintech", "healthtech", "e-commerce", "edtech", "cyberdefense", "telecom", "logistics", "retail",
    "gaming", "public sector", "energy", "manufacturing", "banking", "insurance", "media", "travel", "saas"
]

COMPANY_CONTEXTS = [
    "startup en hypercroissance", "scale-up internationale", "grand groupe", "cabinet de conseil", "editeur SaaS",
    "organisation regulee", "equipe produit distribuee", "plateforme cloud"
]

LOCATIONS = ["Paris", "Lyon", "Toulouse", "Nantes", "Bruxelles", "Montreal", "Dakar", "Casablanca", "Remote"]

SPECIAL_CASE_RATIOS = {
    "cross_lingual": 0.06,
    "typos": 0.08,
    "obsolete": 0.04,
    "contradictory_offer": 0.05,
    "abbreviated_cv": 0.12,
    "hybrid_profile": 0.10,
    "cert_heavy": 0.10,
}


def dedupe(items: Iterable[str]) -> List[str]:
    seen = {}
    for item in items:
        value = str(item).strip()
        if value:
            seen[value.lower()] = value
    return list(seen.values())


def load_dictionary(refresh: bool = False) -> Dict[str, object]:
    if refresh or not SKILLS_PATH.exists():
        write_skills_dictionary(SKILLS_PATH)
    return json.loads(SKILLS_PATH.read_text(encoding="utf-8"))


def build_domain_profiles(skills_dictionary: Dict[str, object]) -> Dict[str, Dict[str, List[str]]]:
    profiles = {}
    for domain_name, blueprint in DOMAIN_BLUEPRINTS.items():
        hard = []
        for category in blueprint["categories"]:
            hard.extend(skills_dictionary["hard_skills"].get(category, []))
        hard.extend(blueprint["anchors"])
        soft = dedupe(list(blueprint["soft"]) + skills_dictionary["soft_skills"][:18])
        certifications = dedupe(list(blueprint.get("certifications", [])) + skills_dictionary["certifications"][:25])
        profiles[domain_name] = {
            "titles": list(blueprint["titles"]),
            "hard": dedupe(hard),
            "soft": soft,
            "related": list(blueprint["related"]),
            "certifications": certifications,
        }
    return profiles


def pick_raw_label(rng: random.Random) -> float:
    return rng.choices(population=[1.0, 0.5, 0.0], weights=[40, 30, 30], k=1)[0]


def sample_seniority(rng: random.Random) -> Tuple[str, int]:
    seniority = rng.choices(population=["junior", "mid", "senior", "lead"], weights=[0.24, 0.36, 0.26, 0.14], k=1)[0]
    years = {"junior": rng.randint(0, 2), "mid": rng.randint(3, 5), "senior": rng.randint(6, 10), "lead": rng.randint(10, 18)}[seniority]
    return seniority, years


def make_flag_set(rng: random.Random) -> Set[str]:
    return {flag for flag, ratio in SPECIAL_CASE_RATIOS.items() if rng.random() < ratio}


def apply_typos(text: str, rng: random.Random) -> str:
    replacements = {
        "python": "pyhton",
        "kubernetes": "kubernets",
        "architecture": "architechture",
        "experience": "experiance",
        "development": "developpment",
        "engineering": "enginering",
        "security": "secruity",
        "database": "databse",
    }
    output = text
    for source, target in replacements.items():
        if rng.random() < 0.35:
            output = output.replace(source, target).replace(source.title(), target.title())
    return output


def apply_abbreviations(text: str, aliases: Dict[str, str], rng: random.Random) -> str:
    inverse_aliases = {target: alias for alias, target in aliases.items() if len(alias) <= 6}
    output = text
    for target, alias in inverse_aliases.items():
        if rng.random() < 0.18:
            output = output.replace(target, alias).replace(target.title(), alias.upper())
    return output


def maybe_add_obsolete(skills: List[str], rng: random.Random) -> List[str]:
    return dedupe(skills + rng.sample(OBSOLETE_SKILLS, k=rng.randint(2, 4)))


def sample_profile(profile: Dict[str, List[str]], rng: random.Random, seniority: str, minimum: int = 8, maximum: int = 18) -> Tuple[List[str], List[str]]:
    bands = {"junior": (minimum, minimum + 3), "mid": (minimum + 2, maximum - 4), "senior": (minimum + 4, maximum - 1), "lead": (minimum + 5, maximum + 2)}
    low, high = bands[seniority]
    hard_count = min(len(profile["hard"]), rng.randint(low, max(low, high)))
    soft_count = min(len(profile["soft"]), {"junior": 4, "mid": 5, "senior": 6, "lead": 7}[seniority])
    return dedupe(rng.sample(profile["hard"], k=hard_count)), dedupe(rng.sample(profile["soft"], k=soft_count))


def blend_skills(cv_skills: List[str], job_skills: List[str], raw_label: float, rng: random.Random) -> List[str]:
    if raw_label == 1.0:
        overlap = max(5, int(len(cv_skills) * 0.75))
    elif raw_label == 0.5:
        overlap = max(4, int(len(cv_skills) * 0.45))
    else:
        overlap = 0

    shared = rng.sample(cv_skills, k=min(overlap, len(cv_skills))) if overlap else []
    remaining_needed = max(6, len(cv_skills) - overlap)
    other_skills = [skill for skill in job_skills if skill not in shared]
    extras = rng.sample(other_skills, k=min(remaining_needed, len(other_skills))) if other_skills else []
    return dedupe(shared + extras)


def render_cv_text(title: str, domain: str, seniority: str, years: int, skills: List[str], soft_skills: List[str], certifications: List[str], location: str, industry: str, cross_lingual: bool, style: str) -> str:
    skills_inline = ", ".join(skills[:12])
    soft_inline = ", ".join(soft_skills[:5])
    cert_inline = ", ".join(certifications[:3]) if certifications else "Aucune certification formelle"
    metric = f"amelioration des resultats de {10 + years}% a {18 + years}%"
    if cross_lingual:
        return (
            f"PROFILE\n{title} with {years} years of experience in {domain}, based in {location}.\n\n"
            f"EXPERIENCE\nWorked in {industry}. Main stack: {skills_inline}. Delivered {metric}.\n\n"
            f"SKILLS\n{skills_inline}\n\nSOFT SKILLS\n{soft_inline}\n\nCERTIFICATIONS\n{cert_inline}"
        )
    if style == "structured":
        return (
            f"PROFIL\n{title} {seniority} en {domain}, base a {location}, avec {years} ans d'experience.\n\n"
            f"EXPERIENCE\nMissions dans le secteur {industry}. Stack principale: {skills_inline}. Resultats: {metric}.\n\n"
            f"COMPETENCES\n{skills_inline}\n\nSOFT SKILLS\n{soft_inline}\n\nCERTIFICATIONS\n{cert_inline}"
        )
    if style == "compact":
        return f"{title} | {domain} | {years} ans | {location} | stack: {skills_inline} | soft: {soft_inline} | certs: {cert_inline}"
    return (
        f"Professionnel {title} avec {years} ans d'experience en {domain}. "
        f"J'ai travaille sur {skills_inline} dans des environnements {industry}. "
        f"J'apporte {soft_inline}. Certifications: {cert_inline}. Resultat cle: {metric}."
    )


def render_job_text(title: str, domain: str, seniority: str, required_skills: List[str], optional_skills: List[str], soft_skills: List[str], location: str, industry: str, company_context: str, contradictory: bool, cross_lingual: bool, style: str) -> str:
    required = ", ".join(required_skills[:10])
    optional = ", ".join(optional_skills[:6])
    if contradictory:
        optional = f"{optional}, cobol, adobe flash, blockchain, ar/vr"
    soft = ", ".join(soft_skills[:4])
    if cross_lingual:
        return (
            f"Nous recrutons un {title} en {domain}. Competences obligatoires: {required}. "
            f"Nice to have: {optional}. Le profil ideal demontre {soft}. Localisation: {location}."
        )
    if style == "enterprise":
        return (
            f"Grand compte recherche un {title} {seniority} pour une equipe {domain}. "
            f"Competences requises: {required}. Competences appreciees: {optional}. "
            f"Soft skills: {soft}. Contexte: {company_context}, secteur {industry}, localisation {location}."
        )
    if style == "startup":
        return (
            f"Startup recherche un {title}. Must have: {required}. Bonus: {optional}. "
            f"Le poste demande {soft}. Domaine: {domain}. Lieu: {location}."
        )
    return (
        f"Poste {title} {seniority} dans le secteur {industry}. Required: {required}. "
        f"Nice to have: {optional}. Soft skills attendues: {soft}. Contexte: {company_context}. Localisation: {location}."
    )


def build_row(index: int, rng: random.Random, profiles: Dict[str, Dict[str, List[str]]], skills_dictionary: Dict[str, object]) -> Dict[str, object]:
    raw_label = pick_raw_label(rng)
    flags = make_flag_set(rng)
    cv_domain = rng.choice(list(profiles))
    related_domains = profiles[cv_domain]["related"]
    if raw_label == 1.0:
        job_domain = rng.choice([cv_domain] + related_domains)
    elif raw_label == 0.5:
        job_domain = rng.choice(related_domains)
    else:
        unrelated = [domain for domain in profiles if domain != cv_domain and domain not in related_domains]
        job_domain = rng.choice(unrelated)

    seniority, years = sample_seniority(rng)
    cv_hard, cv_soft = sample_profile(profiles[cv_domain], rng, seniority)
    if "hybrid_profile" in flags:
        hybrid_domain = rng.choice(related_domains)
        cv_hard = dedupe(cv_hard + sample_profile(profiles[hybrid_domain], rng, seniority, minimum=3, maximum=7)[0])
    if "obsolete" in flags:
        cv_hard = maybe_add_obsolete(cv_hard, rng)

    job_hard = blend_skills(cv_hard, profiles[job_domain]["hard"], raw_label, rng)
    required_skills = rng.sample(job_hard, k=min(len(job_hard), {"junior": 6, "mid": 8, "senior": 10, "lead": 12}[seniority]))
    optional_skills = dedupe(job_hard[len(required_skills):] + rng.sample(profiles[job_domain]["hard"], k=min(4, len(profiles[job_domain]["hard"]))))
    job_soft = sample_profile({"hard": profiles[job_domain]["hard"], "soft": profiles[job_domain]["soft"]}, rng, seniority, minimum=3, maximum=6)[1]

    cert_upper = 3 if "cert_heavy" in flags else 2
    certifications = dedupe(rng.sample(profiles[cv_domain]["certifications"], k=min(rng.randint(0, cert_upper), len(profiles[cv_domain]["certifications"]))))
    cross_lingual = "cross_lingual" in flags
    cv_style = rng.choice(["structured", "narrative", "compact"])
    job_style = rng.choice(["technical", "enterprise", "startup"])
    title = rng.choice(profiles[cv_domain]["titles"])
    job_title = rng.choice(profiles[job_domain]["titles"])
    location = rng.choice(LOCATIONS)
    industry = rng.choice(INDUSTRIES)
    company_context = rng.choice(COMPANY_CONTEXTS)

    cv_text = render_cv_text(title, cv_domain, seniority, years, cv_hard, cv_soft, certifications, location, industry, cross_lingual, cv_style)
    job_text = render_job_text(job_title, job_domain, seniority, required_skills, optional_skills, job_soft, location, industry, company_context, "contradictory_offer" in flags, cross_lingual, job_style)

    if "abbreviated_cv" in flags:
        cv_text = apply_abbreviations(cv_text, skills_dictionary.get("aliases", {}), rng)
    if "typos" in flags:
        cv_text = apply_typos(cv_text, rng)

    difficulty = "easy"
    if raw_label == 0.5 or "contradictory_offer" in flags or "hybrid_profile" in flags:
        difficulty = "hard"
    elif raw_label == 0.0:
        difficulty = "medium"

    match_reason = {
        1.0: "alignement fort sur le domaine, la stack et le niveau d'experience",
        0.5: "profil transferable avec recouvrement partiel des competences et technologies connexes",
        0.0: "domaine different ou ecarts importants sur les competences critiques",
    }[raw_label]

    return {
        "id": index + 1,
        "cv_text": cv_text,
        "job_text": job_text,
        "label": 1 if raw_label >= 0.5 else 0,
        "score_raw": raw_label,
        "cv_hard_skills": json.dumps(dedupe(cv_hard), ensure_ascii=False),
        "cv_soft_skills": json.dumps(dedupe(cv_soft), ensure_ascii=False),
        "job_hard_skills": json.dumps(dedupe(job_hard), ensure_ascii=False),
        "job_soft_skills": json.dumps(dedupe(job_soft), ensure_ascii=False),
        "domain": job_domain,
        "seniority": seniority,
        "match_reason": match_reason,
        "difficulty": difficulty,
    }


def generate_dataset(output_path: Path = OUTPUT_PATH, size: int = DEFAULT_SIZE, seed: int = DEFAULT_SEED, refresh_skills: bool = False) -> pd.DataFrame:
    rng = random.Random(seed)
    skills_dictionary = load_dictionary(refresh=refresh_skills)
    profiles = build_domain_profiles(skills_dictionary)
    rows = [build_row(index, rng, profiles, skills_dictionary) for index in range(size)]
    dataframe = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_path, index=False)
    return dataframe


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a large and enriched synthetic CV/job matching dataset.")
    parser.add_argument("--size", type=int, default=DEFAULT_SIZE, help=f"Number of rows to generate. Default: {DEFAULT_SIZE}")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help=f"Random seed. Default: {DEFAULT_SEED}")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH, help=f"Output CSV path. Default: {OUTPUT_PATH}")
    parser.add_argument("--refresh-skills", action="store_true", help="Regenerate the skills dictionary before generating the CSV.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataframe = generate_dataset(output_path=args.output, size=args.size, seed=args.seed, refresh_skills=args.refresh_skills)
    print(f"total lignes: {len(dataframe)}")
    print(f"distribution labels: {dict(Counter(dataframe['score_raw']))}")
    print(f"distribution domaines: {dict(Counter(dataframe['domain']))}")


if __name__ == "__main__":
    main()
