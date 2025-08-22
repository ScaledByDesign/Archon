#!/bin/bash
set -e

echo "🚀 PostgreSQL Multiple Database Initialization"
echo "POSTGRES_USER: ${POSTGRES_USER}"
echo "POSTGRES_DB: ${POSTGRES_DB}"
echo "POSTGRES_MULTIPLE_DATABASES: ${POSTGRES_MULTIPLE_DATABASES:-}"

if [ -n "${POSTGRES_MULTIPLE_DATABASES:-}" ]; then
	echo "Creating multiple databases: $POSTGRES_MULTIPLE_DATABASES"

	# Split the database list by comma
	IFS=',' read -ra DATABASES <<< "$POSTGRES_MULTIPLE_DATABASES"

	for db in "${DATABASES[@]}"; do
		# Trim whitespace
		db=$(echo "$db" | tr -d '[:space:]')

		if [ -n "$db" ]; then
			echo "Creating database: $db"
			psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
				CREATE DATABASE "$db";
			EOSQL
			echo "✅ Database '$db' created successfully"
		fi
	done

	echo "✅ All databases created!"
else
	echo "No multiple databases specified"
fi
