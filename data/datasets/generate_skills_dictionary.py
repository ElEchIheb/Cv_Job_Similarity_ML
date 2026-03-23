from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List


OUTPUT_PATH = Path(__file__).resolve().parent / "skills_dictionary.json"


BASE_HARD_SKILLS: Dict[str, List[str]] = {
    "programming_languages": [
        "python", "java", "javascript", "typescript", "c", "c++", "c#", "go", "rust", "swift", "kotlin",
        "scala", "ruby", "php", "perl", "lua", "dart", "objective-c", "r", "matlab", "sas", "julia",
        "fortran", "cobol", "abap", "groovy", "powershell", "bash", "shell scripting", "elixir",
        "haskell", "clojure", "f#", "solidity", "move", "assembly", "visual basic", "vba", "delphi",
        "prolog", "smalltalk", "ocaml", "nim", "zig", "crystal", "apl", "scheme", "lisp", "pl/sql",
        "t-sql", "graphql", "sql", "mdx", "dax", "sml", "awk", "sed", "gml", "opencl"
    ],
    "frontend_frameworks": [
        "react", "next.js", "remix", "gatsby", "vite", "webpack", "babel", "rollup", "parcel", "vue.js",
        "nuxt.js", "angular", "svelte", "sveltekit", "astro", "solidjs", "qwik", "ember.js", "backbone.js",
        "jquery", "alpine.js", "lit", "preact", "redux", "zustand", "mobx", "recoil", "pinia", "react query",
        "tanstack query", "rxjs", "storybook", "tailwind css", "bootstrap", "bulma", "material ui", "chakra ui",
        "mantine", "ant design", "shadcn/ui", "radix ui", "styled-components", "emotion", "sass", "less",
        "css modules", "three.js", "d3.js", "chart.js", "echarts", "framer motion", "web components"
    ],
    "backend_frameworks": [
        "node.js", "express", "nestjs", "fastify", "koa", "hapi", "adonisjs", "django", "flask", "fastapi",
        "pyramid", "tornado", "spring boot", "spring cloud", "quarkus", "micronaut", "dropwizard", "ktor",
        "gin", "echo", "fiber", "beego", "actix", "axum", "rocket", "asp.net core", "blazor", "entity framework",
        "laravel", "symfony", "codeigniter", "cakephp", "rails", "sinatra", "phoenix", "hibernate", "mybatis",
        "vert.x", "play framework", "grpc", "graphql api", "rest api", "soap services", "signalr", "openapi",
        "swagger", "api gateway", "bff", "serverless framework", "azure functions", "aws lambda"
    ],
    "mobile_frameworks": [
        "android", "android sdk", "jetpack compose", "kotlin multiplatform", "ios", "ios sdk", "swiftui",
        "xcode", "react native", "flutter", "xamarin", "ionic", "cordova", "capacitor", "native script",
        "expo", "firebase analytics", "firebase crashlytics", "app store connect", "google play console",
        "mobile accessibility", "mobile ci", "bluetooth low energy", "arcore", "arkit", "mapkit", "core data",
        "room", "realm mobile", "healthkit", "watchos"
    ],
    "desktop_frameworks": [
        "electron", "tauri", "qt", "wxwidgets", "wpf", "winforms", "gtk", "swing", "javafx", "avalonia",
        "uwp", "maui", "cef", "pyqt", "pyside", "tkinter", "desktop automation", "desktop accessibility",
        "wix installer", "msix"
    ],
    "data_engineering": [
        "pandas", "numpy", "polars", "duckdb", "pyarrow", "apache spark", "pyspark", "dask", "ray",
        "apache hadoop", "hive", "presto", "trino", "airflow", "dbt", "prefect", "dagster", "kedro",
        "apache beam", "flink", "kafka streams", "ksql", "delta lake", "iceberg", "hudi", "databricks",
        "snowflake", "bigquery", "redshift", "synapse", "glue", "athena", "emr", "dataflow", "pub/sub",
        "event hub", "azure data factory", "ssis", "talend", "informatica", "mulesoft", "fivetran",
        "stitch", "hevodata", "matillion", "streamsets", "etl", "elt", "cdc", "feature store"
    ],
    "machine_learning": [
        "scikit-learn", "xgboost", "lightgbm", "catboost", "tensorflow", "keras", "pytorch", "jax", "onnx",
        "mlflow", "weights & biases", "comet ml", "optuna", "hyperopt", "ray tune", "deep learning",
        "machine learning", "reinforcement learning", "supervised learning", "unsupervised learning",
        "semi-supervised learning", "self-supervised learning", "active learning", "classification",
        "regression", "clustering", "forecasting", "time series", "recommendation systems", "anomaly detection",
        "computer vision", "nlp", "speech recognition", "feature engineering", "feature selection",
        "model evaluation", "cross validation", "ensemble learning", "bayesian optimization", "causal inference",
        "statistics", "hypothesis testing", "a/b testing", "experimentation", "survival analysis"
    ],
    "llm_ai": [
        "llm", "rag", "fine-tuning", "instruction tuning", "prompt engineering", "guardrails", "langchain",
        "langgraph", "llamaindex", "haystack", "semantic kernel", "crewai", "autogen", "openai api",
        "anthropic api", "transformers", "hugging face", "sentence-transformers", "tokenization",
        "embedding models", "vector database", "semantic search", "reranking", "model serving", "vllm",
        "text generation inference", "ollama", "lm studio", "openrouter", "function calling", "tool use",
        "agents", "prompt chaining", "evaluation harness", "ragas", "trulens", "deepeval", "peft", "lora",
        "qlora", "bitsandbytes", "gguf", "llama.cpp", "whisper", "tts", "multimodal ai", "vision-language models"
    ],
    "databases_sql": [
        "postgresql", "mysql", "mariadb", "sql server", "oracle database", "sqlite", "db2", "teradata",
        "cockroachdb", "timescaledb", "yugabytedb", "snowflake", "bigquery", "redshift", "greenplum",
        "sap hana", "trino", "presto", "duckdb", "clickhouse", "singleStore", "vertica", "firebird", "h2", "tidb"
    ],
    "databases_nosql": [
        "mongodb", "redis", "elasticsearch", "opensearch", "cassandra", "scylladb", "dynamodb", "cosmos db",
        "couchbase", "couchdb", "neo4j", "janusgraph", "influxdb", "questdb", "firebase", "fauna", "arangodb",
        "hbase", "memcached", "realm", "weaviate", "pinecone", "milvus", "qdrant", "chromadb"
    ],
    "cloud_aws": [
        "aws", "ec2", "s3", "rds", "lambda", "eks", "ecs", "fargate", "dynamodb", "redshift", "athena",
        "glue", "step functions", "cloudformation", "cloudwatch", "route 53", "api gateway", "iam", "kms",
        "sagemaker", "bedrock", "emr", "eventbridge", "sns", "sqs", "cognito", "waf", "guardduty", "efs", "elb"
    ],
    "cloud_azure": [
        "azure", "azure vm", "azure functions", "aks", "azure sql", "cosmos db", "blob storage", "event hub",
        "service bus", "data factory", "synapse", "azure devops", "entra id", "application insights", "log analytics",
        "bicep", "azure ml", "azure openai", "azure app service", "azure monitor", "key vault", "azure firewall",
        "front door", "azure policy", "azure arc", "azure container apps", "azure kubernetes service", "azure databricks"
    ],
    "cloud_gcp": [
        "gcp", "compute engine", "gke", "cloud run", "app engine", "bigquery", "cloud sql", "spanner",
        "pub/sub", "dataflow", "dataproc", "composer", "vertex ai", "cloud functions", "cloud storage",
        "cloud build", "artifact registry", "secret manager", "operations suite", "identity aware proxy",
        "firebase hosting", "cloud armor", "looker", "cloud logging", "memorystore", "alloydb"
    ],
    "containers_platform": [
        "docker", "docker compose", "kubernetes", "helm", "kustomize", "argocd", "flux", "istio", "linkerd",
        "consul", "nomad", "openshift", "rancher", "containerd", "podman", "buildah", "skaffold", "telepresence",
        "service mesh", "platform engineering", "internal developer platform", "backstage", "crossplane", "knative",
        "gateway api", "cilium", "calico", "falco", "grafana alloy", "opentelemetry collector"
    ],
    "devops_ci_cd": [
        "ci/cd", "jenkins", "gitlab ci", "github actions", "circleci", "travis ci", "teamcity", "bamboo",
        "tekton", "argo workflows", "bitbucket pipelines", "azure pipelines", "buildkite", "spinnaker", "drone ci",
        "linux", "ubuntu", "debian", "red hat", "centos", "alpine linux", "nginx", "apache", "traefik", "haproxy",
        "sre", "incident management", "runbooks", "postmortems", "release engineering", "blue green deployment",
        "canary release", "feature flags", "chaos engineering", "capacity planning", "load balancing"
    ],
    "infrastructure_as_code": [
        "terraform", "terragrunt", "ansible", "packer", "chef", "puppet", "saltstack", "vagrant", "pulumi",
        "cloudformation", "bicep", "arm templates", "cdk", "aws cdk", "serverless framework", "vault",
        "consul", "boundary", "nomad", "policy as code", "opa", "sentinel", "network as code", "gitops", "nix"
    ],
    "observability": [
        "prometheus", "grafana", "grafana loki", "grafana tempo", "mimir", "alertmanager", "opentelemetry",
        "jaeger", "zipkin", "datadog", "new relic", "dynatrace", "splunk", "elastic observability", "sentry",
        "rollbar", "bugsnag", "pagerduty", "opsgenie", "uptime monitoring", "apm", "distributed tracing",
        "metrics", "logging", "slis", "slos", "error budgets", "incident response", "root cause analysis", "profiling"
    ],
    "security_appsec": [
        "owasp", "secure coding", "sast", "dast", "sca", "dependency scanning", "secret scanning", "jwt", "oauth",
        "openid connect", "saml", "mfa", "sso", "iam", "rbac", "abac", "waf", "csrf", "xss", "sql injection",
        "threat modeling", "api security", "container security", "kubernetes security", "vault", "key management",
        "ssl/tls", "cryptography", "zero trust", "devsecops", "application security", "csp", "security headers"
    ],
    "security_offsec": [
        "penetration testing", "red team", "blue team", "purple team", "soc", "siem", "xdr", "edr", "ids", "ips",
        "incident response", "digital forensics", "malware analysis", "reverse engineering", "burp suite", "nmap",
        "metasploit", "wireshark", "nessus", "qualys", "osquery", "yara", "splunk enterprise security", "suricata",
        "snort", "kali linux", "security operations", "threat intelligence", "vulnerability management", "phishing analysis"
    ],
    "security_governance": [
        "iso 27001", "soc 2", "gdpr", "pci dss", "hipaa", "nist", "cis controls", "risk management",
        "security governance", "business continuity", "disaster recovery", "audit", "compliance", "governance",
        "identity governance", "data loss prevention", "endpoint protection", "mdm", "casb", "cloud security posture management"
    ],
    "networking": [
        "tcp/ip", "udp", "http/https", "http2", "http3", "dns", "dhcp", "ipv4", "ipv6", "bgp", "ospf", "mpls",
        "vpn", "sd-wan", "lan", "wan", "vlan", "subnetting", "load balancer", "reverse proxy", "cdn", "websocket",
        "grpc", "mqtt", "amqp", "smtp", "imap", "sftp", "ssh", "network automation", "cisco", "juniper", "fortinet"
    ],
    "qa_testing": [
        "pytest", "unittest", "nose", "jest", "vitest", "mocha", "chai", "ava", "cypress", "playwright", "selenium",
        "appium", "robot framework", "postman testing", "newman", "karate", "jmeter", "k6", "gatling", "locust",
        "contract testing", "consumer driven contracts", "pact", "integration testing", "unit testing", "e2e testing",
        "performance testing", "load testing", "soak testing", "accessibility testing", "testcontainers", "bdd", "tdd"
    ],
    "architecture_patterns": [
        "software architecture", "system design", "clean architecture", "hexagonal architecture", "onion architecture",
        "microservices", "modular monolith", "event-driven architecture", "cqrs", "event sourcing", "domain-driven design",
        "distributed systems", "high availability", "fault tolerance", "resilience", "scalability", "caching",
        "message queues", "pub/sub", "api design", "graphql federation", "service oriented architecture", "eda",
        "multitenancy", "backpressure", "rate limiting", "circuit breaker", "saga pattern", "outbox pattern", "solid"
    ],
    "messaging_streaming": [
        "apache kafka", "kafka connect", "kafka streams", "rabbitmq", "activemq", "nats", "redis streams", "pulsar",
        "azure service bus", "sns", "sqs", "google pub/sub", "eventbridge", "webhooks", "event mesh", "stream processing",
        "apache flink", "apache storm", "samza", "mqtt", "zeromq", "ibm mq", "message brokers", "queueing", "streaming etl"
    ],
    "api_integration": [
        "rest api", "graphql", "grpc", "websocket", "openapi", "swagger", "postman", "insomnia", "soap", "wsdl",
        "mulesoft", "boomi", "apigee", "kong", "tibco", "oracle integration cloud", "event api", "oauth scopes",
        "webhooks", "etl connectors", "edi", "message transformation", "api versioning", "api lifecycle management", "rate limiting"
    ],
    "analytics_bi": [
        "tableau", "power bi", "looker", "looker studio", "qlik", "superset", "metabase", "redash", "mode analytics",
        "thoughtspot", "data visualization", "dashboards", "kpis", "dax", "power query", "semantic layer", "cube",
        "metric layer", "customer analytics", "cohort analysis", "funnel analysis", "retention analysis", "attribution"
    ],
    "erp_crm": [
        "salesforce", "sales cloud", "service cloud", "marketing cloud", "hubspot", "microsoft dynamics", "sap",
        "sap hana", "oracle erp", "workday", "servicenow", "netsuite", "odoo", "crm", "erp", "cpq", "sharepoint",
        "power platform", "power apps", "power automate"
    ],
    "design_product": [
        "figma", "sketch", "adobe xd", "invision", "miro", "framer", "principle", "proto.io", "whimsical", "maze",
        "user research", "ux writing", "wireframing", "prototyping", "design systems", "accessibility", "wcag",
        "information architecture", "journey mapping", "interaction design"
    ],
    "embedded_iot": [
        "embedded c", "embedded linux", "rtos", "freeRTOS", "zephyr", "arm", "stm32", "arduino", "raspberry pi",
        "esp32", "microcontrollers", "firmware", "can bus", "modbus", "uart", "spi", "i2c", "hardware bring-up",
        "edge computing", "iot", "mqtt", "opc ua", "plc", "scada", "industrial iot"
    ],
    "blockchain_web3": [
        "blockchain", "web3", "ethereum", "solidity", "smart contracts", "hardhat", "foundry", "ethers.js",
        "web3.js", "polygon", "solana", "rust smart contracts", "anchor", "defi", "nfts", "cryptography",
        "consensus algorithms", "hyperledger", "chainlink", "wallet integration", "metamask", "subgraphs", "ipfs", "walletconnect"
    ],
    "game_ar_vr": [
        "unity", "unreal engine", "godot", "directx", "opengl", "vulkan", "shader programming", "c++ game dev",
        "game physics", "networked multiplayer", "rendering", "procedural generation", "animation systems", "game ai",
        "ar/vr", "mixed reality", "metaverse", "oculus sdk", "openxr", "spatial computing", "haptics", "motion capture", "ray tracing"
    ],
    "robotics_industrial": [
        "ros", "ros2", "gazebo", "moveit", "slam", "path planning", "opencv", "lidar", "sensor fusion",
        "control systems", "pid control", "industrial automation", "plc programming", "labview", "matlab simulink",
        "robotics", "computer vision robotics", "autonomous systems", "digital twin", "machine vision"
    ],
    "collaboration_tools": [
        "git", "github", "gitlab", "bitbucket", "jira", "confluence", "notion", "trello", "asana", "clickup",
        "linear", "slack", "microsoft teams", "google workspace", "zoom", "miro", "lucidchart", "draw.io",
        "obsidian", "airtable", "monday.com", "service desk", "zendesk", "freshdesk", "documentation"
    ],
    "operating_systems": [
        "linux", "ubuntu", "debian", "red hat", "centos", "fedora", "arch linux", "windows server", "windows",
        "macos", "unix", "freebsd", "openbsd", "android os", "ios", "shell", "terminal", "powershell", "zsh", "bash"
    ],
}


