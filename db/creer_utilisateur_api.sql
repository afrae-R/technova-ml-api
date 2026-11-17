-- Crée l'utilisateur PostgreSQL « technova_api » utilisé par l'API (moindre privilège).
--
-- À exécuter UNE seule fois, en administrateur (postgres), connecté à la base « technova » :
--     psql -U postgres -d technova -f db/creer_utilisateur_api.sql
--
-- Le mot de passe n'est PAS écrit dans ce fichier (il serait publié sur GitHub).
-- On le définit ensuite à part, dans psql, avec la commande :  \password technova_api
--
-- Ce que « technova_api » peut faire : lire et ajouter des lignes dans « requetes » et « predictions ».
-- Ce qu'il ne peut PAS faire : modifier ou supprimer des lignes, créer ou supprimer des tables,
-- lire les salariés (table « salaries »), ni toucher aux autres bases.

-- 1. Créer l'utilisateur (sans mot de passe pour l'instant), seulement s'il n'existe pas déjà
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'technova_api') THEN
        CREATE ROLE technova_api LOGIN;
    END IF;
END
$$;

-- 2. Droit de se connecter à la base technova et de voir ses tables
GRANT CONNECT ON DATABASE technova TO technova_api;
GRANT USAGE ON SCHEMA public TO technova_api;

-- 3. Droits sur les deux tables du journal : lire (SELECT) et ajouter (INSERT) uniquement.
--    SELECT est nécessaire : l'API relit le numéro de la demande qu'elle vient d'ajouter.
GRANT SELECT, INSERT ON requetes, predictions TO technova_api;

-- 4. Droit d'utiliser les compteurs qui donnent leur numéro automatique aux nouvelles lignes
GRANT USAGE ON SEQUENCE requetes_id_seq, predictions_id_seq TO technova_api;
