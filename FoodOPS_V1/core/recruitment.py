import random
from FoodOPS_V1.data.roles import ROLES
from FoodOPS_V1.core.rh import cout_licenciement

PRENOMS = [
    "Alex",
    "Marie",
    "Lucas",
    "Sophie",
    "Karim",
    "Claire",
    "Hugo",
    "Lea",
    "Antoine",
    "Nadia",
]
NOMS = [
    "Durand",
    "Moreau",
    "Lefevre",
    "Garcia",
    "Bernard",
    "Petit",
    "Roux",
    "Fontaine",
]


def generer_candidats(type_resto, nb=5):
    """
    Génère une liste de candidats disponibles sur le marché du travail.
    """
    candidats = []
    roles_dispo = ROLES[type_resto]
    for _ in range(nb):
        role = random.choice(roles_dispo)
        salaire_attendu = int(role["salaire_marche"] * random.uniform(0.95, 1.15))
        candidat = {
            "nom": f"{random.choice(PRENOMS)} {random.choice(NOMS)}",
            "poste": role["nom"],
            "experience": random.randint(1, 15),  # en années
            "competence": round(random.uniform(0.4, 1.0), 2),  # 0 à 1
            "salaire_attendu": salaire_attendu,
            "contrat": random.choice(["CDI", "CDD", "Extra"]),
        }
        candidats.append(candidat)
    return candidats


def embaucher(candidat, salaire_propose, equipe):
    """
    Tente d'embaucher un candidat à un salaire donné.
    """
    if salaire_propose < candidat["salaire_attendu"]:
        # Risque de refus si salaire trop bas
        if random.random() < 0.5:
            return False, equipe
    employe = {
        "nom": candidat["poste"],
        "salaire": salaire_propose,
        "contrat": candidat["contrat"],
        "experience": candidat["experience"],
        "competence": candidat["competence"],
    }
    equipe.append(employe)
    return True, equipe


def licencier(index_employe, equipe):
    """
    Supprime un employé de l'équipe et retourne le coût.
    """
    if 0 <= index_employe < len(equipe):
        employe = equipe.pop(index_employe)
        return cout_licenciement(employe), equipe
    return 0, equipe