SOFT_SKILLS = [
    "communication", "written communication", "verbal communication", "teamwork", "collaboration", "leadership",
    "mentoring", "coaching", "stakeholder management", "problem solving", "critical thinking", "analytical thinking",
    "strategic thinking", "adaptability", "resilience", "creativity", "curiosity", "ownership", "autonomy",
    "organization", "time management", "prioritization", "decision making", "negotiation", "presentation",
    "customer focus", "attention to detail", "cross-functional collaboration", "conflict resolution", "empathy",
    "knowledge sharing", "documentation", "facilitation", "initiative", "learning agility", "planning",
    "project management", "product thinking", "business acumen", "solution design", "roadmapping", "accountability",
    "active listening", "public speaking", "remote collaboration", "agile", "scrum", "kanban", "design thinking",
    "change management", "quality mindset", "risk management", "incident management", "operational excellence",
    "research", "experimentation", "innovation", "execution", "influence", "relationship building", "self-management",
    "discipline", "patience", "decision ownership", "systems thinking", "service orientation", "adaptation",
    "cooperation", "feedback culture", "meeting facilitation", "storytelling", "consulting", "vendor management",
    "sales alignment", "hiring", "interviewing", "performance management", "vision setting", "team building"
]


CERTIFICATIONS = [
    "aws certified cloud practitioner", "aws certified developer", "aws certified solutions architect associate",
    "aws certified solutions architect professional", "aws certified devops engineer professional",
    "aws certified data engineer associate", "aws certified machine learning specialty", "aws certified security specialty",
    "azure fundamentals", "azure administrator associate", "azure developer associate", "azure data engineer associate",
    "azure ai engineer associate", "azure security engineer associate", "azure solutions architect expert",
    "google associate cloud engineer", "google professional cloud architect", "google professional data engineer",
    "google professional machine learning engineer", "google professional devops engineer", "google professional security engineer",
    "terraform associate", "vault associate", "kubernetes cka", "kubernetes ckad", "kubernetes cks",
    "docker certified associate", "red hat certified system administrator", "red hat certified engineer",
    "cisco ccna", "cisco ccnp", "comptia a+", "comptia network+", "comptia security+", "comptia linux+",
    "cissp", "ccsp", "ceh", "oscp", "gcih", "gcfa", "splunk core certified power user", "splunk enterprise certified admin",
    "itil foundation", "pmp", "prince2", "scrum master", "psm i", "psm ii", "pspo i", "safe agilist",
    "salesforce administrator", "salesforce platform developer i", "salesforce service cloud consultant",
    "databricks data engineer associate", "databricks data engineer professional", "databricks machine learning professional",
    "snowflake snowpro core", "oracle java se", "oracle cloud infrastructure architect associate",
    "microsoft power bi data analyst", "tableau desktop specialist", "tableau certified data analyst",
    "servicenow system administrator", "servicenow application developer", "sap certified development associate",
    "workday pro", "hubspot marketing software", "hubspot sales software", "lpic-1", "cka security", "cka platform engineer",
    "hashicorp terraform authoring", "isc2 sscp", "isc2 certified in cybersecurity", "cisa", "crisc", "cdpse",
    "certified scrum product owner", "professional agile leadership", "neo4j certified professional",
    "mongodb developer associate", "mongodb database administrator", "postgresql associate", "elastic certified engineer",
    "elastic certified observability engineer", "confluent certified developer for apache kafka", "dbt fundamentals",
    "astronomer airflow certification", "looker business analyst", "qlik sense business analyst", "adobe analytics certification",
    "gitlab certified associate", "github actions certification", "github advanced security certification",
    "ciw javascript specialist", "unity certified programmer", "unreal authorized instructor", "opc ua certified developer"
]


