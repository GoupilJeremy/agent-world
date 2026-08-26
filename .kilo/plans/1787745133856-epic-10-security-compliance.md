# Plan d'implémentation — Épic 10 : Sécurité et Conformité

*Basé sur BACKLOG.md (v1.4.0). Cible : backend Flask + tests. Frontend non inclus (placeholder).*

## Contexte & état actuel

L'épic 10 regroupe 6 User Stories (US-065 → US-070), toutes actuellement `⏳ To Do` / `⏳ Backlog` dans le BACKLOG, **mais l'en-tête de l'épic est erronément marqué « ✅ Terminé (v0.3.0) »**. C'est une incohérence à corriger (voir section « Mise à jour du BACKLOG »).

Constat de l'existant (`backend/`) :
- `services/auth_service.py` : JWT HS256, `login()` / `issue_access_token()` / `authenticate_authorization_header()`. **Mais ce guard n'est branché que sur `/auth/me` et sur l'auth des destinataires de partage** (`routes/share_auth.py`). Les routes CRUD (agents, templates, files, history, integrations, invitations) ne sont **pas** protégées par token → effectivement publiques.
- `models/user.py` : `is_admin` (bool) uniquement. Pas de rôles/permissions, pas de champs 2FA, pas de modèle d'audit.
- Mots de passe : `werkzeug` `generate_password_hash` (pbkdf2) — acceptable, à conserver.
- `config/settings.py` : `CORS_ORIGINS` par défaut `"*"` ; pas de rate limiting ; `SECRET_KEY` dev fallback faible.
- `services/db_optimization_service.py` : SQL brut avec interpolation f-string de `{table_name}` (lignes ~409/451) → à auditer/paramétrer pour US-070.
- Migrations Alembic présentes (`migrations/versions/`) → les nouveaux modèles nécessitent des scripts de migration.
- Intégrations : `IntegrationCredentials` (tokens OAuth) non persistés en DB pour l'instant → cible d'encryption seulement si persistance ajoutée.

## Décisions validées avec l'utilisateur
1. **BACKLOG** : corriger le statut de l'épic au démarrage (→ « En cours ») et basculer chaque US en `✅ Done` progressivement (voir section dédiée).
2. **Verrouillage API** : ajouter un décorateur `@require_auth` + `@require_permission`, appliqué d'abord aux routes sensibles, derrière un flag `AUTH_ENFORCE_ALL` (défaut `False` en dev/test pour ne pas casser les tests/CLI existants).
3. **Dépendances** : ajouter `pyotp` (TOTP 2FA), `cryptography` (AES-256/Fernet), `flask-limiter` (rate limiting).
4. **Frontend** : backend + API + tests uniquement ; pas d'UI d'enrôlement 2FA / RGPD (frontend placeholder).

## Dépendances
Ajouter dans `requirements.txt` (section « Authentication & Security ») :
```
pyotp==2.9.0
cryptography==42.0.5
flask-limiter==3.5.0
```
`requirements-dev.txt` inchangé.

## Modèles & migrations (Alembic)
Créer un script de migration par US modifiant le schéma (`migrations/versions/`).
- **US-065** : `User` ← `totp_secret` (String chiffré, nullable), `totp_enabled` (bool, défaut False), `totp_verified_at` (DateTime nullable), `backup_codes` (JSON des hashes, nullable).
- **US-066** : nouveaux modèles `Role` (id, name, permissions JSON) et association `user_roles` (user_id, role_id) ; réutiliser le vocabulaire de rôles existant (`admin`/`member`/`viewer` de `models/invitation.py`). Garder `is_admin` pour rétro-compat.
- **US-067** : `EncryptedString` (`SQLAlchemy TypeDecorator`) dans `models/base.py` ; colonnes chiffrées (ex. `totp_secret`). Clé via `ENCRYPTION_KEY` (32 octets base64 url-safe) dans `config/settings.py`.
- **US-068** : nouveau modèle `AuditLog` (id, actor_id nullable, action, resource_type, resource_id, ip, user_agent, meta JSON, created_at). Index sur (actor_id, created_at, action).
- **US-069** : `User` ← `consent_given_at` (DateTime nullable), `data_deleted_at` (nullable, pour anonymisation).

