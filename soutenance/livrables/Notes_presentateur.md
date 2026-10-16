# JobTest — Soutenance PFE 2025/2026 · Notes de présentateur

Iheb El Ech · Mastère Professionnel Applications Web Intelligentes · ISI Kef — Université de Jendouba · CyberCloud Solutions

Ces notes sont aussi enregistrées dans le design Canva (panneau « Notes » de chaque slide). Compter 20 à 30 secondes par note.

## Slide 1 — Page de titre

Bonjour, mesdames et messieurs les membres du jury. Je m'appelle Iheb El Ech et je vous présente mon projet de fin d'études, réalisé au sein de CyberCloud Solutions pour l'obtention du Mastère Professionnel en Applications Web Intelligentes. Le projet s'intitule : conception et développement d'une plateforme intelligente d'aide au recrutement et de mise en correspondance entre CV et offres d'emploi. Le produit s'appelle JobTest. Ce travail a été encadré par le Dr Aymen Louati à l'ISI du Kef et par la Dr Emna Trabelsi côté entreprise, que je remercie tous les deux.

## Slide 2 — Sommaire

La présentation suit six parties, puis une conclusion. Je commence par le contexte et la problématique, puis la méthodologie retenue. Je détaille ensuite les besoins et la conception UML. La cinquième partie est le cœur du travail : le moteur intelligent et son évaluation. Je termine par la réalisation, une démonstration, les tests, la sécurité et le déploiement sur Azure.

## Slide 3 — Introduction

Le point de départ est simple : un recruteur reçoit des CV dans des formats très différents, PDF, Word ou texte brut, et doit les confronter à des offres rédigées en langage libre. Cette première lecture prend du temps et reste difficile à justifier après coup. JobTest fusionne trois signaux pour proposer une évaluation, mais aucune décision d'embauche n'est automatisée. Toute la plateforme est construite autour de cette phrase : assister le recruteur, pas le remplacer.

## Slide 4 — CyberCloud Solutions

CyberCloud Solutions est une entreprise de services et de conseil en informatique, fondée en 2017 et située dans le Grand Tunis, avec un effectif de deux à dix personnes. Ses activités couvrent le conseil et la transformation numérique, l'infrastructure, la sécurité Internet et le network forensics, ainsi que la cybersécurité, le cloud et le DevOps. Mon stage est un PFE individuel, mené de mars à août 2026 en mode distant et hybride. Le sujet a été proposé par l'entreprise.

## Slide 5 — Étude de l'existant

J'ai étudié deux approches existantes. La première est le processus manuel : lire l'offre, définir des critères, ouvrir les CV un par un, repérer les compétences, puis garder ou écarter. Il est coûteux à répéter, peu traçable et sensible aux formats disparates. La seconde regroupe les ATS et la recherche lexicale par mots-clés et filtres. Elle ignore les paraphrases, gère mal les CV multilingues et échoue dès que le vocabulaire du candidat n'est pas exactement celui de l'offre.

## Slide 6 — Benchmark des solutions

J'ai comparé trois solutions du marché à partir de leur documentation officielle, consultée le 13 septembre 2026 : LinkedIn Recruiter, Workable et Greenhouse. Elles proposent toutes une forme de correspondance assistée par IA, mais la décomposition du score et l'analyse des écarts de compétences ne sont pas documentées. Attention : « non documenté » signifie que je n'ai trouvé aucune preuve dans les pages officielles, pas que la fonction n'existe pas. JobTest se positionne sur un périmètre plus étroit mais transparent : sous-scores, écarts, recommandations, historique et rapport PDF, avec des données cloisonnées par recruteur.

## Slide 7 — Critique de l'existant

La critique de l'existant ne porte pas sur l'absence d'une brique, mais sur leur articulation. On trouve des outils qui analysent le texte, d'autres qui appliquent une règle de décision, d'autres qui affichent une explication. Ce qui manque, c'est la cohérence entre les trois : que l'explication affichée soit bien celle du score calculé, et que la décision découle d'une règle visible. C'est précisément ce que JobTest cherche à garantir.

## Slide 8 — Problématique

D'où la problématique : comment fournir au recruteur une évaluation CV/offre à la fois hybride, explicable, reproductible et persistante, sans lui déléguer la décision d'embauche ? Hybride, parce que le contenu est hétérogène et qu'un seul signal ne suffit pas. Explicable, parce que le résultat doit être vérifiable par ses composantes. Reproductible, parce que le même dossier doit donner le même score. Et le génératif doit rester encadré : il commente, il ne décide pas.