ALIASES = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "golang": "go",
    "node": "node.js",
    "nodejs": "node.js",
    "nextjs": "next.js",
    "nuxtjs": "nuxt.js",
    "vue": "vue.js",
    "postgres": "postgresql",
    "postgres sql": "postgresql",
    "ms sql": "sql server",
    "k8s": "kubernetes",
    "tf": "terraform",
    "gh actions": "github actions",
    "gitlab pipelines": "gitlab ci",
    "ci cd": "ci/cd",
    "ml": "machine learning",
    "dl": "deep learning",
    "cv": "computer vision",
    "nlu": "nlp",
    "genai": "generative ai",
    "llms": "llm",
    "rag pipeline": "rag",
    "hf": "hugging face",
    "sbert": "sentence-transformers",
    "pg": "postgresql",
    "mongo": "mongodb",
    "redis cache": "redis",
    "elastic": "elasticsearch",
    "aws eks": "eks",
    "aws ecs": "ecs",
    "azure aks": "aks",
    "google kubernetes engine": "gke",
    "tf serving": "model serving",
    "open telemetry": "opentelemetry",
    "oidc": "openid connect",
    "entra": "entra id",
    "adf": "azure data factory",
    "ad": "active directory",
    "ux": "user experience",
    "ui": "user interface",
    "qa": "quality assurance",
    "sre": "site reliability engineering",
    "soc": "security operations center",
    "appsec": "application security",
    "devsecops": "devsecops",
    "etl pipelines": "etl",
    "elt pipelines": "elt",
    "llama index": "llamaindex",
    "lang graph": "langgraph",
    "wx": "wxwidgets",
    "oid": "openid connect",
    "mfa auth": "mfa",
    "sso auth": "sso",
    "ssm": "aws systems manager",
    "gql": "graphql",
    "restful api": "rest api",
    "pgvector": "vector database",
    "vector db": "vector database",
    "ar vr": "ar/vr",
    "mixed-reality": "mixed reality",
    "ci": "continuous integration",
    "cd": "continuous delivery"
}


