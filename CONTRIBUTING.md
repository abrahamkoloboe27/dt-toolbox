# Contributing to dt-toolbox

Merci de votre intérêt pour contribuer à dt-toolbox! Ce document fournit les guidelines pour contribuer au projet.

## Code of Conduct

En participant à ce projet, vous acceptez de respecter les autres contributeurs et de maintenir un environnement accueillant et inclusif.

## Comment contribuer

### Signaler un bug

1. Vérifiez d'abord que le bug n'a pas déjà été signalé dans les [issues](https://github.com/abrahamkoloboe27/dt-toolbox/issues)
2. Si non, créez une nouvelle issue en utilisant le template de bug report
3. Incluez:
   - Description claire du problème
   - Steps pour reproduire
   - Comportement attendu vs comportement observé
   - Version de Python et de dt-toolbox
   - Traceback complet si applicable

### Proposer une fonctionnalité

1. Créez une issue avec le label "enhancement"
2. Décrivez:
   - Le cas d'usage
   - La solution proposée
   - Les alternatives considérées

### Soumettre une Pull Request

1. Fork le repository
2. Créez une branche depuis `develop`:
   ```bash
   git checkout -b feature/ma-fonctionnalite
   ```

3. Faites vos modifications en suivant les standards de code

4. Ajoutez des tests pour vos modifications:
   ```bash
   pytest tests/
   ```

5. Vérifiez le formatage et le linting:
   ```bash
   black src/ tests/
   isort src/ tests/
   ruff check src/ tests/
   ```

6. Commitez vos changements:
   ```bash
   git commit -m "feat: description de la fonctionnalité"
   ```
   
   Utilisez les préfixes de commit conventionnels:
   - `feat:` nouvelle fonctionnalité
   - `fix:` correction de bug
   - `docs:` documentation
   - `test:` ajout de tests
   - `refactor:` refactoring
   - `chore:` tâches de maintenance

7. Push vers votre fork:
   ```bash
   git push origin feature/ma-fonctionnalite
   ```

8. Ouvrez une Pull Request vers `develop`

## Standards de code

### Style de code

- Suivre PEP 8
- Utiliser Black pour le formatage (line length: 100)
- Utiliser isort pour l'organisation des imports
- Type hints obligatoires pour les fonctions publiques
- Docstrings Google style pour toutes les fonctions publiques

### Tests

- Tests unitaires avec pytest
- Couverture minimale: 80%
- Mocker les services externes (SMTP, webhooks, S3)
- Nommer les tests: `test_<fonction>_<scenario>`

Exemple:
```python
def test_init_monitoring_with_tags(temp_log_dir):
    """Test monitoring initialization with tags."""
    logger = init_monitoring(
        app_name="test_app",
        owner="test@example.com",
        tags=["test", "unit"],
        log_dir=temp_log_dir,
    )
    assert logger is not None
```

### Documentation

- Docstrings pour toutes les fonctions publiques
- Exemples dans les docstrings quand pertinent
- Mettre à jour le README si nécessaire
- Ajouter une entrée dans CHANGELOG.md

## Environnement de développement

### Setup

```bash
# Cloner le repo
git clone https://github.com/abrahamkoloboe27/dt-toolbox.git
cd dt-toolbox

# Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Installer en mode développement
pip install -e ".[dev]"

# Installer pre-commit hooks
pre-commit install
```

### Commandes utiles

```bash
# Lancer les tests
pytest tests/ -v

# Tests avec couverture
pytest tests/ --cov=dt_toolbox --cov-report=html

# Linting
ruff check src/ tests/

# Formatage
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Build le package
python -m build
```

## Process de review

1. Au moins une review approuvée requise
2. Tous les tests CI doivent passer
3. Couverture de code maintenue au-dessus de 80%
4. Pas de conflits avec la branche cible

## Questions?

N'hésitez pas à:
- Ouvrir une issue de type "question"
- Contacter les mainteneurs: abklb27@gmail.com

Merci de contribuer à dt-toolbox! 🎉