## Slide 9 — Solution proposée : JobTest

JobTest prend en entrée un CV, en texte, PDF ou DOCX, et une offre d'emploi. Le moteur hybride combine trois signaux : TF-IDF, embeddings et compétences. Il produit un score global en pourcentage, un verdict HIRE, CONSIDER ou REJECT, la liste des compétences trouvées et manquantes, et des recommandations. Autour de ce flux central, la plateforme offre l'historique, le classement de plusieurs CV, le rapport PDF, la comparaison des méthodes dans AI Insights et le suivi du benchmark dans l'AI Quality Center.

## Slide 10 — Objectifs du projet

Le projet poursuit huit objectifs spécifiques. Offrir un workflow complet au recruteur, accepter un CV en texte ou en fichier, fusionner trois signaux, et produire une décision cohérente avec le score. Le résultat doit être explicable, l'historique persistant, et la plateforme doit fournir un rapport et un classement. Enfin, le déploiement doit être démontrable : la plateforme tourne réellement sur une machine Azure accessible en ligne.

## Slide 11 — Modèle en cascade

J'ai retenu le modèle en cascade, en six phases : besoins, analyse, conception, implémentation, validation et correction, puis déploiement. Ce choix convient à un PFE dont les livrables peuvent être stabilisés et il donne un fil de lecture clair au mémoire. Royce lui-même, dans son article de 1970, insiste sur les retours contrôlés entre phases. J'assume donc des boucles de correction, notamment de la validation vers l'implémentation : cohérence de la décision, analyse des compétences, qualité du benchmark et sécurisation des accès.

## Slide 12 — Acteurs et parties prenantes

Le système a deux acteurs. Le visiteur non authentifié peut seulement créer un compte et se connecter. Le recruteur authentifié est l'acteur principal : il accède à toutes les fonctions métier. Point important : le candidat n'est jamais un utilisateur de la plateforme, c'est une entité métier, un dossier géré par le recruteur. La maintenance et la QA sont une partie prenante technique, en dehors du parcours fonctionnel.

## Slide 13 — Besoins fonctionnels

Les besoins fonctionnels se regroupent en six familles. L'authentification : inscription, connexion par JWT et déconnexion. Les offres : un CRUD complet, trois statuts et un code attribué automatiquement au format JOB-année-numéro. Les candidats : un pipeline de suivi, de NEW jusqu'à HIRED ou REJECTED. L'évaluation, à partir d'un texte ou d'un fichier, avec un verdict explicable. Les compléments : analyse approfondie, rapport PDF, classement et export CSV. Et le pilotage : historique, AI Insights, Quality Center et réglage des seuils.

## Slide 14 — Besoins non fonctionnels

Les besoins non fonctionnels sont structurés selon la norme ISO/IEC 25010. La sécurité repose sur le JWT et le contrôle d'appartenance ; la confidentialité, sur le cloisonnement par recruteur. L'explicabilité impose la même politique de décision dans toute l'application, et la reproductibilité impose d'enregistrer poids et seuils avec chaque résultat. Côté performance, la couche 2 n'est jamais bloquante : elle prend environ 54 secondes sur CPU, mais le score est déjà affiché. La fiabilité signifie qu'une panne d'Ollama n'est pas un échec de l'évaluation. Enfin, l'interface est responsive et le tout est portable grâce à Docker Compose.

## Slide 15 — Règles de gestion

Dix règles de gestion encadrent le comportement. Un recruteur ne voit que ses données. Une offre ou un candidat déjà évalué ne peut plus être supprimé, pour préserver l'historique. La décision suit les seuils actifs, et le seuil Potential Fit reste toujours inférieur au seuil Strong Fit. La règle la plus importante est la RG-06 : la couche LLM ne modifie jamais le score ni le verdict. AI Insights ne persiste rien, l'analyse approfondie n'est enregistrée que si son état est ok, et les fichiers acceptés sont des PDF ou DOCX contenant du texte lisible.

## Slide 16 — Diagramme global des cas d'utilisation

Voici le diagramme global des cas d'utilisation. À gauche, le visiteur peut créer un compte et s'authentifier. À droite, le recruteur accède aux huit cas métier : tableau de bord, offres, candidats, évaluation, consultation des résultats, analyse approfondie, exploitation des résultats et configuration. Deux relations sont à retenir. Évaluer un CV inclut la consultation des résultats explicables. Et l'analyse approfondie est une extension : elle est optionnelle et vient après le résultat.