DOMAIN_KEYWORDS = {
    "data_science_ml": ["python", "pandas", "scikit-learn", "tensorflow", "pytorch", "machine learning", "mlflow", "feature engineering"],
    "ai_nlp": ["llm", "rag", "transformers", "hugging face", "langchain", "spacy", "vector database", "prompt engineering"],
    "data_engineering": ["apache spark", "airflow", "dbt", "snowflake", "bigquery", "etl", "apache beam", "databricks"],
    "frontend": ["react", "next.js", "vue.js", "angular", "tailwind css", "typescript", "storybook", "three.js"],
    "backend": ["fastapi", "spring boot", "nestjs", "django", "postgresql", "grpc", "rest api", "microservices"],
    "full_stack": ["react", "node.js", "typescript", "postgresql", "graphql", "docker", "rest api", "redis"],
    "devops_cloud": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "github actions", "prometheus"],
    "platform_sre": ["platform engineering", "sre", "argocd", "helm", "opentelemetry", "grafana", "incident response", "slos"],
    "cybersecurity": ["owasp", "siem", "penetration testing", "iam", "zero trust", "sast", "dast", "incident response"],
    "mobile": ["android", "ios", "kotlin", "swift", "react native", "flutter", "jetpack compose", "swiftui"],
    "qa_automation": ["pytest", "playwright", "cypress", "selenium", "k6", "jmeter", "contract testing", "testcontainers"],
    "blockchain_web3": ["blockchain", "web3", "ethereum", "solidity", "smart contracts", "hardhat", "foundry", "wallet integration"],
    "embedded_iot": ["embedded c", "rtos", "arm", "stm32", "arduino", "esp32", "iot", "firmware"],
    "game_ar_vr": ["unity", "unreal engine", "godot", "opengl", "vulkan", "shader programming", "ar/vr", "spatial computing"],
    "erp_crm": ["salesforce", "sap", "servicenow", "workday", "microsoft dynamics", "crm", "erp", "power platform"],
    "analytics_bi": ["power bi", "tableau", "looker", "qlik", "dashboards", "customer analytics", "retention analysis", "semantic layer"],
    "architecture": ["software architecture", "system design", "domain-driven design", "event-driven architecture", "distributed systems", "scalability", "caching", "saga pattern"]
}


