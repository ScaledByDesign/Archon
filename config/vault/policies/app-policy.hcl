# Policy for applications to read secrets
path "secret/data/app/*" {
  capabilities = ["read"]
}

path "secret/metadata/app/*" {
  capabilities = ["list", "read"]
}

# Allow applications to read their specific environment variables
path "secret/data/env/{{identity.entity.aliases.auth_approle_*.name}}/*" {
  capabilities = ["read"]
}

path "secret/metadata/env/{{identity.entity.aliases.auth_approle_*.name}}/*" {
  capabilities = ["list", "read"]
}

# Allow reading database credentials
path "database/creds/app-db-role" {
  capabilities = ["read"]
}

# Allow token self-renewal
path "auth/token/renew-self" {
  capabilities = ["update"]
}

path "auth/token/lookup-self" {
  capabilities = ["read"]
}
