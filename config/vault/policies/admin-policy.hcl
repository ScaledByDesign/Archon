# Admin policy - full access to all secrets and management functions
path "*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

# Additional admin capabilities
path "auth/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

path "sys/*" {
  capabilities = ["create", "read", "update", "delete", "list", "sudo"]
}

path "secret/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

path "database/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}