def _dedupe(items: Iterable[str]) -> List[str]:
    seen = {}
    for item in items:
        normalized = item.strip()
        if normalized:
            seen[normalized.lower()] = normalized
    return sorted(seen.values(), key=lambda value: value.lower())


def build_skills_dictionary() -> Dict[str, object]:
    hard_skills = {category: _dedupe(values) for category, values in BASE_HARD_SKILLS.items()}
    soft_skills = _dedupe(SOFT_SKILLS)
    certifications = _dedupe(CERTIFICATIONS)
    aliases = {alias.lower(): target for alias, target in sorted(ALIASES.items())}
    return {
        "hard_skills": hard_skills,
        "soft_skills": soft_skills,
        "certifications": certifications,
        "aliases": aliases,
        "domain_keywords": DOMAIN_KEYWORDS,
        "metadata": {
            "hard_skill_categories": len(hard_skills),
            "hard_skill_total": sum(len(values) for values in hard_skills.values()),
            "soft_skill_total": len(soft_skills),
            "certification_total": len(certifications),
        },
    }


def write_skills_dictionary(output_path: Path = OUTPUT_PATH) -> Dict[str, object]:
    payload = build_skills_dictionary()
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def main() -> None:
    payload = write_skills_dictionary()
    metadata = payload["metadata"]
    print(f"hard categories: {metadata['hard_skill_categories']}")
    print(f"hard skills total: {metadata['hard_skill_total']}")
    print(f"soft skills total: {metadata['soft_skill_total']}")
    print(f"certifications total: {metadata['certification_total']}")


if __name__ == "__main__":
    main()
