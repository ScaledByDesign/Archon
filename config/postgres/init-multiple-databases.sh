#!/bin/bash
set -e
set -u

function create_user_and_database() {
	local database=$1
	local user=$2
	echo "  Creating user '$user' and database '$database'..."
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	    CREATE USER $user WITH PASSWORD '$POSTGRES_PASSWORD';
	    CREATE DATABASE $database;
	    GRANT ALL PRIVILEGES ON DATABASE $database TO $user;
EOSQL
}

if [ -n "$POSTGRES_MULTIPLE_DATABASES" ]; then
	echo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"
	IFS=',' read -ra DATABASES <<< "$POSTGRES_MULTIPLE_DATABASES"
	for db in "${DATABASES[@]}"; do
		# Create database with same name as user for each database
		case $db in
			"authentik")
				create_user_and_database "$db" "authentik"
				;;
			"fastapi")
				create_user_and_database "$db" "fastapi"
				;;
			"healthchecks")
				create_user_and_database "$db" "healthchecks"
				;;
			"langfuse")
				create_user_and_database "$db" "langfuse"
				;;
			*)
				create_user_and_database "$db" "$db"
				;;
		esac
	done
	echo "Multiple databases created"
fi