## Slide 17 — Cas d'utilisation raffinés

J'ai raffiné huit cas d'utilisation, de UC-01 à UC-08. Le cas central est UC-04, évaluer un CV : le recruteur choisit une offre, fournit un texte ou un fichier, et le verdict est persisté. UC-05, l'analyse approfondie, est une extension : le contexte est reconstruit depuis le résultat, Ollama est appelé en local, et l'analyse n'est enregistrée que si elle est valide. Le rapport PDF ne recalcule rien. Le classement multi-CV réutilise le même flux d'évaluation, fichier par fichier, puis trie par score.

## Slide 18 — Diagramme de classes

Le diagramme de classes présente le modèle métier. User est la classe parente, spécialisée en Candidate et Recruiter. Un recruteur publie zéro ou plusieurs offres ; une offre reçoit des candidatures ; chaque candidature a au plus un résultat de matching. Les compétences sont reliées aux candidats et aux offres par des associations plusieurs-à-plusieurs. Un choix de conception à signaler : l'analyse du LLM est stockée dans un champ JSON du MatchResult, sans table dédiée, ce qui garde le résultat et son commentaire ensemble.

## Slide 19 — Séquence : évaluation d'un CV

Voici le flux central. Le recruteur lance l'évaluation, Next.js appelle l'API FastAPI sur POST /ui/evaluate. L'API valide le CV et vérifie que l'offre appartient bien au recruteur. Le service d'évaluation sollicite la couche 1 : TF-IDF, embeddings et compétences, agrégés avec les poids 0,2, 0,4 et 0,4. La décision et l'explication sont produites, puis le résultat est persisté dans PostgreSQL avant d'être renvoyé. L'interface affiche donc toujours un résultat déjà enregistré.

## Slide 20 — Séquences : analyse approfondie + rapport PDF

À gauche, l'analyse approfondie. L'API relit le MatchResult, construit un contexte structuré et appelle Ollama. Si la réponse est valide, elle est persistée ; sinon l'API renvoie un état contrôlé : disabled, unavailable, error ou inconsistent. Dans tous les cas, le score et le verdict restent inchangés. À droite, le rapport PDF : l'interface transmet le résultat existant, ReportLab génère le document et le navigateur le télécharge. Aucun score n'est recalculé.

## Slide 21 — Architecture logique

L'architecture logique repose sur un seul point d'entrée. Le navigateur parle en HTTP à Nginx, seul service exposé, sur le port 80. Nginx relaie la racine vers Next.js et le préfixe /api/v1 vers FastAPI. FastAPI s'appuie sur la couche 1, sur PostgreSQL et sur Ollama. Les ports 3000, 8000, 5432 et 11434 ne sont pas publiés à l'extérieur du réseau Docker. À droite, les modules du code : chacun a une responsabilité unique, de l'interface jusqu'à l'ORM.

## Slide 22 — Pipeline de rapprochement

J'arrive au cœur du projet. Le pipeline compte cinq étapes : réception du CV et de l'offre, extraction et segmentation en sections, calcul des trois signaux, fusion pondérée, puis décision. C'est une fusion tardive : chaque composant conserve son score avant l'agrégation, ce qui permet de l'afficher et de l'expliquer. La couche 2, en pointillés, est optionnelle : elle est additive et non décisionnelle. L'extraction utilise pdfplumber avec un repli sur PyPDF2, et python-docx pour les fichiers Word.

## Slide 23 — Les 3 composantes du score

Le premier signal est lexical : TF-IDF avec des n-grammes de 1 à 3, au plus 10 000 caractéristiques, et une similarité cosinus. Il est lisible mais sensible aux synonymes. Le deuxième est sémantique : deux modèles Sentence-Transformers, un anglais et un multilingue, dont les similarités sont moyennées, complétées par une similarité par sections où l'expérience pèse 0,40 et les compétences 0,30. Le troisième exploite un dictionnaire de compétences versionné : 70 % pour les compétences techniques, 30 % pour les comportementales, avec un bonus de domaine, un bonus de certifications plafonné, et une pénalité pouvant atteindre 0,20 pour les compétences critiques absentes. C'est ce troisième signal qui fournit la justification métier.

