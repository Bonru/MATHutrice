"""
seed.py — Remplit une base vide : les notions et les compétences du REFERENTIEL.

Appelé au démarrage de l'application (lifespan de app.py), après la création
des tables. N'insère que les lignes manquantes : un second démarrage n'écrit rien.

Lancement manuel possible :
  python -m mathutrice.fonctions_python.seed
"""

import uuid

from sqlmodel import Session, SQLModel, select

from mathutrice import models
from mathutrice.referentiel import REFERENTIEL

# Le REFERENTIEL ne porte pas de description, que la table notion exige.
DESCRIPTIONS = {
    "trigonometrie": "Étude des fonctions trigonométriques, des angles et du cercle trigonométrique.",
    "fractions_puissances_radicaux": "Manipulation des fractions, puissances et radicaux.",
    "logarithme_exponentielle": "Étude des fonctions logarithme et exponentielle.",
    "manipulation_expressions_litterales": "Isolement et manipulation de variables dans des expressions algébriques.",
    "equations_inequations": "Résolution d'équations et d'inéquations du premier et second degré.",
    "polynomes_factorisation": "Étude des polynômes, factorisation et identités remarquables.",
    "analyse_dimensionnelle": "Dimensions, unités et homogénéité des formules physiques.",
}


def seed_missing(engine) -> None:
    """Insère les notions et compétences du REFERENTIEL absentes de la base."""
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        for notion_key, notion_data in REFERENTIEL.items():
            notion = session.exec(
                select(models.Notion).where(models.Notion.referentiel_key == notion_key)
            ).first()
            if notion is None:
                notion = models.Notion(
                    notion_id=uuid.uuid4(),
                    referentiel_key=notion_key,
                    title=notion_data["notion_nom"],
                    description=DESCRIPTIONS[notion_key],
                )
                session.add(notion)
                session.flush()

            for comp in notion_data["competences"]:
                exists = session.exec(
                    select(models.Competence).where(
                        models.Competence.referentiel_code == comp["code"]
                    )
                ).first()
                if exists is None:
                    session.add(
                        models.Competence(
                            competence_id=uuid.uuid4(),
                            referentiel_code=comp["code"],
                            title=comp["nom"],
                            level=comp["niveau"],
                            notion_id=notion.notion_id,
                        )
                    )
        session.commit()


if __name__ == "__main__":
    from mathutrice.database import engine

    seed_missing(engine)
    print("Notions et compétences insérées.")
