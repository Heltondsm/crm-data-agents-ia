-- Schéma PostgreSQL (Supabase) du CRM.
-- Les accès passent par la clé secrète côté serveur (GitHub Actions) ou par le connecteur MCP :
-- la sécurité par ligne (RLS) est activée et aucune politique publique n'est ouverte.

create table candidatures (
  id bigserial primary key,
  notion_page_id text unique,          -- miroir Notion (facultatif)
  entreprise text not null,
  poste text,
  statut text,                         -- À préparer, Envoyé, Relancer, Réponse positive, Entretien, Offre, Refus, Abandon
  type text,                           -- Candidature, Démarchage, Spontanée, Réseau
  piste text,
  canal text,
  chances text,
  date_envoi date,
  relance date,                        -- prochaine action datée
  prochaine_action text,
  contacts text,
  linkedin text,
  email text,
  telephone text,
  notes text,                          -- historique court : [R1 jj/mm], [Réponse LinkedIn jj/mm …]
  preuve_url text,
  message_pret text,
  agent text,                          -- quel agent ou script a modifié la fiche, et quand
  ville text, lat double precision, lon double precision,   -- siège (annuaire recherche-entreprises.api.gouv.fr)
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  notion_sync boolean default false
);
create index on candidatures (statut);
create index on candidatures (relance);

create table offres (
  id bigserial primary key,
  cle text unique,                     -- « source|identifiant » : évite les doublons
  titre text, entreprise text, lieu text, source text,
  publiee_le date, score int, points_forts text, vigilance text, url text,
  statut text default 'Nouvelle',      -- Nouvelle, Vue, Ajoutée au pipeline, Écartée (sert à évaluer la note)
  trouvee_le date default current_date,
  extrait text, lat double precision, lon double precision,
  flags jsonb default '{}'::jsonb      -- junior, bac5, exp, pbi, sql, dbt…
);
create index on offres (score desc);

create table journal_agents (          -- un passage = une ligne : marque-page, éléments traités, échecs
  id bigserial primary key, agent text, execution text, date timestamptz default now(),
  statut text, resume text, marque_page text, traites text
);

create table semaines (                -- indicateurs hebdomadaires de prospection
  debut date primary key, invitations int, acceptees int, reponses int, appels int, note text
);

create table li_relations (            -- copie des relations LinkedIn (API Member Data Portability)
  url text primary key, prenom text, nom text, entreprise text, poste text, connected_on date, vu_le timestamptz default now()
);

create table li_events (               -- messages LinkedIn déjà vus (journal de l'API)
  id text primary key, type text, at timestamptz, thread text, de_moi boolean, auteur text, extrait text, fiche_id bigint, traite boolean default false
);
create index on li_events (thread);

create table li_posts (                -- publications prévues : vérification du lien en premier commentaire
  id bigserial primary key, date date not null, debut text not null, lien text, commentaire text, texte text,
  statut text default 'prévu', note text, created_at timestamptz default now()
);

alter table candidatures enable row level security;
alter table offres enable row level security;
alter table journal_agents enable row level security;
alter table semaines enable row level security;
alter table li_relations enable row level security;
alter table li_events enable row level security;
alter table li_posts enable row level security;