## Slide 24 — Fusion hybride & décision

Le score hybride vaut 0,2 fois le score TF-IDF, plus 0,4 fois le score sémantique, plus 0,4 fois le score de compétences. Ces poids sont fixés, ils ne sont pas appris : ils donnent le même poids au sens et aux compétences explicites. Par exemple, des sous-scores de 0,60, 0,70 et 0,80 donnent 72 %. Le moteur de décision applique ensuite trois bandes : à partir de 75 %, HIRE ; de 55 à 75, CONSIDER ; en dessous de 55, REJECT. Ces seuils sont réglables par le recruteur et enregistrés avec chaque résultat. La confiance affichée est une distance au seuil le plus proche, pas une probabilité d'embauche.

## Slide 25 — Couche 2 : analyse locale encadrée

La couche 2 est séparée de la couche 1 par un mur : c'est la règle RG-06. Le modèle local qwen2.5:1.5b, exécuté par Ollama, reçoit le verdict comme une donnée à commenter et produit cinq blocs : trajectoire, alertes, justification, recommandations et questions d'entretien. Trois garde-fous l'encadrent. Le format est imposé, sans aucun champ de score : une réponse non conforme est rejetée. Un contrôle de cohérence détecte un texte trop favorable sur un dossier REJECT, relance une fois le modèle, puis retourne l'état inconsistent. Enfin, le score est calculé avant tout appel au modèle : une injection de prompt cachée dans un CV ne peut toucher que le commentaire, jamais le verdict.

## Slide 26 — Protocole expérimental

L'évaluation utilise un jeu de données généré localement, cv_job_dataset.csv, avec la graine 42 : 12 000 paires CV-offre, 20 domaines métier, en français et en anglais. Le générateur dégrade volontairement les documents : abréviations, fautes de frappe, technologies obsolètes, et des paires contradictoires où le vocabulaire se recoupe sans que le profil corresponde. La partition est stratifiée : 8 400 paires pour l'apprentissage, 1 800 pour la validation, 1 800 pour le test. Pourquoi un corpus synthétique ? Aucun corpus réel n'était accessible, un CV réel est une donnée personnelle, l'extraction devait être maîtrisée, il n'existe pas de vérité terrain fiable, et la graine fixée rend l'expérience reproductible.

## Slide 27 — Résultats comparatifs

Sur les 1 800 paires de test, la fusion hybride atteint un F1 de 0,93 et une AUC de 0,96. TF-IDF obtient le meilleur F1, 0,95. Je ne présente pas cela comme une supériorité du lexical : le générateur construit les CV et les offres à partir d'un vocabulaire contrôlé et partagé, ce qui favorise mécaniquement le recouvrement de termes. La fusion est retenue parce qu'elle associe ce signal à la sémantique et à une justification par compétences. Elle est aussi plus rapide dans la mesure effectuée : environ 56 millisecondes par paire, contre 922 pour les embeddings seuls. Les seuils du tableau sont des points de fonctionnement expérimentaux, pas les seuils du produit.

## Slide 28 — Honnêteté scientifique : deux corrections

Deux défauts ont été découverts puis corrigés pendant le projet, et je préfère les montrer. Le premier concerne les poids : le modèle en service portait 0,9, 0,0 et 0,1, hérités d'une recherche sur grille. Avec un poids nul sur la sémantique, deux CV aux compétences identiques obtenaient 99,2 % et 73,6 % selon leur formulation : 25,6 points d'écart, donc une faille exploitable en recopiant l'annonce. Avec les poids documentés, l'écart tombe à 9,6 points. Le second défaut concerne le protocole : un seuil unique de 0,60 donnait à TF-IDF un F1 nul alors que son AUC était de 0,979. Avec un seuil calibré par méthode sur la validation, le F1 passe à 0,950. Une alerte automatique empêche désormais que ce cas se reproduise en silence.

## Slide 29 — Stack technique

La pile technique est la suivante. Le frontend utilise Next.js 14 avec l'App Router, React 18 et TypeScript ; le style repose sur Tailwind CSS, Framer Motion et Three.js pour les fonds animés. Le backend est en Python avec FastAPI, Uvicorn et Pydantic. La persistance passe par SQLAlchemy, avec SQLite en développement et PostgreSQL 16 dans l'environnement conteneurisé. L'intelligence artificielle s'appuie sur scikit-learn, Sentence-Transformers, spaCy et Ollama. Les documents sont traités avec pdfplumber, PyPDF2, python-docx et ReportLab, et l'infrastructure repose sur Docker Compose, Nginx et Microsoft Azure.

