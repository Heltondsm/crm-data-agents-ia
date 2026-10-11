# Consignes des agents (modèle)

Cette page est relue par chaque agent au début de chaque passage. Si elle est illisible, l'agent s'arrête et le note dans le journal.

## 1. Le profil
[Poste visé, zone géographique, compétences, projets avec leurs chiffres vérifiés. Seuls ces chiffres peuvent être cités.]

## 2. Les offres à garder ou à écarter
[Familles de postes acceptées, types de contrat, critères d'exclusion.]

## 3. Règles d'écriture
[Ton, longueur des messages, ce qu'il ne faut jamais écrire, ne rien inventer.]

## 4. Note d'une offre sur 100
Base 55. Plus : ouverte aux débutants, outils maîtrisés cités, publiée récemment, secteur proche de l'expérience. Moins : niveau d'expérience trop élevé, diplôme exigé non détenu, langue exigée, stage ou alternance. Bornée entre 0 et 100.

## 5. Garde-fous
- Ne jamais écrire à quelqu'un d'autre que le propriétaire : les réponses sont des brouillons.
- Ne rien supprimer, ne rien payer.
- En cas de doute, ne rien modifier et le signaler.
- Une source illisible est signalée « en échec », jamais présentée comme « rien de neuf ».
- Chaque passage écrit une ligne dans `journal_agents`.

## 6. Base de données
Toutes les lectures et écritures passent par l'outil SQL du connecteur Supabase (tables décrites dans `sql/schema.sql`).