## Services
- `services/encryption_service.py` (US-067) : encapsulation `cryptography.Fernet` (AES-256-CBC + HMAC-SHA256). `encrypt()`/`decrypt()`, helper de génération de clé, rotation de clé (ancienne→nouvelle). Utilisé par `EncryptedString`.
- `services/two_factor_service.py` (US-065) : `enroll(user)` (secret TOTP + `provisioning_uri` + QR data), `verify(user, code)`, `generate_backup_codes(user)` / `verify_backup_code(user, code)` (hash argon2/pbkdf2 + constant-time compare), `disable(user)`.
- `services/permission_service.py` (US-066) : matrice de permissions (ex. `agent:read|write|delete`, `template:read|write`, `user:manage`, `audit:read`, `security:manage`). `has_permission(user, perm)`, `role_permissions(role)`.
- `services/audit_service.py` (US-068) : `record(action, actor, request, resource, meta)` ; décorateur `audit(action)` pour journaliser automatiquement les actions protégées. Réutilisé par US-069 (rétention).
- `services/gdpr_service.py` (US-069) : `export_data(user)` (agrège User + projets + agents + exécutions + audit anonymisé), `erase(user)` (anonymisation en respectant la rétention d'audit : `actor_id` → NULL + pseudo, suppression des données personnelles).

## Décorateurs de sécurité (US-066 / transversal)
Dans `services/auth_service.py` (ou `backend/security/decorators.py`) :
- `@require_auth` : résout le `Bearer` via `authenticate_authorization_header` ; 401 sinon.
- `@require_permission(perm)` : compose `@require_auth` + `permission_service.has_permission`.
Application progressive sur routes sensibles (agents/templates/files write, history, integrations, invitations admin) ; protégé par `app.config["AUTH_ENFORCE_ALL"]` (défaut `False`). Quand `False`, les routes restent publiques (comportement actuel) pour préserver CLI + tests.

## Routes (toutes sous `/api`, JSON)
`routes/security.py` (regroupe 2FA + permissions + audit + rgpd admin) :
- **US-065** : `POST /api/auth/2fa/setup` (étape 1 : secret+URI+QR, non activé), `POST /api/auth/2fa/enable` (vérifie un code TOTP puis active), `POST /api/auth/2fa/disable` (admin/owner ou code), `POST /api/auth/login/2fa` (step-up : après mot de passe, valide le TOTP/code de secours et renvoie le token d'accès). Modifier `routes/auth.py#login` pour émettre un « step-up token » si `totp_enabled`.
- **US-066** : `GET/POST /api/admin/roles`, `GET/POST /api/admin/users/<id>/roles` (admin only).
- **US-068** : `GET /api/admin/audit` (filtres date/action/actor, pagination) + `GET /api/admin/audit/export` (CSV & JSON). Admin only.
- **US-069** : `GET /api/account/export` (données du user courant), `DELETE /api/account` (droit à l'oubli → `gdpr_service.erase`), `GET /api/legal/privacy` (politique de confidentialité depuis config).

## US-070 — Protection contre les attaques (transversal)
- **Rate limiting** (`flask-limiter`) : limites sur `/api/auth/login`, `/api/auth/login/2fa`, `/api/auth/2fa/*`, et une limite globale par IP. Config `RATE_LIMIT_*` dans `settings.py`.
- **CORS** : `CORS_ORIGINS` ne doit plus défaut à `"*"` → allowlist configurable, appliquée dans `app.py`.
- **Security headers** : `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy` (API), `Strict-Transport-Security` (prod) via `after_request` (ou Flask-Talisman si ajouté).
- **CSRF** : l'API est stateless (Bearer) → non vulnérable au CSRF classique ; documenter ce point et ne pas ajouter de cookie de session. Si une session cookie apparaît, ajouter protection CSRF.
- **SQL Injection** : auditer `db_optimization_service.py` — remplacer l'interpolation `{table_name}` par une liste blitelistée de tables + `text()` paramétré ; vérifier qu'aucun `execute(text(f"...{user_input}..."))` n'existe ailleurs.
- **XSS** : l'API ne rend pas de HTML (JSON only) ; pour la prévisualisation Markdown des fichiers (`routes/files.py`), sandbox/escape le rendu côté client et ne pas injecter de HTML non échappé.
- **Tests de pénétration** (suite de tests `tests/security/`) : tentative de contournement d'authz, brute-force/rate-limit, probes d'injection, fuite de secret dans les réponses.

## Ordre d'implémentation recommandé (dépendances)
1. **US-070** (renforcement transversal : rate limit, headers, CORS, review SQL) — faible couplage, tôt.
2. **US-067** (service de chiffrement + `EncryptedString`) — prérequis de US-065.
3. **US-066** (permissions + `@require_auth`/`@require_permission` + `AUTH_ENFORCE_ALL`) — prérequis de verrouillage et de US-065.
4. **US-065** (2FA ; dépend de 067 + 066).
5. **US-068** (audit ; journalise les événements de 065/066/069).
6. **US-069** (RGPD ; dépend de 068 pour la rétention).

## Fichiers à créer / modifier
- Créer : `services/encryption_service.py`, `services/two_factor_service.py`, `services/permission_service.py`, `services/audit_service.py`, `services/gdpr_service.py`, `routes/security.py`, `models/role.py` (+ `user_roles`), `models/audit_log.py`, `tests/security/` (ou `tests/unit|integration/` par US), `tests/unit/test_*_service.py`, `tests/integration/test_*_routes.py`.
- Modifier : `models/user.py`, `models/base.py` (EncryptedString), `config/settings.py` (nouvelles clés), `app.py` (CORS, headers, limiter, enregistrement `security` blueprint + services), `routes/auth.py` (login step-up 2FA), `requirements.txt`, `migrations/versions/` (1 script par US), `services/db_optimization_service.py` (paramétrage SQL).
- Respecter les conventions : 4 espaces, Black 88, `snake_case`, types hintés, route handlers minces (logique dans les services), tests marqués `unit`/`integration`.

## Mise à jour du BACKLOG (`@BACKLOG.md`)
Procédure à exécuter **pendant** l'implémentation (par l'agent d'implémentation, pas en plan mode) :
- **Au démarrage** : corriger l'en-tête Épic 10 — remplacer `✅ **Terminé** (Version v0.3.0 - 25 août 2026)` par `⏳ **En cours**` et fixer la version cible (ex. `v0.5.0`). Supprimer la mention erronée « v0.3.0 ».
- **Par US terminée** (critères d'acceptation validés + tests verts) : dans le tableau Épic 10, passer `Statut` de l'US à `✅ Done` ; faire de même dans le tableau MoSCoW P2 (lignes US-065→070).
- **À la fin** (6/6 Done) : Épic 10 → `✅ **Terminé** (Version v0.5.0)`, ajouter un Milestone « Security » dans la section Roadmap, mettre à jour la « Vue d'Ensemble » (Heures/Statut) et le pied de page (« Dernière mise à jour » + version).
- Garder la trace des criticités d'acceptation (ex. TOTP Google Authenticator, AES-256, codes de secours, matrice de permissions, droit à l'oubli).

## Validation
- `pytest` (cible ≥ 90 % couverture backend) ; `black --check backend tests` ; `isort --check-only` ; `flake8` ; `mypy backend tests --ignore-missing-imports`.
- Tests dédiés par US : service (unit) + routes (integration via `pytest-flask`), y compris la suite `tests/security/` (authz bypass, rate limit, injection, fuite de secrets).
- Vérifier que CLI (`backend/cli`) et tests existants restent verts avec `AUTH_ENFORCE_ALL=False` (défaut).
- Manuel : Activer `AUTH_ENFORCE_ALL=True` en staging et confirmer 401 sur routes sensibles sans token ; flux 2FA complet (enroll→enable→login step-up→backup code) ; export/réimport RGPD.

## Risques
- Verrouillage des routes existantes → risque de casser de nombreux tests/CLI : mitigé par `AUTH_ENFORCE_ALL` défaut `False` ; activer progressivement.
- `login` devient en 2 étapes → clients (CLI/intégrations) doivent gérer le step-up token.
- Gestion de clé de chiffrement en prod (`ENCRYPTION_KEY`) : prévoir KMS/secret manager (hors périmètre, documenter).
- Rétention d'audit vs droit à l'oubli RGPD : consigner l'actor de façon pseudonymisée plutôt que supprimer.

## Questions ouvertes (à confirmer à l'implémentation)
- Stratégie de provisioning de `ENCRYPTION_KEY` (env vs KMS) et politique de rotation.
- Période de rétention d'audit (défaut proposé : 365 j, anonymisation après).
- Périmètre exact de `AUTH_ENFORCE_ALL=True` : toutes les routes `/api` ou allowlist sensibles ?