## Slide 30 — Architecture du projet

Le code est organisé par responsabilité. Le dossier web contient les pages Next.js, les composants et le client d'API. Côté serveur, src/api porte les routeurs FastAPI ; src/matching orchestre l'évaluation et la persistance ; src/models contient les trois modèles ; src/fusion calcule le score hybride ; src/decisioning applique les règles de verdict. Les explications, les prompts Ollama, l'extraction des documents et le rapport PDF ont chacun leur module. Cette séparation est ce qui permet de garantir qu'une seule politique de décision gouverne toute l'application.

## Slide 31 — Les interfaces

Voici les interfaces réelles de la plateforme, capturées sur l'instance déployée. L'écran de connexion, la vue d'ensemble avec les indicateurs, la gestion des offres, puis la page d'analyse d'un candidat. Le résultat affiche le score, le verdict et un radar de compétences ; l'analyse approfondie vient en dessous. Le Talent Leaderboard classe plusieurs CV avec un podium. On trouve enfin l'historique des analyses et les paramètres où le recruteur règle ses seuils. L'interface est responsive et a été vérifiée sur mobile.

## Slide 32 — Démonstration

Je vous propose maintenant une démonstration. Le parcours comporte six étapes : connexion, création d'une offre de Machine Learning Engineer, évaluation d'un CV au format PDF, lecture du résultat, analyse approfondie, puis export du rapport PDF. Dans l'enregistrement, le CV de démonstration obtient 82 % et le verdict Strong Fit, avec dix compétences requises sur dix. L'analyse locale se termine en une soixantaine de secondes sans modifier ce score. La plateforme est accessible en ligne à l'adresse affichée et via le QR code. Tous les CV utilisés dans la démonstration sont fictifs.

## Slide 33 — Tests & validation

Côté tests, je préfère être précis. La suite pytest donne 106 tests réussis sur 113, en 45 secondes environ. Les six échecs sont concentrés dans un seul fichier, test_api_extended.py : ses fixtures sont antérieures au contrôle d'appartenance et attendent un autre code que le 404 désormais renvoyé. Un test est ignoré. La suite n'est donc pas entièrement verte, et la maintenance est identifiée. En parallèle, huit contrôles de bout en bout ont été validés sur Azure, de l'inscription jusqu'au PDF de deux pages, avec cinq conteneurs à l'état healthy et Swagger accessible.

## Slide 34 — Sécurité & données personnelles

Pour la sécurité, voici ce qui est en place : mots de passe hachés avec bcrypt, JWT signé en HS256 avec expiration, contrôle d'appartenance sur chaque ressource, ORM sans SQL concaténé, limitation à 60 requêtes par minute et par IP, corps limité à 15 Mo, secrets hors du dépôt, et un NSG Azure qui n'ouvre que les ports 80 et 22. Surtout, le LLM s'exécute en local : aucun CV n'est envoyé à un tiers. Les limites sont assumées : HTTP sans TLS, jeton en localStorage, SSH à restreindre, pas de WAF ni de sauvegarde planifiée. Un usage sur de vraies candidatures relèverait de la loi tunisienne 2004-63 et de l'INPDP : consentement, finalité, droits d'accès. Ce sont des conditions d'entrée en service, pas des perspectives lointaines.

## Slide 35 — Déploiement Azure

Le déploiement comporte trois frontières emboîtées : la région Azure East US, une machine virtuelle Ubuntu 24.04 LTS, et le réseau Docker jobtest. Le trafic Internet traverse le NSG, arrive sur Nginx, puis est relayé vers Next.js ou FastAPI, qui accède à PostgreSQL et Ollama. La machine est une Standard D2as_v7 : 2 vCPU, 8 Gio de mémoire, avec 4 Gio de swap et un arrêt automatique vers 2 heures pour maîtriser les coûts. Cinq conteneurs tournent, et trois volumes conservent la base, les modèles Ollama et le cache des embeddings. Ce format suffit pour une démonstration, pas pour une charge réelle.

## Slide 36 — Apports du projet

