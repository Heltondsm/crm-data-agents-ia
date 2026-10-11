# Consignes des agents (modèle)

Cette page est relue par chaque agent au début de chaque passage. Si elle est illisible, l'agent s'arrête et le note dans le journal.

## 1. L'offre et la cible
[Ce que l'équipe vend, à qui (secteurs, taille d'entreprise, zone géographique), les références clients et leurs chiffres vérifiés. Seuls ces chiffres peuvent être cités.]

## 2. Les opportunités à garder ou à écarter
[Types de projets acceptés, budget minimum, critères d'exclusion.]

## 3. Règles d'écriture
[Ton, longueur des messages, ce qu'il ne faut jamais écrire, ne rien inventer.]

## 4. Note d'une opportunité sur 100
Base 55. Plus : besoin aligné avec l'offre, outils maîtrisés cités (Power BI, SQL…), publiée récemment, secteur déjà connu. Moins : budget trop faible, délai irréaliste, technologie hors périmètre, zone non couverte. Bornée entre 0 et 100.

## 5. Garde-fous
- Ne jamais écrire à un prospect directement : les réponses sont des brouillons, relus avant envoi.
- Ne rien supprimer, ne rien payer.
- En cas de doute, ne rien modifier et le signaler.
- Une source illisible est signalée « en échec », jamais présentée comme « rien de neuf ».
- Chaque passage écrit une ligne dans `journal_agents`.

## 6. Base de données
Toutes les lectures et écritures passent par l'outil SQL du connecteur Supabase (tables décrites dans `sql/schema.sql`).
