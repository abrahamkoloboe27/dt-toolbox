# dt-toolbox

[![CI](https://github.com/abrahamkoloboe27/dt-toolbox/actions/workflows/ci.yml/badge.svg)](https://github.com/abrahamkoloboe27/dt-toolbox/actions)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**dt-toolbox** est une toolbox Python pour le monitoring, logging et alerting de scripts data. Elle permet d'uniformiser la gestion des logs et des notifications d'erreur/succès pour les équipes data.

## ✨ Caractéristiques

- 🚀 **Initialisation en une ligne** - Configuration simple et rapide
- 📊 **Logs structurés JSON** - Format standardisé pour ingestion facile
- 🔔 **Alerting automatique** - Notifications SMTP et Webhooks (Slack/Google Chat)
- 🔐 **Redaction PII** - Masquage automatique des données sensibles
- ☁️ **Upload logs** - Support S3/MinIO pour les logs volumineux
- ⚙️ **Configuration flexible** - Env vars, fichier config ou arguments
- 🧪 **Bien testé** - Couverture de tests > 80%

## 📦 Installation

### Avec pip

```bash
pip install dt-toolbox
```

### Avec uv (recommandé)

[uv](https://docs.astral.sh/uv/) est l'outil moderne pour la gestion de projets Python.

```bash
# Installer uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Créer un projet avec uv
uv init mon-projet
cd mon-projet

# Ajouter dt-toolbox
uv add dt-toolbox
```

### Depuis les sources

```bash
git clone https://github.com/abrahamkoloboe27/dt-toolbox.git
cd dt-toolbox
pip install -e ".[dev]"
```

## 🚀 Utilisation rapide

### Option 1: Initialisation simple

```python
from dt_toolbox import init_monitoring
import logging

# Initialiser le monitoring
logger = init_monitoring(
    app_name="etl_orders",
    owner="abklb27@gmail.com",
    recipients=["data-team@company.com"],
    tags=["daily", "etl"],
    notify_on_success=False,  # Ne notifier qu'en cas d'erreur
)

# Utiliser le logger
logger.info("Démarrage du traitement...")
logger.info("Traitement des commandes...")
logger.info("Traitement terminé avec succès")
```

### Option 2: Décorateur

```python
from dt_toolbox import monitor
import logging

@monitor(
    owner="abklb27@gmail.com",
    recipients=["data-team@company.com"],
    tags=["ad-hoc"],
)
def main():
    logger = logging.getLogger()
    logger.info("Processing data...")
    # Votre code ici

if __name__ == "__main__":
    main()
```

## 📖 Documentation

### Configuration

La configuration suit un ordre de priorité:
**Arguments fonction** > **Variables d'environnement** > **Fichier config**

#### Fichier .env (recommandé pour le développement)

Copier le fichier `.env.example` en `.env` et configurer vos valeurs:

```bash
# Copier le template
cp .env.example .env

# Éditer avec vos valeurs
vim .env
```

Le fichier `.env.example` contient tous les paramètres disponibles avec des exemples:
- Configuration basique (APP_NAME, OWNER, LOG_LEVEL, TAGS)
- Configuration SMTP pour les emails
- Configuration webhooks (Slack/Google Chat)
- Configuration stockage (S3/MinIO)
- Configuration redaction PII
- Exemples multi-environnements

**Note**: Le package charge automatiquement le fichier `.env` s'il existe.

#### Via variables d'environnement

```bash
export DTB_APP_NAME="mon_app"
export DTB_OWNER="data@company.com"
export DTB_SMTP_HOST="smtp.gmail.com"
export DTB_SMTP_PORT="587"
export DTB_SMTP_USER="alerts@company.com"
export DTB_SMTP_PASSWORD="secret"
export DTB_RECIPIENTS="team@company.com,alerts@company.com"
export DTB_NOTIFY_ON_SUCCESS="false"
```

#### Via fichier de configuration

Créer `~/.dt_toolbox/config.yml`:

```yaml
app_name: mon_app
owner: data@company.com
tags:
  - production
  - etl

notification:
  smtp_host: smtp.gmail.com
  smtp_port: 587
  smtp_user: alerts@company.com
  smtp_password: ${SMTP_PASSWORD}  # Utiliser env var pour les secrets
  recipients:
    - team@company.com
  notify_on_success: false
  webhook_url: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
  webhook_type: slack

storage:
  enabled: true
  backend: s3
  bucket_name: company-logs
  prefix: dt-toolbox
  upload_threshold_kb: 200
  aws_region: us-east-1

redaction:
  enabled: true
  patterns:
    - "password\\s*=\\s*\\w+"
    - "api[_-]?key\\s*=\\s*[\\w-]+"
```

### Fonctionnalités avancées

#### Upload des logs sur S3

```python
from dt_toolbox import init_monitoring

logger = init_monitoring(
    app_name="big_etl",
    owner="data@company.com",
    storage_enabled=True,
    storage_backend="s3",
    storage_bucket_name="company-logs",
    storage_upload_threshold_kb=200,  # Upload si > 200KB
)
```

Configuration S3 via variables d'environnement:

```bash
export DTB_STORAGE_ENABLED="true"
export DTB_STORAGE_BACKEND="s3"
export DTB_STORAGE_BUCKET="company-logs"
export DTB_AWS_ACCESS_KEY_ID="your-key"
export DTB_AWS_SECRET_ACCESS_KEY="your-secret"
export DTB_AWS_REGION="us-east-1"
```

#### Webhooks (Slack/Google Chat)

```python
logger = init_monitoring(
    app_name="pipeline",
    owner="data@company.com",
    webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK",
    webhook_type="slack",  # ou "gchat"
)
```

#### Redaction PII

Par défaut, dt-toolbox masque automatiquement:
- Mots de passe
- Clés API/secrets
- Numéros de sécurité sociale (SSN)
- Numéros de carte de crédit

Patterns personnalisés:

```python
from dt_toolbox.types import RedactionConfig

config = RedactionConfig(
    enabled=True,
    patterns=[
        r"email['\"]?\s*[:=]\s*[\w.-]+@[\w.-]+",
        r"phone['\"]?\s*[:=]\s*[\d-]+",
    ],
    replacement="***REDACTED***",
)
```

## 📝 Exemples

Voir le dossier [`examples/`](./examples/) pour des exemples complets:

- [`example_success.py`](./examples/example_success.py) - Exécution réussie
- [`example_failure.py`](./examples/example_failure.py) - Gestion d'erreur
- [`example_decorator.py`](./examples/example_decorator.py) - Utilisation du décorateur

## 🧪 Tests

dt-toolbox inclut une suite de tests complète avec **112 tests** couvrant tous les cas d'usage.

### Installation des dépendances de test

```bash
# Installer les dépendances de dev
pip install -e ".[dev]"
```

### Exécuter les tests

**Option 1: Utiliser le script de test (recommandé)**

```bash
# Tous les tests
python run_tests.py all

# Tests unitaires uniquement
python run_tests.py unit

# Tests d'intégration
python run_tests.py integration

# Tests de scénarios réels
python run_tests.py scenarios

# Tests de cas limites
python run_tests.py edge

# Mode verbose
python run_tests.py integration -v

# Lister les types de tests disponibles
python run_tests.py --list
```

**Option 2: Utiliser pytest directement**

```bash
# Tous les tests
pytest tests/ -v

# Tests spécifiques
pytest tests/test_integration.py -v
pytest tests/test_scenarios.py -v
pytest tests/test_edge_cases.py -v

# Avec couverture
pytest tests/ --cov=dt_toolbox --cov-report=html

# Test spécifique
pytest tests/test_integration.py::TestCompleteWorkflows::test_complete_successful_workflow -v
```

### Types de tests

#### Tests Unitaires (36 tests)
- Configuration (environnement, fichiers, priorités)
- Handlers de logging (JSON, rotation)
- Monitoring (initialisation, décorateur)
- Notifications (SMTP, webhooks)
- Redaction PII
- Stockage (S3, MinIO, local)

#### Tests d'Intégration (21 tests)
- Workflows complets de bout en bout
- Capture d'exceptions
- Notifications en conditions réelles
- Upload de logs
- Scénarios réels (ETL, ML, qualité données)

#### Tests de Scénarios (25 tests)
- Scripts de succès (ETL, batch, validation)
- Scripts d'échec (connexion, erreurs données)
- Redaction PII (credentials, API keys, paiement)
- Notifications multiples
- Tags et catégorisation
- Jobs longs
- Multi-environnements (dev/staging/prod)

#### Tests de Cas Limites (28 tests)
- Configuration manquante/invalide
- Échecs réseau (SMTP, webhook, S3)
- Erreurs de permissions
- Données volumineuses
- Caractères spéciaux (unicode, JSON)
- Concurrence
- Nettoyage des ressources

### Résultats des tests

```bash
$ python run_tests.py all
===================================
Running all tests...
112 tests collected
112 passed in 3.45s
===================================
```

### Linting et formatage

```bash
# Vérifier le formatage
ruff check src/ tests/
black --check src/ tests/
isort --check-only src/ tests/

# Corriger automatiquement
black src/ tests/
isort src/ tests/
ruff check --fix src/ tests/
```

## 🐳 Docker

```bash
# Build l'image
docker build -f docker/Dockerfile -t dt-toolbox .

# Lancer un exemple
docker run dt-toolbox python examples/example_success.py
```

## 🔧 Développement

### Setup avec uv

```bash
# Cloner le repo
git clone https://github.com/abrahamkoloboe27/dt-toolbox.git
cd dt-toolbox

# Créer l'environnement virtuel avec uv
uv venv

# Activer l'environnement
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Installer en mode développement
uv pip install -e ".[dev]"

# Installer les pre-commit hooks
pre-commit install
```

### Workflow de développement

```bash
# Lancer les tests
uv run pytest

# Formater le code
uv run black src/ tests/
uv run isort src/ tests/

# Linting
uv run ruff check src/ tests/

# Build le package
uv build
```

## 📦 Publication

```bash
# Build
python -m build

# Publier sur PyPI (test)
twine upload --repository testpypi dist/*

# Publier sur PyPI (prod)
twine upload dist/*
```

## 🤝 Contribution

Les contributions sont les bienvenues! Voir [CONTRIBUTING.md](./CONTRIBUTING.md) pour les guidelines.

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 License

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- [uv](https://docs.astral.sh/uv/) pour la gestion moderne de projets Python
- [Pydantic](https://docs.pydantic.dev/) pour la validation de configuration
- [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) pour l'intégration AWS

## 📞 Support

Pour toute question ou problème:
- Ouvrir une [issue](https://github.com/abrahamkoloboe27/dt-toolbox/issues)
- Contacter: abklb27@gmail.com

## 🗺️ Roadmap

- [ ] Support Google Cloud Storage (GCS)
- [ ] Métriques et dashboards
- [ ] Support pour plus de webhooks (Teams, Discord)
- [ ] Templates de messages personnalisables
- [ ] Intégration avec systèmes de monitoring (Datadog, New Relic)
- [ ] CLI pour configuration et tests