Cinq apports se dégagent. Une chaîne complète, du CV jusqu'au verdict et au rapport. Un moteur hybride dont les trois signaux sont documentés et visibles. Une décision explicite et reproductible, grâce à des seuils enregistrés avec chaque résultat. Une séparation stricte entre le calcul déterministe et le contenu génératif : c'est, à mes yeux, le résultat le plus important. Et un déploiement conteneurisé démontré sur une machine Azure accessible en ligne.

## Slide 37 — Limites & perspectives

Les limites sont assumées : un corpus synthétique, une machine unique sans haute disponibilité, la latence CPU de la couche 2 et un dictionnaire de compétences forcément incomplet. À court terme, les priorités sont un domaine avec certificat TLS, des cookies sécurisés, la restriction de SSH, les sauvegardes PostgreSQL, le monitoring et la correction des tests hérités. À moyen terme, il faut confronter le moteur à un corpus réel anonymisé et autorisé, travailler avec des recruteurs, calibrer les seuils et tester les biais. À long terme : traitements asynchrones, observabilité, intégration avec des ATS et gouvernance des décisions assistées.

## Slide 38 — Merci

Pour conclure, JobTest est un prototype fonctionnel et traçable d'aide à l'analyse des candidatures. Il organise des signaux et des explications utiles au recruteur, sans prétendre remplacer son jugement ni sa responsabilité dans la décision finale. Je vous remercie pour votre attention et je suis à votre disposition pour répondre à vos questions. La plateforme reste accessible via le QR code si vous souhaitez la consulter.

---

# Questions probables du jury + réponses

### 1. Pourquoi un corpus synthétique et pas de vrais CV ?

Pour cinq raisons. Aucun corpus réel apparié CV-offre n'était accessible en quantité suffisante : quelques dizaines de dossiers ne permettent ni une partition en trois ensembles ni une mesure stable. Un CV réel est une donnée personnelle, soumise à la loi 2004-63. L'extraction de texte échoue partiellement sur de vrais CV, ce qui aurait mesuré la chaîne d'extraction plutôt que le rapprochement. Il n'existe pas de vérité terrain : une embauche dépend d'entretiens absents du dossier. Enfin, la graine 42 rend l'expérience reproductible. La contrepartie est assumée : ces chiffres mesurent la capacité de discrimination sur un matériau contrôlé, pas le comportement sur des CV réels.

### 2. Pourquoi TF-IDF obtient-il un meilleur F1 que l'hybride ?

Parce que le générateur construit CV et offres à partir d'un vocabulaire contrôlé et partagé, ce qui avantage mécaniquement le recouvrement de termes. Ce n'est pas une supériorité générale du lexical. L'écart est faible, 0,95 contre 0,93, et l'expérience de reformulation montre la faiblesse du lexical seul : 25,6 points d'écart entre deux CV aux compétences identiques. La fusion est retenue pour sa robustesse à la formulation et pour l'explication par compétences qu'elle apporte.

### 3. Pourquoi les poids 0,2 / 0,4 / 0,4 et pas d'autres ?

Ce sont des poids fixés et documentés, non appris. Ils donnent le même poids à la proximité sémantique et à la couverture explicite des compétences, et gardent une part lexicale minoritaire. Une recherche sur grille avait proposé 0,9 / 0,0 / 0,1 en maximisant l'AUC, mais ce réglage rendait le score très sensible à la formulation. Je les ai rétablis sans optimisation, précisément pour ne pas ajuster les poids sur les données qui servent à les juger. Ils restent empiriques et devront être calibrés sur des données réelles.

### 4. Le LLM peut-il changer la décision ?

Non, c'est la règle de gestion RG-06. Le score et le verdict sont calculés par la couche déterministe avant tout appel au modèle. Le format de réponse imposé ne contient aucun champ de score ni de verdict. Si le texte contredit un REJECT, le système relance une fois le modèle puis retourne l'état inconsistent et n'affiche rien. Même une injection de prompt dans un CV ne peut atteindre que le commentaire.

### 5. Que se passe-t-il si Ollama tombe ?

L'évaluation continue de fonctionner normalement. La couche 2 est appelée après l'affichage du résultat et n'est pas bloquante. L'API retourne un état contrôlé, unavailable, disabled ou error, que l'interface affiche avec un bouton pour réessayer. Rien n'est persisté dans ce cas, puisque l'analyse n'est enregistrée que si son état est ok.

### 6. Pourquoi le modèle en cascade et pas Agile ?

