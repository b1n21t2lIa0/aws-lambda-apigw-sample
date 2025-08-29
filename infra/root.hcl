remote_state {
  backend = "s3"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite"
  }
  config = {
    bucket         = "vsop-audit-common-terraform-state"
    key            = "${path_relative_to_include()}/terraform.tfstate"
    region         = "ap-southeast-1"
    dynamodb_table = "lock-table"
  }
}

inputs = {
  region = "ap-southeast-1"
}