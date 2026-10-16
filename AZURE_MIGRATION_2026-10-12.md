# Migration Azure — 12 octobre 2026

Rapport détaillé des opérations : [RAPPORT_MIGRATION_AZURE_2026-10-12.md](RAPPORT_MIGRATION_AZURE_2026-10-12.md).

## Déploiement actif

- Compte Azure : nouvel abonnement de Iheb
- Abonnement : `1c03a372-35c0-4c27-a3a6-bbdbe2e237f5` (`Azure subscription 1`)
- Groupe de ressources / VM : `rg-jobtest-pfe` / `vm-jobtest-pfe`
- Région / taille : East US / Standard D2as v7 (2 vCPU, 8 Gio)
- IP publique statique : `20.75.163.163`
- URL : <https://jobtest-pfe-iheb.eastus.cloudapp.azure.com/>
- Services Docker Compose : `db`, `ollama`, `api`, `web`, `caddy`
- HTTPS : certificat Let's Encrypt géré et renouvelé automatiquement par Caddy ; HTTP redirige vers HTTPS.
- Clé SSH privée locale : `C:\Users\ihebe\.ssh\jobtest_azure_iheb_2026` (à garder privée)

Connexion et état :

```powershell
ssh -i 'C:\Users\ihebe\.ssh\jobtest_azure_iheb_2026' iheb@20.75.163.163
cd /opt/jobtest
sudo docker compose ps
```

## Données transférées

Source : PostgreSQL 16 sur l'ancienne VM du compte `ihebelleuch6@gmail.com`, abonnement `9552bd87-ee32-4302-8788-b9e558dc0688`. La base a été sauvegardée au format `pg_dump -Fc`, puis restaurée dans PostgreSQL 16 sur la nouvelle VM.

Sauvegarde locale : `D:\education\pfe\jobtest-postgres-old-20261012.dump` (contient des données de recrutement ; ne pas publier dans Git).

SHA-256 : `8a5a08f1a88c202a615ad15d1befcd468a8d7376e80f258e75d41a24f5eacfd6`

| Table | Avant | Après |
| --- | ---: | ---: |
| `users` | 2 | 2 |
| `candidates` | 32 | 32 |
| `job_offers` | 3 | 3 |
| `cvs` | 32 | 32 |
| `match_results` | 32 | 32 |

L'ancienne VM `vm-jobtest-pfe` a été arrêtée et désallouée après la sauvegarde. Son disque et son IP publique existent encore dans l'ancien compte pour permettre un retour arrière ; ils peuvent continuer à être facturés. L'ancien nom DNS `jobtest.eastus.cloudapp.azure.com` a été retiré de son IP, mais Azure le signalait encore « déjà utilisé » lors de la configuration de la nouvelle IP. Le déploiement actif utilise donc l'URL ci-dessus.

## Vérifications réalisées

- `docker compose ps` : cinq services en fonctionnement, API, base et frontend sains.
- Page d'accueil HTTPS : HTTP `200` avec validation du certificat par `curl`.
- HTTP sur le domaine et l'IP : redirection `308` vers HTTPS.
- `/api/v1/health` sur HTTPS : `status: ok`, version `2.0.0`.
- Deux modèles `SentenceTransformer` chargés : anglais et multilingue.
- Ollama : modèle `qwen2.5:1.5b` présent.
- Page de connexion vérifiée visuellement dans le navigateur intégré Codex.

## Maintenance

```bash
cd /opt/jobtest
sudo docker compose ps
sudo docker compose logs --tail=100 api
sudo docker compose logs --tail=100 caddy
sudo docker compose up -d --build
```

La configuration de l'API est dans `/opt/jobtest/.env` (mode `0600`) ; elle contient les secrets de base et de JWT générés lors du déploiement. Les volumes Docker contiennent les données PostgreSQL, le modèle Ollama, le cache des embeddings et les certificats TLS. Ne pas exécuter `docker compose down -v`.