C'est un PFE individuel dont les livrables sont stabilisables : besoins, conception, réalisation, tests, déploiement. Travaillant seul, les rituels d'équipe d'une méthode agile apportaient peu. La cascade fournit un fil de lecture clair pour le mémoire. Je ne l'ai pas appliquée de façon rigide : des boucles de correction ont eu lieu entre validation et implémentation, comme Royce le prévoit dans son article de 1970.

### 7. Pourquoi 55 % et 75 % comme seuils ?

Ce sont des bornes de politique métier, pas des résultats du benchmark. Elles sont réglables par le recruteur dans les paramètres et enregistrées avec chaque évaluation. Sur le corpus synthétique, les scores sont compressés entre 0,12 et 0,61 : la borne HIRE n'y est jamais franchie, donc je ne peux pas prétendre qu'elles y sont validées. Leur calibration devra se faire sur la distribution des scores de candidatures réelles.

### 8. Comment gérez-vous les données personnelles ?

Dans ce projet, les évaluations portent sur des CV synthétiques ou fictifs. Techniquement, les données sont cloisonnées par recruteur avec un contrôle d'appartenance sur chaque ressource, et le LLM s'exécute en local : aucun CV n'est transmis à un service tiers. Un usage réel relèverait de la loi organique 2004-63 : consentement, finalité déterminée, droits d'accès, de rectification et de suppression, et démarches auprès de l'INPDP. Une politique de conservation et de suppression des CV reste à formaliser avant toute mise en service.

### 9. Pourquoi HTTP et pas HTTPS ?

Le démonstrateur est exposé sur une adresse IP publique, sans nom de domaine ni certificat TLS. C'est une limite que je documente et non un choix de conception : le jeton circule donc en clair. C'est la première action à court terme : associer un domaine, installer un certificat, puis passer le jeton dans des cookies HttpOnly, Secure et SameSite. Nginx étant déjà le point d'entrée unique, l'ajout du TLS ne modifie pas l'architecture.

### 10. Quelle est la différence entre le seuil 0,2636 du benchmark et les seuils produit ?

Ce sont deux lectures distinctes du même score. Le seuil 0,2636 est un instrument de mesure : c'est le point de fonctionnement qui maximise le F1 sur la validation, pour juger la qualité de discrimination du modèle. Les seuils 55 % et 75 % sont la politique de décision du produit, fixée indépendamment. Si on applique 0,55 au corpus synthétique, le rappel tombe à 0,02 parce que le corpus ne peuple pas le haut de l'échelle. Je présente donc les deux séparément, pour ne pas attribuer au produit une performance mesurée à un autre seuil.

### 11. Pourquoi un petit modèle local plutôt qu'une API de LLM en ligne ?

Pour la confidentialité et la maîtrise : un CV ne quitte jamais la machine, il n'y a ni coût par appel ni dépendance à un fournisseur. La contrepartie est la latence, environ une minute sur CPU, et une qualité de texte plus modeste. C'est acceptable parce que cette couche est optionnelle, non bloquante et strictement consultative.

### 12. Votre système peut-il introduire des biais ?

Oui, c'est un risque que je ne minimise pas. Les biais peuvent venir du dictionnaire de compétences, des modèles d'embeddings ou des règles. Le projet ne mesure pas l'équité entre groupes : c'est une perspective à moyen terme, avec des tests de biais par sous-groupes sur des données autorisées. En attendant, trois protections existent : la décision reste humaine, chaque score est décomposé et vérifiable, et les poids et seuils sont tracés avec chaque résultat.

---

# Emplacements d'images, logos et vidéo

| Slide | Élément |
|---|---|
| 1 | Champ « Soutenu le » : zone de texte éditable ajoutée dans Canva, à compléter avec la date. |
| 1 | Logos ISI Kef, Université de Jendouba, CyberCloud Solutions : déjà intégrés (fichiers du rapport). À remplacer seulement si vous avez des versions HD. |
| 31 | 10 captures réelles déjà placées (enregistrées le 06/10/2026 sur http://20.51.167.202/). Pour en changer une : remplacer le fichier dans soutenance/demo/screenshots/ puis relancer build_deck.py, ou poser l'image par-dessus dans Canva. |
| 32 | Emplacement vidéo : la vidéo de démonstration (JobTest_Demo.mp4) est à insérer sur le cadre en pointillés. |
| 32 | QR code vers http://20.51.167.202/ : déjà généré et intégré (slides 32 et 38). |
| 38 | Logos en pied de page : déjà intégrés. |
